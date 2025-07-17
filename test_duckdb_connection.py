#!/usr/bin/env python3
"""
DuckDB Connection Test Script

This script tests the connection to the DuckDB HTTP server and helps diagnose issues.
Run this script to test connectivity before using the main application.

Usage: python test_duckdb_connection.py
"""

import sys
import os
import logging

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.sql_generator import DuckDBHTTPClient
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main test function"""
    print("🧪 DuckDB Connection Test")
    print("=" * 50)
    
    # Display configuration
    print(f"📍 Host: {Config.DUCKDB_HOST}")
    print(f"🔌 Port: {Config.DUCKDB_PORT}")
    print(f"🔑 Token: {Config.DUCKDB_TOKEN[:10]}...{Config.DUCKDB_TOKEN[-5:] if len(Config.DUCKDB_TOKEN) > 15 else Config.DUCKDB_TOKEN}")
    print(f"🌐 Full URL: http://{Config.DUCKDB_HOST}:{Config.DUCKDB_PORT}")
    print()
    
    # Create client
    client = DuckDBHTTPClient()
    
    # Test 1: Basic connection test
    print("🧪 Test 1: Basic Connection Test")
    print("-" * 30)
    is_connected, message = client.test_connection()
    
    if is_connected:
        print(f"✅ Connection test passed: {message}")
    else:
        print(f"❌ Connection test failed: {message}")
        return False
    
    print()
    
    # Test 2: Simple SQL query
    print("🧪 Test 2: Simple SQL Query")
    print("-" * 30)
    
    test_queries = [
        "SELECT 1 as test",
        "SELECT CURRENT_TIMESTAMP as now", 
        "SHOW TABLES",
        "SELECT * FROM information_schema.tables LIMIT 5"
    ]
    
    for query in test_queries:
        print(f"📝 Testing query: {query}")
        result, error = client.execute_query(query)
        
        if error:
            print(f"❌ Query failed: {error}")
        else:
            print(f"✅ Query succeeded. Result: {result[:2] if result else 'No data'}")
        print()
    
    # Test 2.5: Test the exact format from working example
    print("🧪 Test 2.5: Working Example Format Test")
    print("-" * 40)
    
    import requests
    
    # Test using exact format from working example
    test_headers = {
        "X-API-Key": Config.DUCKDB_TOKEN,
        "Content-Type": "text/plain"
    }
    
    try:
        # Test ping
        ping_response = requests.get(f"http://{Config.DUCKDB_HOST}:{Config.DUCKDB_PORT}/ping", headers=test_headers)
        print(f"📍 Direct ping test: {ping_response.status_code} - {ping_response.text}")
        
        # Test simple SQL
        sql_response = requests.post(
            f"http://{Config.DUCKDB_HOST}:{Config.DUCKDB_PORT}/",
            params={"default_format": "JSONCompact"},
            data="SELECT 1 as test_direct",
            headers=test_headers
        )
        print(f"📍 Direct SQL test: {sql_response.status_code}")
        print(f"📍 Response: {sql_response.text}")
        
        if sql_response.status_code == 200:
            result_data = sql_response.json()
            print(f"✅ Direct API call successful!")
            print(f"📊 Response format: {type(result_data)}")
            print(f"📊 Response keys: {list(result_data.keys()) if isinstance(result_data, dict) else 'N/A'}")
        else:
            print(f"❌ Direct API call failed")
            
    except Exception as e:
        print(f"❌ Direct API test failed: {str(e)}")
    
    print()
    
    # Test 3: Schema information
    print("🧪 Test 3: Schema Information")
    print("-" * 30)
    
    schemas = client.get_table_schemas()
    if schemas:
        print(f"✅ Found {len(schemas)} tables:")
        for table_name, schema in list(schemas.items())[:5]:  # Show first 5 tables
            column_count = len(schema) if isinstance(schema, list) else 0
            print(f"  📊 {table_name}: {column_count} columns")
    else:
        print("❌ No tables found or schema query failed")
    
    print()
    print("🏁 Connection test completed!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception("Test script failed with exception:")
        print(f"💥 Test script crashed: {str(e)}")
        sys.exit(1) 