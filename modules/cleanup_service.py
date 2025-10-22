# cleanup_service.py
"""
PostgreSQL Session Database Cleanup Service

Automatically cleans up inactive session databases to prevent resource exhaustion
and duplicate key errors. Runs as a background thread checking for inactive sessions
based on configurable timeout periods.

Features:
- Configurable inactivity timeout (default: 30 minutes)
- Configurable cleanup interval (default: 10 minutes)
- Safe concurrent access with file locking
- Comprehensive logging for audit trail
- Graceful shutdown support
"""

import os
import json
import time
import logging
import threading
import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PostgreSQLCleanupService:
    """Background service to clean up inactive PostgreSQL session databases"""

    def __init__(self,
                 sessions_dir: str = '/var/lib/duckdb/sessions',
                 inactive_minutes: int = 30,
                 cleanup_interval_minutes: int = 10,
                 enabled: bool = True):
        """
        Initialize the cleanup service

        Args:
            sessions_dir: Directory containing session marker files
            inactive_minutes: Minutes of inactivity before cleanup (default: 30)
            cleanup_interval_minutes: Minutes between cleanup runs (default: 10)
            enabled: Whether cleanup is enabled (default: True)
        """
        self.sessions_dir = sessions_dir
        self.inactive_minutes = inactive_minutes
        self.cleanup_interval_seconds = cleanup_interval_minutes * 60
        self.enabled = enabled

        # PostgreSQL connection parameters
        self.pg_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', 5432),
            'user': os.getenv('POSTGRES_USER', 'app_user'),
            'password': os.getenv('POSTGRES_PASSWORD', '1234')
        }

        # Background thread
        self._thread = None
        self._stop_event = threading.Event()
        self._running = False

        # Statistics
        self.stats = {
            'total_runs': 0,
            'databases_cleaned': 0,
            'markers_cleaned': 0,
            'last_run': None,
            'last_cleanup_count': 0,
            'errors': 0
        }

        logger.info(f"[Cleanup Service] Initialized with inactivity timeout: {inactive_minutes} min, "
                   f"interval: {cleanup_interval_minutes} min, enabled: {enabled}")

    def start(self):
        """Start the background cleanup service"""
        if not self.enabled:
            logger.info("[Cleanup Service] Service is disabled, not starting")
            return

        if self._running:
            logger.warning("[Cleanup Service] Service is already running")
            return

        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._thread.start()
        logger.info("[Cleanup Service] Started background cleanup thread")

    def stop(self):
        """Stop the background cleanup service"""
        if not self._running:
            return

        logger.info("[Cleanup Service] Stopping cleanup service...")
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)

        self._running = False
        logger.info("[Cleanup Service] Cleanup service stopped")

    def _cleanup_loop(self):
        """Main cleanup loop running in background thread"""
        logger.info("[Cleanup Service] Cleanup loop started")

        while not self._stop_event.is_set():
            try:
                # Run cleanup
                self._run_cleanup()

                # Wait for next interval or stop signal
                self._stop_event.wait(timeout=self.cleanup_interval_seconds)

            except Exception as e:
                logger.error(f"[Cleanup Service] Error in cleanup loop: {e}")
                self.stats['errors'] += 1
                # Continue running despite errors
                time.sleep(60)  # Wait 1 minute before retrying

        logger.info("[Cleanup Service] Cleanup loop exited")

    def _run_cleanup(self):
        """Execute a single cleanup pass"""
        try:
            logger.info("[Cleanup Service] Starting cleanup pass...")
            self.stats['total_runs'] += 1
            self.stats['last_run'] = datetime.now().isoformat()

            cleanup_count = 0
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(minutes=self.inactive_minutes)

            # Get all session marker files
            if not os.path.exists(self.sessions_dir):
                logger.warning(f"[Cleanup Service] Sessions directory does not exist: {self.sessions_dir}")
                return

            marker_files = [f for f in os.listdir(self.sessions_dir) if f.endswith('.db')]

            logger.info(f"[Cleanup Service] Found {len(marker_files)} session markers to check")

            for marker_file in marker_files:
                try:
                    marker_path = os.path.join(self.sessions_dir, marker_file)

                    # Read marker file
                    with open(marker_path, 'r') as f:
                        content = f.read()

                    # Try to parse as JSON
                    try:
                        marker_data = json.loads(content)
                    except json.JSONDecodeError:
                        # Old format marker file (plain text) - treat as very old and clean up
                        logger.info(f"[Cleanup Service] Found old-format marker file: {marker_file}, cleaning up...")

                        # Extract session_id and db_name from filename
                        session_id = marker_file[:-3]  # Remove .db extension
                        db_name = f"session_{session_id.lower().replace('-', '_')}"

                        # Drop the database
                        if self._drop_database(db_name):
                            os.remove(marker_path)
                            cleanup_count += 1
                            self.stats['databases_cleaned'] += 1
                            self.stats['markers_cleaned'] += 1
                            logger.info(f"[Cleanup Service] Cleaned up old-format session: {session_id}")
                        continue

                    # Parse last accessed time
                    last_accessed_str = marker_data.get('last_accessed')
                    if not last_accessed_str:
                        logger.warning(f"[Cleanup Service] No last_accessed in marker: {marker_file}, treating as old...")
                        # Treat as old and clean up
                        db_name = marker_data.get('database_name')
                        session_id = marker_data.get('session_id')

                        if db_name:
                            if self._drop_database(db_name):
                                os.remove(marker_path)
                                cleanup_count += 1
                                self.stats['databases_cleaned'] += 1
                                self.stats['markers_cleaned'] += 1
                                logger.info(f"[Cleanup Service] Cleaned up marker without timestamp: {session_id}")
                        continue

                    last_accessed = datetime.fromisoformat(last_accessed_str)

                    # Check if inactive
                    if last_accessed < cutoff_time:
                        db_name = marker_data.get('database_name')
                        session_id = marker_data.get('session_id')

                        inactive_minutes = (current_time - last_accessed).total_seconds() / 60
                        logger.info(f"[Cleanup Service] Found inactive session: {session_id} "
                                  f"(inactive for {inactive_minutes:.1f} minutes)")

                        # Drop the database
                        if self._drop_database(db_name):
                            # Remove marker file
                            os.remove(marker_path)
                            cleanup_count += 1
                            self.stats['databases_cleaned'] += 1
                            self.stats['markers_cleaned'] += 1
                            logger.info(f"[Cleanup Service] Cleaned up session: {session_id}, database: {db_name}")
                        else:
                            logger.warning(f"[Cleanup Service] Failed to drop database: {db_name}")

                except json.JSONDecodeError:
                    logger.warning(f"[Cleanup Service] Invalid JSON in marker file: {marker_file}")
                except Exception as e:
                    logger.error(f"[Cleanup Service] Error processing marker {marker_file}: {e}")

            self.stats['last_cleanup_count'] = cleanup_count
            logger.info(f"[Cleanup Service] Cleanup pass completed. Cleaned up {cleanup_count} sessions")

        except Exception as e:
            logger.error(f"[Cleanup Service] Error in cleanup pass: {e}")
            self.stats['errors'] += 1

    def _drop_database(self, db_name: str) -> bool:
        """
        Safely drop a PostgreSQL database

        Args:
            db_name: Name of the database to drop

        Returns:
            True if successful, False otherwise
        """
        try:
            # Connect to PostgreSQL server
            conn = psycopg2.connect(
                host=self.pg_config['host'],
                port=self.pg_config['port'],
                database='postgres',
                user=self.pg_config['user'],
                password=self.pg_config['password']
            )
            conn.autocommit = True
            cursor = conn.cursor()

            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (db_name,)
            )
            exists = cursor.fetchone()

            if exists:
                # Terminate existing connections
                cursor.execute("""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = %s
                    AND pid <> pg_backend_pid()
                """, (db_name,))

                # Drop the database
                cursor.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {}").format(
                        sql.Identifier(db_name)
                    )
                )
                logger.info(f"[Cleanup Service] Dropped database: {db_name}")
            else:
                logger.info(f"[Cleanup Service] Database does not exist: {db_name}")

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"[Cleanup Service] Failed to drop database {db_name}: {e}")
            return False

    def force_cleanup_session(self, session_id: str) -> bool:
        """
        Force cleanup of a specific session (manual cleanup)

        Args:
            session_id: Session ID to clean up

        Returns:
            True if successful, False otherwise
        """
        try:
            marker_file = f"{session_id}.db"
            marker_path = os.path.join(self.sessions_dir, marker_file)

            if not os.path.exists(marker_path):
                logger.warning(f"[Cleanup Service] Session marker not found: {session_id}")
                return False

            # Read marker file
            with open(marker_path, 'r') as f:
                content = f.read()

            # Try to parse as JSON
            try:
                marker_data = json.loads(content)
                db_name = marker_data.get('database_name')
            except json.JSONDecodeError:
                # Old format - derive db_name from session_id
                logger.info(f"[Cleanup Service] Old-format marker for force cleanup: {session_id}")
                db_name = f"session_{session_id.lower().replace('-', '_')}"

            # Drop database
            if self._drop_database(db_name):
                # Remove marker file
                os.remove(marker_path)
                logger.info(f"[Cleanup Service] Force cleaned up session: {session_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"[Cleanup Service] Failed to force cleanup session {session_id}: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get cleanup service statistics"""
        return {
            **self.stats,
            'enabled': self.enabled,
            'running': self._running,
            'inactive_minutes': self.inactive_minutes,
            'cleanup_interval_minutes': self.cleanup_interval_seconds / 60
        }

    def get_active_sessions(self) -> List[Dict]:
        """
        Get list of currently active sessions

        Returns:
            List of session information dictionaries
        """
        try:
            active_sessions = []

            if not os.path.exists(self.sessions_dir):
                return active_sessions

            marker_files = [f for f in os.listdir(self.sessions_dir) if f.endswith('.db')]
            current_time = datetime.now()

            for marker_file in marker_files:
                try:
                    marker_path = os.path.join(self.sessions_dir, marker_file)

                    with open(marker_path, 'r') as f:
                        content = f.read()

                    # Try to parse as JSON
                    try:
                        marker_data = json.loads(content)
                    except json.JSONDecodeError:
                        # Old format - skip in listing
                        logger.debug(f"[Cleanup Service] Skipping old-format marker in listing: {marker_file}")
                        continue

                    last_accessed_str = marker_data.get('last_accessed')
                    if last_accessed_str:
                        last_accessed = datetime.fromisoformat(last_accessed_str)
                        inactive_minutes = (current_time - last_accessed).total_seconds() / 60

                        active_sessions.append({
                            'session_id': marker_data.get('session_id'),
                            'database_name': marker_data.get('database_name'),
                            'created_at': marker_data.get('created_at'),
                            'last_accessed': last_accessed_str,
                            'inactive_minutes': round(inactive_minutes, 2),
                            'will_cleanup_in_minutes': max(0, self.inactive_minutes - inactive_minutes)
                        })

                except Exception as e:
                    logger.error(f"[Cleanup Service] Error reading session {marker_file}: {e}")

            # Sort by last accessed (most recent first)
            active_sessions.sort(key=lambda x: x['last_accessed'], reverse=True)

            return active_sessions

        except Exception as e:
            logger.error(f"[Cleanup Service] Failed to get active sessions: {e}")
            return []


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_cleanup_service(enabled: bool = None) -> PostgreSQLCleanupService:
    """
    Factory function to create cleanup service with configuration from environment

    Args:
        enabled: Override for enabled status (default: from environment)

    Returns:
        PostgreSQLCleanupService instance
    """
    # Get configuration from environment
    if enabled is None:
        enabled = os.getenv('POSTGRES_CLEANUP_ENABLED', 'true').lower() == 'true'

    inactive_minutes = int(os.getenv('POSTGRES_CLEANUP_INACTIVE_MINUTES', '30'))
    cleanup_interval_minutes = int(os.getenv('POSTGRES_CLEANUP_INTERVAL_MINUTES', '10'))
    sessions_dir = os.getenv('DATABASE_DIR', '/var/lib/duckdb/sessions')

    service = PostgreSQLCleanupService(
        sessions_dir=sessions_dir,
        inactive_minutes=inactive_minutes,
        cleanup_interval_minutes=cleanup_interval_minutes,
        enabled=enabled
    )

    return service


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example usage
    print("=" * 80)
    print("PostgreSQL Session Cleanup Service")
    print("=" * 80)

    # Create service
    service = create_cleanup_service()

    print(f"\nService Configuration:")
    print(f"  Enabled: {service.enabled}")
    print(f"  Inactivity Timeout: {service.inactive_minutes} minutes")
    print(f"  Cleanup Interval: {service.cleanup_interval_seconds / 60} minutes")
    print(f"  Sessions Directory: {service.sessions_dir}")

    # Start service
    service.start()

    print(f"\nService started. Press Ctrl+C to stop...")

    try:
        # Keep running
        while True:
            time.sleep(10)

            # Print stats every 10 seconds
            stats = service.get_stats()
            print(f"\nStats: Runs={stats['total_runs']}, "
                  f"Cleaned={stats['databases_cleaned']}, "
                  f"Last={stats['last_cleanup_count']}, "
                  f"Errors={stats['errors']}")

            # Show active sessions
            active = service.get_active_sessions()
            print(f"Active Sessions: {len(active)}")
            for session in active[:5]:  # Show first 5
                print(f"  - {session['session_id']}: "
                      f"inactive {session['inactive_minutes']:.1f} min")

    except KeyboardInterrupt:
        print("\n\nStopping service...")
        service.stop()
        print("Service stopped. Goodbye!")
