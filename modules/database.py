import duckdb
import pandas as pd
import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import sys

logger = logging.getLogger(__name__)

class DuckDBManager:
    """Manages DuckDB connections and operations for flight data (Local Ubuntu Server)"""
    
    def __init__(self, session_id: str, db_path: str = None):
        self.session_id = session_id
        # Create database in a dedicated directory
        self.db_dir = os.path.join('/var/lib/duckdb', 'sessions')  # or wherever you want
        os.makedirs(self.db_dir, exist_ok=True)
        
        self.db_path = os.path.join(self.db_dir, f"{session_id}.db")
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Establish connection to DuckDB"""
        try:
            print(f"🔌 [DEBUG] DuckDB Manager → Connecting to local database: {self.db_path}", flush=True)
            print(f"🗄️ [DEBUG] DuckDB Manager → Database name: {os.path.basename(self.db_path)}", flush=True)
            
            self.conn = duckdb.connect(self.db_path)
            
            print(f"✅ [DEBUG] DuckDB Manager → Successfully connected to local database for session: {self.session_id}", flush=True)
            logger.info(f"Connected to local DuckDB for session {self.session_id}")
        except Exception as e:
            print(f"❌ [DEBUG] DuckDB Manager → Failed to connect to local database: {str(e)}", flush=True)
            logger.error(f"Failed to connect to local DuckDB: {e}")
            raise
    
    def _check_tables_exist(self) -> bool:
        """Check if required tables exist in the database"""
        try:
            # Check if clean_flights table exists
            result = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clean_flights'").fetchall()
            clean_exists = len(result) > 0
            
            # Check if error_flights table exists
            result = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='error_flights'").fetchall()
            error_exists = len(result) > 0
            
            print(f"🔍 [DEBUG] DuckDB Manager → Tables exist: clean_flights={clean_exists}, error_flights={error_exists}", flush=True)
            
            return clean_exists and error_exists
        except Exception as e:
            print(f"⚠️ [DEBUG] DuckDB Manager → Error checking tables: {str(e)}", flush=True)
            return False
    
    def load_csv_data(self, clean_csv_path: str, error_csv_path: str) -> Dict[str, Any]:
        """Load CSV files into DuckDB tables with automatic schema detection"""
        try:
            print(f"📊 [DEBUG] DuckDB Manager → Starting CSV data loading", flush=True)
            print(f"📊 [DEBUG] DuckDB Manager → Session: {self.session_id}", flush=True)
            print(f"📊 [DEBUG] DuckDB Manager → Database: {self.db_path}", flush=True)
            
            # Check if database exists and has required tables
            tables_exist = self._check_tables_exist()
            
            if not tables_exist:
                print(f"📋 [DEBUG] DuckDB Manager → Tables don't exist, creating new tables", flush=True)
                
                # Drop existing tables if any
                try:
                    self.conn.execute("DROP TABLE IF EXISTS clean_flights")
                    self.conn.execute("DROP TABLE IF EXISTS error_flights")
                    print(f"🗑️ [DEBUG] DuckDB Manager → Dropped existing tables", flush=True)
                except Exception as e:
                    print(f"⚠️ [DEBUG] DuckDB Manager → Error dropping tables (expected): {e}", flush=True)
                
                # Load clean data
                print(f"📈 [DEBUG] DuckDB Manager → Loading clean data from: {clean_csv_path}", flush=True)
                logger.info(f"Loading clean data from {clean_csv_path}")
                
                # Check if file exists
                if not os.path.exists(clean_csv_path):
                    raise FileNotFoundError(f"Clean CSV file not found: {clean_csv_path}")
                
                self.conn.execute(f"""
                    CREATE TABLE clean_flights AS 
                    SELECT * FROM read_csv_auto('{clean_csv_path}', 
                        header=true, 
                        sample_size=10000,
                        ignore_errors=true
                    )
                """)
                print(f"✅ [DEBUG] DuckDB Manager → Clean flights table created successfully", flush=True)
                
                # Load error data
                print(f"📉 [DEBUG] DuckDB Manager → Loading error data from: {error_csv_path}", flush=True)
                logger.info(f"Loading error data from {error_csv_path}")
                
                # Check if file exists
                if not os.path.exists(error_csv_path):
                    raise FileNotFoundError(f"Error CSV file not found: {error_csv_path}")
                
                self.conn.execute(f"""
                    CREATE TABLE error_flights AS 
                    SELECT * FROM read_csv_auto('{error_csv_path}', 
                        header=true, 
                        sample_size=10000,
                        ignore_errors=true
                    )
                """)
                print(f"✅ [DEBUG] DuckDB Manager → Error flights table created successfully", flush=True)
                
                # Create indexes for common query patterns
                print(f"🔍 [DEBUG] DuckDB Manager → Creating database indexes", flush=True)
                self._create_indexes()
                print(f"✅ [DEBUG] DuckDB Manager → Database indexes created", flush=True)
            else:
                print(f"✅ [DEBUG] DuckDB Manager → Tables already exist, skipping data loading", flush=True)
            
            # Get table info
            clean_count = self.conn.execute("SELECT COUNT(*) FROM clean_flights").fetchone()[0]
            error_count = self.conn.execute("SELECT COUNT(*) FROM error_flights").fetchone()[0]
            
            print(f"📊 [DEBUG] DuckDB Manager → Clean flights loaded: {clean_count} rows", flush=True)
            print(f"📊 [DEBUG] DuckDB Manager → Error flights loaded: {error_count} rows", flush=True)
            
            # Get schema info
            clean_schema = self._get_table_schema('clean_flights')
            error_schema = self._get_table_schema('error_flights')
            print(f"📋 [DEBUG] DuckDB Manager → Clean flights schema: {len(clean_schema)} columns", flush=True)
            print(f"📋 [DEBUG] DuckDB Manager → Error flights schema: {len(error_schema)} columns", flush=True)
            
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
            
            print(f"🎉 [DEBUG] DuckDB Manager → Data loading completed successfully!", flush=True)
            return result
            
        except Exception as e:
            print(f"💥 [DEBUG] DuckDB Manager → Failed to load CSV data: {str(e)}", flush=True)
            logger.error(f"Failed to load CSV data: {e}")
            raise
    
    def _create_indexes(self):
        """Create indexes on frequently queried columns"""
        index_columns = {
            'clean_flights': ['Date', '"A/C Registration"', 'Flight', '"Origin ICAO"', '"Destination ICAO"'],
            'error_flights': ['Error_Category', 'Row_Index', 'Date']
        }
        
        for table, columns in index_columns.items():
            for column in columns:
                try:
                    clean_column = column.replace(' ', '_').replace('/', '_').replace('"', '')
                    index_name = f"idx_{table}_{clean_column}"
                    self.conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
                    logger.info(f"Created index {index_name}")
                except Exception as e:
                    logger.warning(f"Could not create index on {table}.{column}: {e}")
    
    def _get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """Get schema information for a table"""
        try:
            result = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
            return [
                {
                    'column_name': row[0],
                    'data_type': row[1],
                    'nullable': row[2] if len(row) > 2 else None,
                    'default': row[3] if len(row) > 3 else None,
                    'extra': row[4] if len(row) > 4 else None
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Failed to get schema for {table_name}: {e}")
            return []
    
    def execute_query(self, sql: str, params: Optional[Dict] = None) -> Tuple[List[Dict], Optional[str]]:
        """Execute SQL query and return results"""
        try:
            print(f"🔍 [DEBUG] DuckDB Manager → Executing SQL: {sql[:200]}...", flush=True)
            
            if params:
                result = self.conn.execute(sql, params).fetchall()
            else:
                result = self.conn.execute(sql).fetchall()
            
            # Get column names
            columns = [desc[0] for desc in self.conn.description]
            
            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in result]
            
            print(f"📊 [DEBUG] DuckDB Manager → Query returned {len(data)} rows", flush=True)
            
            return data, None
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return [], str(e)
    
    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """Validate SQL query without executing it"""
        try:
            # Use EXPLAIN to validate without executing
            self.conn.execute(f"EXPLAIN {sql}")
            return True, None
        except Exception as e:
            return False, str(e)
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about all tables in the database"""
        try:
            tables = self.conn.execute("SHOW TABLES").fetchall()
            table_info = {}
            
            for table in tables:
                table_name = table[0]
                schema = self._get_table_schema(table_name)
                row_count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                
                table_info[table_name] = {
                    'schema': schema,
                    'row_count': row_count
                }
            
            return table_info
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info(f"Closed DuckDB connection for session {self.session_id}")
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old session databases"""
        try:
            current_time = datetime.now()
            
            for filename in os.listdir(self.db_dir):
                if filename.endswith('.db'):
                    file_path = os.path.join(self.db_dir, filename)
                    file_age = current_time - datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_age.total_seconds() > max_age_hours * 3600:
                        os.remove(file_path)
                        logger.info(f"Removed old session database: {filename}")
                        
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")