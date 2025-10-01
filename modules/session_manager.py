import os
import uuid
import json
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import sys
import stat
from pathlib import Path

from .database import DuckDBManager
from config import Config

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages chat sessions and database lifecycle for Ubuntu server"""
    
    def __init__(self):
        self.sessions = {}
        self.db_dir = '/var/lib/duckdb/sessions'
        self.upload_dir = '/root/report/uploads'
        self.log_dir = '/var/log/flight-analyzer/app.log'
        self._ensure_directories()
        self._load_existing_sessions()
    
    def _ensure_directories(self):
        """Ensure required directories exist with proper permissions"""
        try:
            # Create directories with proper permissions
            directories = [
                self.db_dir,
                self.upload_dir,
                self.log_dir,
                os.path.join(self.db_dir, 'backups'),  # For database backups
                os.path.join(self.log_dir, 'archived')  # For log archives
            ]
            
            for directory in directories:
                Path(directory).mkdir(parents=True, exist_ok=True)
                # Set permissions: owner read/write/execute, group read/execute, others read/execute
                os.chmod(directory, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                logger.info(f"📁 Created/verified directory: {directory}")
            
            # Create sessions metadata file if it doesn't exist
            sessions_file = os.path.join(self.db_dir, 'sessions.json')
            if not os.path.exists(sessions_file):
                with open(sessions_file, 'w') as f:
                    json.dump({}, f)
                os.chmod(sessions_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                logger.info(f"📄 Created sessions metadata file: {sessions_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {e}")
            raise
    
    def _load_existing_sessions(self):
        """Load existing sessions from disk with error handling"""
        session_file = os.path.join(self.db_dir, 'sessions.json')
        try:
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    self.sessions = json.load(f)
                
                # Validate existing sessions and clean up orphaned ones
                self._validate_existing_sessions()
                
                logger.info(f"📊 Loaded {len(self.sessions)} existing sessions")
            else:
                self.sessions = {}
                logger.info("📊 No existing sessions found, starting fresh")
                
        except Exception as e:
            logger.error(f"❌ Failed to load sessions: {e}")
            # Backup corrupted sessions file
            if os.path.exists(session_file):
                backup_file = f"{session_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(session_file, backup_file)
                logger.info(f"🔄 Backed up corrupted sessions file to: {backup_file}")
            
            self.sessions = {}
    
    def _validate_existing_sessions(self):
        """Validate existing sessions and remove orphaned ones"""
        orphaned_sessions = []
        
        for session_id, session_data in self.sessions.items():
            db_path = session_data.get('db_path')
            
            # Check if database file exists
            if db_path and not os.path.exists(db_path):
                logger.warning(f"⚠️ Database file missing for session {session_id}: {db_path}")
                orphaned_sessions.append(session_id)
                continue
            
            # Check if session has expired
            try:
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if datetime.now() > expires_at:
                    logger.info(f"⏰ Session {session_id} has expired")
                    orphaned_sessions.append(session_id)
            except (KeyError, ValueError) as e:
                logger.warning(f"⚠️ Invalid expiration date for session {session_id}: {e}")
                orphaned_sessions.append(session_id)
        
        # Clean up orphaned sessions
        for session_id in orphaned_sessions:
            self._cleanup_session_files(session_id)
            del self.sessions[session_id]
        
        if orphaned_sessions:
            logger.info(f"🧹 Cleaned up {len(orphaned_sessions)} orphaned sessions")
            self._save_sessions()
    
    def create_session(self, clean_csv: str, error_csv: str) -> Tuple[str, Dict]:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        print(f"🆔 [DEBUG] Session Manager → Generating new UUID session_id: {session_id}", flush=True)
        return self._create_session_internal(session_id, clean_csv, error_csv)
    
    def create_session_with_id(self, session_id: str, clean_csv: str, error_csv: str) -> Tuple[str, Dict]:
        """Create a new chat session with a specific session_id"""
        print(f"🆔 [DEBUG] Session Manager → Using provided session_id: {session_id}", flush=True)
        return self._create_session_internal(session_id, clean_csv, error_csv)
    
    def _create_session_internal(self, session_id: str, clean_csv: str, error_csv: str) -> Tuple[str, Dict]:
        """Internal method to create a session with given ID"""
        timestamp = datetime.now()
        
        # Create database path with session_id as the database name - use .db extension
        db_filename = f"{session_id}.db"
        db_path = os.path.join(self.db_dir, db_filename)
        print(f"🗄️ [DEBUG] Session Manager → Database will be created at: {db_path}", flush=True)
        print(f"🗄️ [DEBUG] Session Manager → Database name: {session_id}", flush=True)
        
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Get absolute paths for CSV files
        clean_csv_abs = os.path.abspath(clean_csv) if clean_csv else None
        error_csv_abs = os.path.abspath(error_csv) if error_csv else None
        
        session_data = {
            'session_id': session_id,
            'created_at': timestamp.isoformat(),
            'expires_at': (timestamp + timedelta(hours=Config.SESSION_TIMEOUT_HOURS)).isoformat(),
            'clean_csv': clean_csv_abs,
            'error_csv': error_csv_abs,
            'db_path': db_path,
            'status': 'initializing',
            'message_count': 0,
            'server_info': {
                'hostname': os.environ.get('COMPUTERNAME', os.environ.get('HOSTNAME', 'unknown')),
                'python_version': sys.version,
                'working_directory': os.getcwd(),
                'user': os.environ.get('USERNAME', os.environ.get('USER', 'unknown'))
            }
        }
        
        self.sessions[session_id] = session_data
        self._save_sessions()
        
        print(f"✅ [DEBUG] Session Manager → Session data saved: {session_id}", flush=True)
        logger.info(f"📝 Created new session: {session_id} on {session_data['server_info']['hostname']}")
        return session_id, session_data
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data with validation"""
        session = self.sessions.get(session_id)
        
        if session:
            # Check if session has expired
            try:
                expires_at = datetime.fromisoformat(session['expires_at'])
                if datetime.now() > expires_at:
                    logger.info(f"⏰ Session {session_id} has expired")
                    self.delete_session(session_id)
                    return None
            except (KeyError, ValueError) as e:
                logger.warning(f"⚠️ Invalid expiration date for session {session_id}: {e}")
                self.delete_session(session_id)
                return None
            
            # Check if database file still exists
            db_path = session.get('db_path')
            if db_path and not os.path.exists(db_path):
                logger.warning(f"⚠️ Database file missing for session {session_id}: {db_path}")
                self.delete_session(session_id)
                return None
        
        return session
    
    def update_session(self, session_id: str, updates: Dict):
        """Update session data with validation"""
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            self.sessions[session_id]['last_activity'] = datetime.now().isoformat()
            self._save_sessions()
            logger.debug(f"📝 Updated session {session_id}")
        else:
            logger.warning(f"⚠️ Attempted to update non-existent session: {session_id}")
    
    def delete_session(self, session_id: str):
        """Delete a session and its associated data"""
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"⚠️ Attempted to delete non-existent session: {session_id}")
            return
        
        # Clean up associated files
        self._cleanup_session_files(session_id)
        
        # Remove from sessions
        del self.sessions[session_id]
        self._save_sessions()
        
        logger.info(f"🗑️ Deleted session: {session_id}")
    
    def _cleanup_session_files(self, session_id: str):
        """Clean up all files associated with a session"""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        files_to_cleanup = []
        
        # Add database file
        db_path = session.get('db_path')
        if db_path:
            files_to_cleanup.append(db_path)
            # Also check for database journal files
            for ext in ['-wal', '-shm', '.tmp']:
                journal_file = db_path + ext
                if os.path.exists(journal_file):
                    files_to_cleanup.append(journal_file)
        
        # Add upload directory for this session
        upload_session_dir = os.path.join(self.upload_dir, session_id)
        if os.path.exists(upload_session_dir):
            files_to_cleanup.append(upload_session_dir)
        
        # Clean up files
        for file_path in files_to_cleanup:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    logger.info(f"🗑️ Removed directory: {file_path}")
                else:
                    os.remove(file_path)
                    logger.info(f"🗑️ Removed file: {file_path}")
            except Exception as e:
                logger.error(f"❌ Failed to remove {file_path}: {e}")
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions with detailed logging"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            try:
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if current_time > expires_at:
                    expired_sessions.append(session_id)
            except (KeyError, ValueError) as e:
                logger.warning(f"⚠️ Invalid expiration date for session {session_id}: {e}")
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def _save_sessions(self):
        """Save sessions to disk with atomic write and backup"""
        session_file = os.path.join(self.db_dir, 'sessions.json')
        temp_file = f"{session_file}.tmp"
        
        try:
            # Write to temporary file first
            with open(temp_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
            
            # Atomic move to final location
            shutil.move(temp_file, session_file)
            
            # Set proper permissions
            os.chmod(session_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            
            logger.debug(f"💾 Saved sessions to: {session_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save sessions: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def get_session_stats(self) -> Dict:
        """Get comprehensive statistics about sessions"""
        total_sessions = len(self.sessions)
        active_sessions = sum(
            1 for s in self.sessions.values() 
            if s.get('status') == 'active'
        )
        
        # Calculate disk usage
        disk_usage = 0
        db_file_count = 0
        
        try:
            for filename in os.listdir(self.db_dir):
                if filename.endswith('.db'):
                    file_path = os.path.join(self.db_dir, filename)
                    if os.path.isfile(file_path):
                        disk_usage += os.path.getsize(file_path)
                        db_file_count += 1
        except Exception as e:
            logger.error(f"❌ Failed to calculate disk usage: {e}")
        
        # Get system info
        try:
            stat_info = os.statvfs(self.db_dir)
            available_space = stat_info.f_bavail * stat_info.f_frsize
            total_space = stat_info.f_blocks * stat_info.f_frsize
        except Exception as e:
            logger.error(f"❌ Failed to get disk space info: {e}")
            available_space = 0
            total_space = 0
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'database_directory': self.db_dir,
            'upload_directory': self.upload_dir,
            'disk_usage_bytes': disk_usage,
            'disk_usage_mb': round(disk_usage / (1024 * 1024), 2),
            'db_file_count': db_file_count,
            'available_space_bytes': available_space,
            'available_space_gb': round(available_space / (1024 * 1024 * 1024), 2),
            'total_space_gb': round(total_space / (1024 * 1024 * 1024), 2),
            'cleanup_scheduled': True,
            'server_info': {
                'hostname': os.uname().nodename,
                'working_directory': os.getcwd(),
                'user': os.environ.get('USER', 'unknown')
            }
        }
    
    def backup_sessions(self, backup_dir: str = None) -> str:
        """Create a backup of all sessions and databases"""
        if backup_dir is None:
            backup_dir = os.path.join(self.db_dir, 'backups')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"sessions_backup_{timestamp}"
        backup_path = os.path.join(backup_dir, backup_name)
        
        try:
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy sessions.json
            sessions_file = os.path.join(self.db_dir, 'sessions.json')
            if os.path.exists(sessions_file):
                shutil.copy2(sessions_file, backup_path)
            
            # Copy all database files
            for filename in os.listdir(self.db_dir):
                if filename.endswith('.db'):
                    src = os.path.join(self.db_dir, filename)
                    dst = os.path.join(backup_path, filename)
                    shutil.copy2(src, dst)
            
            logger.info(f"💾 Created backup at: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            raise
    
    def get_system_health(self) -> Dict:
        """Get system health information"""
        health_info = {
            'timestamp': datetime.now().isoformat(),
            'directories_exist': all([
                os.path.exists(self.db_dir),
                os.path.exists(self.upload_dir),
                os.path.exists(self.log_dir)
            ]),
            'permissions_ok': True,
            'disk_space_ok': True,
            'sessions_file_ok': True
        }
        
        # Check permissions
        try:
            test_file = os.path.join(self.db_dir, 'test_permissions.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            health_info['permissions_ok'] = False
            health_info['permission_error'] = str(e)
        
        # Check disk space (warn if less than 1GB available)
        try:
            stat_info = os.statvfs(self.db_dir)
            available_space = stat_info.f_bavail * stat_info.f_frsize
            if available_space < 1024 * 1024 * 1024:  # Less than 1GB
                health_info['disk_space_ok'] = False
                health_info['available_space_gb'] = available_space / (1024 * 1024 * 1024)
        except Exception as e:
            health_info['disk_space_ok'] = False
            health_info['disk_space_error'] = str(e)
        
        # Check sessions file
        try:
            sessions_file = os.path.join(self.db_dir, 'sessions.json')
            if not os.path.exists(sessions_file):
                health_info['sessions_file_ok'] = False
            else:
                with open(sessions_file, 'r') as f:
                    json.load(f)
        except Exception as e:
            health_info['sessions_file_ok'] = False
            health_info['sessions_file_error'] = str(e)
        
        return health_info