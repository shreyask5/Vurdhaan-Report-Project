# database.py

import psycopg2
import psycopg2.extras
from psycopg2 import sql
import pandas as pd
import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import sys
import subprocess

logger = logging.getLogger(__name__)

class PostgreSQLManager:
    """Manages PostgreSQL connections and operations for flight data (Local Ubuntu Server)"""
    
    def __init__(self, session_id: str, db_path: str = None):
        self.session_id = session_id
        
        # Keep the same directory structure for compatibility
        self.db_dir = os.path.join('/var/lib/duckdb', 'sessions')
        os.makedirs(self.db_dir, exist_ok=True)
        
        # Create a marker file to track session (for compatibility with existing code)
        self.db_path = os.path.join(self.db_dir, f"{session_id}.db")
        
        # PostgreSQL connection parameters for the main server
        self.pg_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', 5432),
            'user': os.getenv('POSTGRES_USER', 'app_user'),
            'password': os.getenv('POSTGRES_PASSWORD', '1234')
        }
        
        # Create database name based on session_id (PostgreSQL database names must be lowercase)
        self.db_name = f"session_{session_id.lower().replace('-', '_')}"
        self.conn = None
        
        # Create the session database if it doesn't exist
        self._create_database_if_not_exists()
        self._connect()
        
        # Create marker file for session tracking
        self._create_session_marker()
    
    def _create_session_marker(self):
        """Create a marker file to track the session for compatibility"""
        try:
            # Create an empty marker file
            with open(self.db_path, 'w') as f:
                f.write(f"PostgreSQL Database: {self.db_name}\n")
                f.write(f"Session ID: {self.session_id}\n")
                f.write(f"Created: {datetime.now().isoformat()}\n")
            print(f"📝 [DEBUG] PostgreSQL Manager → Created session marker: {self.db_path}", flush=True)
        except Exception as e:
            print(f"⚠️ [DEBUG] PostgreSQL Manager → Failed to create marker file: {str(e)}", flush=True)
    
    def _create_database_if_not_exists(self):
        """Create a PostgreSQL database for this session if it doesn't exist"""
        try:
            # Connect to PostgreSQL server (default 'postgres' database)
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
                (self.db_name,)
            )
            exists = cursor.fetchone()
            
            if not exists:
                # Create the database
                print(f"📁 [DEBUG] PostgreSQL Manager → Creating new database: {self.db_name}", flush=True)
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(self.db_name)
                    )
                )
                print(f"✅ [DEBUG] PostgreSQL Manager → Database created: {self.db_name}", flush=True)
            else:
                print(f"✅ [DEBUG] PostgreSQL Manager → Database already exists: {self.db_name}", flush=True)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ [DEBUG] PostgreSQL Manager → Failed to create database: {str(e)}", flush=True)
            logger.error(f"Failed to create database: {e}")
            raise
    
    def _connect(self):
        """Establish connection to PostgreSQL session database"""
        try:
            print(f"🔌 [DEBUG] PostgreSQL Manager → Connecting to session database: {self.db_name}", flush=True)
            print(f"🗄️ [DEBUG] PostgreSQL Manager → Database name: {self.db_name}", flush=True)
            
            self.conn = psycopg2.connect(
                host=self.pg_config['host'],
                port=self.pg_config['port'],
                database=self.db_name,
                user=self.pg_config['user'],
                password=self.pg_config['password']
            )
            
            # Set autocommit to False for transaction control
            self.conn.autocommit = False
            
            print(f"✅ [DEBUG] PostgreSQL Manager → Successfully connected to session database for: {self.session_id}", flush=True)
            logger.info(f"Connected to PostgreSQL session database for {self.session_id}")
        except Exception as e:
            print(f"❌ [DEBUG] PostgreSQL Manager → Failed to connect to session database: {str(e)}", flush=True)
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def _check_tables_exist(self) -> bool:
        """Check if required tables exist in the database"""
        try:
            cursor = self.conn.cursor()
            
            # Check if clean_flights table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'clean_flights'
                )
            """)
            clean_exists = cursor.fetchone()[0]
            
            # Check if error_flights table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'error_flights'
                )
            """)
            error_exists = cursor.fetchone()[0]
            
            cursor.close()
            
            print(f"🔍 [DEBUG] PostgreSQL Manager → Tables exist: clean_flights={clean_exists}, error_flights={error_exists}", flush=True)
            
            return clean_exists and error_exists
        except Exception as e:
            print(f"⚠️ [DEBUG] PostgreSQL Manager → Error checking tables: {str(e)}", flush=True)
            self.conn.rollback()
            return False
    
    def load_csv_data(self, clean_csv_path: str, error_csv_path: str) -> Dict[str, Any]:
        """Load CSV files into PostgreSQL tables with automatic schema detection"""
        try:
            print(f"📊 [DEBUG] PostgreSQL Manager → Starting CSV data loading", flush=True)
            print(f"📊 [DEBUG] PostgreSQL Manager → Session: {self.session_id}", flush=True)
            print(f"📊 [DEBUG] PostgreSQL Manager → Database: {self.db_name}", flush=True)
            
            # Check if database exists and has required tables
            tables_exist = self._check_tables_exist()
            
            if not tables_exist:
                print(f"📋 [DEBUG] PostgreSQL Manager → Tables don't exist, creating new tables", flush=True)
                
                cursor = self.conn.cursor()
                
                # Drop existing tables if any
                try:
                    cursor.execute("DROP TABLE IF EXISTS clean_flights CASCADE")
                    cursor.execute("DROP TABLE IF EXISTS error_flights CASCADE")
                    self.conn.commit()
                    print(f"🗑️ [DEBUG] PostgreSQL Manager → Dropped existing tables", flush=True)
                except Exception as e:
                    print(f"⚠️ [DEBUG] PostgreSQL Manager → Error dropping tables (expected): {e}", flush=True)
                    self.conn.rollback()
                
                cursor.close()
                
                # Load clean data
                print(f"📈 [DEBUG] PostgreSQL Manager → Loading clean data from: {clean_csv_path}", flush=True)
                logger.info(f"Loading clean data from {clean_csv_path}")
                
                # Check if file exists
                if not os.path.exists(clean_csv_path):
                    raise FileNotFoundError(f"Clean CSV file not found: {clean_csv_path}")
                
                self._create_table_from_csv(clean_csv_path, 'clean_flights')
                print(f"✅ [DEBUG] PostgreSQL Manager → Clean flights table created successfully", flush=True)
                
                # Load error data
                print(f"📉 [DEBUG] PostgreSQL Manager → Loading error data from: {error_csv_path}", flush=True)
                logger.info(f"Loading error data from {error_csv_path}")
                
                # Check if file exists
                if not os.path.exists(error_csv_path):
                    raise FileNotFoundError(f"Error CSV file not found: {error_csv_path}")
                
                self._create_table_from_csv(error_csv_path, 'error_flights')
                print(f"✅ [DEBUG] PostgreSQL Manager → Error flights table created successfully", flush=True)
                
                # Create indexes for common query patterns
                print(f"🔍 [DEBUG] PostgreSQL Manager → Creating database indexes", flush=True)
                self._create_indexes()
                print(f"✅ [DEBUG] PostgreSQL Manager → Database indexes created", flush=True)
            else:
                print(f"✅ [DEBUG] PostgreSQL Manager → Tables already exist, skipping data loading", flush=True)
            
            # Get table info
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clean_flights")
            clean_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM error_flights")
            error_count = cursor.fetchone()[0]
            cursor.close()
            
            print(f"📊 [DEBUG] PostgreSQL Manager → Clean flights loaded: {clean_count} rows", flush=True)
            print(f"📊 [DEBUG] PostgreSQL Manager → Error flights loaded: {error_count} rows", flush=True)
            
            # Get schema info
            clean_schema = self._get_table_schema('clean_flights')
            error_schema = self._get_table_schema('error_flights')
            print(f"📋 [DEBUG] PostgreSQL Manager → Clean flights schema: {len(clean_schema)} columns", flush=True)
            print(f"📋 [DEBUG] PostgreSQL Manager → Error flights schema: {len(error_schema)} columns", flush=True)
            
            result = {
                'status': 'success',
                'clean_flights': {
                    'row_count': clean_count,
                    'schema': clean_schema
                },
                'error_flights': {
                    'row_count': error_count,
                    'schema': error_schema
                }
            }
            
            print(f"🎉 [DEBUG] PostgreSQL Manager → Data loading completed successfully!", flush=True)
            return result
            
        except Exception as e:
            print(f"💥 [DEBUG] PostgreSQL Manager → Failed to load CSV data: {str(e)}", flush=True)
            logger.error(f"Failed to load CSV data: {e}")
            self.conn.rollback()
            raise
    
    def _create_table_from_csv(self, csv_path: str, table_name: str):
        """Create a PostgreSQL table from CSV and load data"""
        # Read CSV to infer schema
        df = pd.read_csv(csv_path, nrows=1000)  # Sample for schema detection
        
        cursor = self.conn.cursor()
        
        # Generate CREATE TABLE statement
        columns = []
        for col in df.columns:
            # Keep original column names with quotes
            col_name = f'"{col}"'
            
            # Infer PostgreSQL data type
            dtype = df[col].dtype
            if dtype == 'object':
                # Check if it's a date column
                if 'date' in col.lower() or col in ['ATD (UTC) Block out', 'ATA (UTC) Block in']:
                    pg_type = 'TEXT'  # Keep as text like DuckDB does
                else:
                    pg_type = 'TEXT'
            elif dtype == 'int64':
                pg_type = 'BIGINT'
            elif dtype == 'float64':
                pg_type = 'DOUBLE PRECISION'
            elif dtype == 'bool':
                pg_type = 'BOOLEAN'
            else:
                pg_type = 'TEXT'
            
            columns.append(f"{col_name} {pg_type}")
        
        create_table_sql = f"""
            CREATE TABLE {table_name} (
                {', '.join(columns)}
            )
        """
        
        cursor.execute(create_table_sql)
        
        # Load data using COPY command for efficiency
        with open(csv_path, 'r') as f:
            cursor.copy_expert(
                f"COPY {table_name} FROM STDIN WITH CSV HEADER",
                f
            )
        
        self.conn.commit()
        cursor.close()
    
    def _create_indexes(self):
        """Create indexes on frequently queried columns"""
        index_columns = {
            'clean_flights': ['Date', '"A/C Registration"', 'Flight', '"Origin ICAO"', '"Destination ICAO"'],
            'error_flights': ['Error_Category', 'Row_Index', 'Date']
        }
        
        cursor = self.conn.cursor()
        
        for table, columns in index_columns.items():
            for column in columns:
                try:
                    clean_column = column.replace(' ', '_').replace('/', '_').replace('"', '')
                    index_name = f"idx_{table}_{clean_column}"
                    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
                    logger.info(f"Created index {index_name}")
                except Exception as e:
                    logger.warning(f"Could not create index on {table}.{column}: {e}")
        
        self.conn.commit()
        cursor.close()
    
    def _get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """Get schema information for a table"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            result = cursor.fetchall()
            cursor.close()
            
            return [
                {
                    'column_name': row[0],
                    'data_type': row[1],
                    'nullable': row[2] == 'YES',
                    'default': row[3],
                    'extra': row[4]  # character_maximum_length as extra
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Failed to get schema for {table_name}: {e}")
            return []
    
    def execute_query(self, sql: str, params: Optional[Dict] = None) -> Tuple[List[Dict], Optional[str]]:
        """Execute SQL query and return results"""
        try:
            print(f"🔍 [DEBUG] PostgreSQL Manager → Executing SQL: {sql[:200]}...", flush=True)
            
            cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # Get column names from cursor description
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                
                # Fetch results
                result = cursor.fetchall()
                
                # Convert RealDictCursor results to list of dicts
                data = [dict(row) for row in result]
            else:
                # For non-SELECT queries
                data = []
            
            # Commit for non-SELECT queries
            if not sql.strip().upper().startswith('SELECT'):
                self.conn.commit()
            
            cursor.close()
            
            print(f"📊 [DEBUG] PostgreSQL Manager → Query returned {len(data)} rows", flush=True)
            
            return data, None
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Query execution failed: {e}")
            return [], str(e)
    
    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """Validate SQL query without executing it"""
        try:
            cursor = self.conn.cursor()
            # Use EXPLAIN to validate without executing
            cursor.execute(f"EXPLAIN {sql}")
            cursor.close()
            return True, None
        except Exception as e:
            self.conn.rollback()
            return False, str(e)
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about all tables in the database"""
        try:
            cursor = self.conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            tables = cursor.fetchall()
            
            table_info = {}
            
            for table in tables:
                table_name = table[0]
                schema = self._get_table_schema(table_name)
                
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                table_info[table_name] = {
                    'schema': schema,
                    'row_count': row_count
                }
            
            cursor.close()
            return table_info
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info(f"Closed PostgreSQL connection for session {self.session_id}")
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old session databases"""
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
            
            # Get all session databases
            cursor.execute("""
                SELECT datname
                FROM pg_database
                WHERE datname LIKE 'session_%'
            """)
            
            databases = cursor.fetchall()
            current_time = datetime.now()
            
            # Also clean up marker files
            for filename in os.listdir(self.db_dir):
                if filename.endswith('.db'):
                    file_path = os.path.join(self.db_dir, filename)
                    file_age = current_time - datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_age.total_seconds() > max_age_hours * 3600:
                        # Extract session_id from filename
                        session_id = filename[:-3]  # Remove .db extension
                        db_name = f"session_{session_id.lower().replace('-', '_')}"
                        
                        # Drop database if exists
                        try:
                            cursor.execute(
                                sql.SQL("DROP DATABASE IF EXISTS {}").format(
                                    sql.Identifier(db_name)
                                )
                            )
                            logger.info(f"Dropped old session database: {db_name}")
                        except Exception as e:
                            logger.warning(f"Could not drop database {db_name}: {e}")
                        
                        # Remove marker file
                        os.remove(file_path)
                        logger.info(f"Removed old session marker: {filename}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")


# For backward compatibility, alias the class name
DuckDBManager = PostgreSQLManager