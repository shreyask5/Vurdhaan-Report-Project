import logging
import hashlib
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

def setup_logging(log_file: str, log_level: str = "INFO"):
    """Setup application logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def validate_csv_file(file_path: str) -> Tuple[bool, str]:
    """Validate CSV file"""
    try:
        # Check file exists
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "File is empty"
        
        if file_size > 100 * 1024 * 1024:  # 100MB limit
            return False, "File is too large (>100MB)"
        
        # Try to read CSV
        df = pd.read_csv(file_path, nrows=5)
        
        if df.empty:
            return False, "CSV file has no data"
        
        return True, "Valid CSV file"
        
    except Exception as e:
        return False, f"CSV validation error: {str(e)}"

def format_number(value: float) -> str:
    """Format number for display"""
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value/1_000:.1f}K"
    else:
        return f"{value:,.0f}"

def generate_session_token(session_id: str) -> str:
    """Generate a secure token for session"""
    return hashlib.sha256(f"{session_id}{datetime.now().isoformat()}".encode()).hexdigest()[:32]

def sanitize_sql(sql: str) -> str:
    """Basic SQL sanitization"""
    # Remove common SQL injection patterns
    dangerous_patterns = [
        "DROP TABLE", "DELETE FROM", "TRUNCATE", "ALTER TABLE",
        "CREATE TABLE", "INSERT INTO", "UPDATE SET"
    ]
    
    sql_upper = sql.upper()
    for pattern in dangerous_patterns:
        if pattern in sql_upper:
            logger.warning(f"Potentially dangerous SQL pattern detected: {pattern}")
            return ""
    
    return sql

def format_query_results(results: List[Dict], max_rows: int = 100) -> Dict[str, Any]:
    """Format query results for API response"""
    total_rows = len(results)
    
    # Limit rows
    display_results = results[:max_rows] if total_rows > max_rows else results
    
    # Calculate summary statistics for numeric columns
    if display_results:
        numeric_summaries = {}
        first_row = display_results[0]
        
        for key, value in first_row.items():
            if isinstance(value, (int, float)):
                column_values = [row[key] for row in display_results if row[key] is not None]
                if column_values:
                    numeric_summaries[key] = {
                        'min': min(column_values),
                        'max': max(column_values),
                        'avg': sum(column_values) / len(column_values),
                        'count': len(column_values)
                    }
    else:
        numeric_summaries = {}
    
    return {
        'data': display_results,
        'total_rows': total_rows,
        'displayed_rows': len(display_results),
        'truncated': total_rows > max_rows,
        'numeric_summaries': numeric_summaries
    }