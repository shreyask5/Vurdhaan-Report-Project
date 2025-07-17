#!/usr/bin/env python3
"""
SQL Agent Example Usage

This script demonstrates how to use the FlightDataSQLAgent for natural language
queries against flight operations data stored in DuckDB.

Run this script to test the SQL agent functionality.
"""

import os
import sys
import json
from datetime import datetime

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.sql_generator import create_sql_agent, FlightDataSQLAgent
from modules.utils import setup_logging
from config import Config

def main():
    """Main example function"""
    
    # Setup logging
    setup_logging('logs/sql_agent_example.log', 'INFO')
    
    print("🛩️  Flight Data SQL Agent Example")
    print("=" * 50)
    
    # Create SQL agent
    print("1. Initializing SQL Agent...")
    agent = create_sql_agent()
    print("✅ SQL Agent initialized successfully")
    
    # Example table schemas (normally would come from database)
    sample_schemas = {
        "clean_flights": [
            {"column_name": "Date", "column_type": "VARCHAR"},
            {"column_name": "A/C Registration", "column_type": "VARCHAR"},
            {"column_name": "Flight", "column_type": "VARCHAR"},
            {"column_name": "Origin ICAO", "column_type": "VARCHAR"},
            {"column_name": "Destination ICAO", "column_type": "VARCHAR"},
            {"column_name": "Fuel Volume", "column_type": "DOUBLE"},
            {"column_name": "Uplift weight", "column_type": "DOUBLE"},
            {"column_name": "Block Off Time", "column_type": "VARCHAR"},
            {"column_name": "Block On Time", "column_type": "VARCHAR"}
        ],
        "error_flights": [
            {"column_name": "Error_Category", "column_type": "VARCHAR"},
            {"column_name": "Row_Index", "column_type": "INTEGER"},
            {"column_name": "Error_Reason", "column_type": "VARCHAR"},
            {"column_name": "Date", "column_type": "VARCHAR"}
        ]
    }
    
    # Example queries to test
    example_queries = [
        "How many flights were there in total?",
        "What is the average fuel consumption per flight?",
        "Show me flights from KJFK to EGLL",
        "Which aircraft registration has the highest fuel usage?",
        "What are the most common error types in the data?",
        "Show me all flights on 01/01/2024",
        "What is the weather like today?"  # This should be marked as not relevant
    ]
    
    print(f"\n2. Testing {len(example_queries)} example queries...")
    print("-" * 50)
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-" * 30)
        
        try:
            # Process the query
            result = agent.process_query(
                question=query,
                session_id=f"example_session_{i}",
                table_schemas=sample_schemas
            )
            
            # Display results
            if result["success"]:
                print("✅ Success!")
                print(f"Answer: {result['answer']}")
                
                if "metadata" in result:
                    metadata = result["metadata"]
                    print(f"📊 SQL Query: {metadata.get('sql_query', 'N/A')}")
                    print(f"📈 Total Rows: {metadata.get('total_rows', 'N/A')}")
                    print(f"🧠 Context Used: {metadata.get('context_used', 'N/A')} tokens")
                    
                    if metadata.get('data_sample'):
                        print(f"📋 Sample Data: {json.dumps(metadata['data_sample'][:2], indent=2)}")
            else:
                print("❌ Failed")
                print(f"Response: {result['answer']}")
                if "error" in result:
                    print(f"Error: {result['error']}")
                    
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        print()
    
    print("🎉 Example completed!")
    print("\n" + "=" * 50)
    print("📚 Key Features Demonstrated:")
    print("• Natural language to SQL conversion")
    print("• Relevance checking for flight data domain")
    print("• Automatic query chunking for large results")
    print("• Error handling and query rewriting")
    print("• Context window management")
    print("• Structured responses with metadata")

def test_duckdb_connection():
    """Test connection to DuckDB HTTP server"""
    print("\n🔗 Testing DuckDB HTTP connection...")
    
    from modules.sql_generator import DuckDBHTTPClient
    
    try:
        client = DuckDBHTTPClient()
        
        # Test simple query
        result, error = client.execute_query("SELECT 1 as test")
        
        if error:
            print(f"❌ Connection failed: {error}")
            print("🔧 Make sure DuckDB HTTP server is running on 80.225.222.10:8080")
            return False
        else:
            print(f"✅ Connection successful! Result: {result}")
            return True
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Flight Data SQL Agent - Example & Test Script")
    print("=" * 60)
    
    # Test DuckDB connection first
    if test_duckdb_connection():
        print("\n" + "=" * 60)
        # Run main example
        main()
    else:
        print("\n⚠️  Cannot proceed without DuckDB connection.")
        print("Please ensure:")
        print("1. DuckDB HTTP server is running on 80.225.222.10:8080")
        print("2. Network connectivity is available")
        print("3. Server is accessible from your location") 