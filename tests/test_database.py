import pytest
import tempfile
import os
from modules.database import DuckDBManager
import pandas as pd

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.duckdb', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def sample_csv_files():
    """Create sample CSV files for testing"""
    # Create clean data
    clean_data = pd.DataFrame({
        'Date': ['01/01/2024', '02/01/2024'],
        'A/C Registration': ['N12345', 'N67890'],
        'Flight': ['AA100', 'AA101'],
        'Fuel_Volume': [1000, 1500]
    })
    
    # Create error data
    error_data = pd.DataFrame({
        'Error_Category': ['Data', 'Format'],
        'Row_Index': [1, 2],
        'Error_Reason': ['Missing value', 'Invalid format']
    })
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        clean_data.to_csv(f, index=False)
        clean_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        error_data.to_csv(f, index=False)
        error_path = f.name
    
    yield clean_path, error_path
    
    # Cleanup
    os.remove(clean_path)
    os.remove(error_path)

def test_database_connection(temp_db):
    """Test database connection"""
    db = DuckDBManager('test_session', temp_db)
    assert db.conn is not None
    db.close()

def test_load_csv_data(temp_db, sample_csv_files):
    """Test CSV loading"""
    clean_path, error_path = sample_csv_files
    db = DuckDBManager('test_session', temp_db)
    
    result = db.load_csv_data(clean_path, error_path)
    
    assert result['status'] == 'success'
    assert result['clean_flights']['row_count'] == 2
    assert result['error_flights']['row_count'] == 2
    
    db.close()

def test_execute_query(temp_db, sample_csv_files):
    """Test query execution"""
    clean_path, error_path = sample_csv_files
    db = DuckDBManager('test_session', temp_db)
    
    # Load data
    db.load_csv_data(clean_path, error_path)
    
    # Execute query
    results, error = db.execute_query("SELECT COUNT(*) as count FROM clean_flights")
    
    assert error is None
    assert len(results) == 1
    assert results[0]['count'] == 2
    
    db.close()