"""
Tests for Flight Data SQL Agent

Tests cover the main functionality including natural language processing,
SQL generation, chunking, error handling, and workflow management.
"""

import pytest
import json
import unittest.mock as mock
from unittest.mock import Mock, patch, MagicMock

# Add modules to path for testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))

from modules.sql_generator import (
    FlightDataSQLAgent, 
    DuckDBHTTPClient, 
    create_sql_agent,
    AgentState
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_schemas():
    """Sample table schemas for testing"""
    return {
        "clean_flights": [
            {"column_name": "Date", "column_type": "VARCHAR"},
            {"column_name": "A/C Registration", "column_type": "VARCHAR"},
            {"column_name": "Flight", "column_type": "VARCHAR"},
            {"column_name": "Origin ICAO", "column_type": "VARCHAR"},
            {"column_name": "Destination ICAO", "column_type": "VARCHAR"},
            {"column_name": "Fuel Volume", "column_type": "DOUBLE"}
        ],
        "error_flights": [
            {"column_name": "Error_Category", "column_type": "VARCHAR"},
            {"column_name": "Row_Index", "column_type": "INTEGER"},
            {"column_name": "Error_Reason", "column_type": "VARCHAR"}
        ]
    }

@pytest.fixture
def sample_flight_data():
    """Sample flight data for testing"""
    return [
        {
            "Date": "01/01/2024",
            "A/C Registration": "N12345",
            "Flight": "AA100",
            "Origin ICAO": "KJFK",
            "Destination ICAO": "EGLL",
            "Fuel Volume": 15000.5
        },
        {
            "Date": "01/01/2024", 
            "A/C Registration": "N67890",
            "Flight": "AA101",
            "Origin ICAO": "EGLL",
            "Destination ICAO": "KJFK",
            "Fuel Volume": 14500.0
        }
    ]

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "choices": [{
            "message": {
                "function_call": {
                    "arguments": json.dumps({
                        "sql_query": "SELECT COUNT(*) as total_flights FROM clean_flights",
                        "query_type": "aggregate",
                        "estimated_rows": 1,
                        "explanation": "Count total flights"
                    })
                }
            }
        }]
    }

# ============================================================================
# DUCKDB HTTP CLIENT TESTS
# ============================================================================

class TestDuckDBHTTPClient:
    """Test DuckDB HTTP client functionality"""
    
    def test_init(self):
        """Test client initialization"""
        client = DuckDBHTTPClient("test-host", 9000)
        assert client.base_url == "http://test-host:9000"
        assert "application/json" in client.session.headers["Content-Type"]
    
    @patch('requests.Session.post')
    def test_execute_query_success(self, mock_post):
        """Test successful query execution"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"count": 100}]}
        mock_post.return_value = mock_response
        
        client = DuckDBHTTPClient()
        result, error = client.execute_query("SELECT COUNT(*) FROM flights")
        
        assert error is None
        assert result == [{"count": 100}]
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_execute_query_error(self, mock_post):
        """Test query execution with error"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "SQL syntax error"
        mock_post.return_value = mock_response
        
        client = DuckDBHTTPClient()
        result, error = client.execute_query("INVALID SQL")
        
        assert result == []
        assert "HTTP 400" in error
        assert "SQL syntax error" in error
    
    @patch('requests.Session.post')
    def test_execute_query_with_pagination(self, mock_post):
        """Test query execution with pagination"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": 1}, {"id": 2}]}
        mock_post.return_value = mock_response
        
        client = DuckDBHTTPClient()
        result, error = client.execute_query("SELECT * FROM flights", limit=10, offset=5)
        
        # Check that LIMIT and OFFSET were added
        call_args = mock_post.call_args[1]["json"]
        assert "LIMIT 10" in call_args["query"]
        assert "OFFSET 5" in call_args["query"]

# ============================================================================
# SQL AGENT TESTS  
# ============================================================================

class TestFlightDataSQLAgent:
    """Test main SQL agent functionality"""
    
    @patch('modules.sql_generator.openai.OpenAI')
    def test_agent_initialization(self, mock_openai):
        """Test agent initialization"""
        agent = FlightDataSQLAgent()
        assert agent.chunk_size == 1000
        assert agent.max_context_tokens > 0
        mock_openai.assert_called_once()
    
    @patch('modules.sql_generator.openai.OpenAI')
    @patch('modules.sql_generator.DuckDBHTTPClient')
    def test_relevance_check_relevant(self, mock_db, mock_openai, sample_schemas):
        """Test relevance check for flight-related questions"""
        # Mock OpenAI response for relevance check
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.function_call.arguments = json.dumps({
            "relevance": "relevant",
            "confidence": 0.9
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        agent = FlightDataSQLAgent()
        
        state = AgentState(
            question="How many flights were there?",
            sql_query="",
            query_result="",
            raw_data=[],
            session_id="test",
            table_schemas=sample_schemas,
            chunk_size=1000,
            total_rows=0,
            current_chunk=0,
            attempts=0,
            relevance="",
            sql_error=False,
            error_message="",
            context_used=0,
            max_context=50000
        )
        
        result_state = agent._workflow_check_relevance(state)
        assert result_state["relevance"] == "relevant"
    
    @patch('modules.sql_generator.openai.OpenAI')
    def test_sql_generation(self, mock_openai, sample_schemas):
        """Test SQL generation from natural language"""
        # Mock OpenAI response for SQL generation
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.function_call.arguments = json.dumps({
            "sql_query": "SELECT COUNT(*) as total FROM clean_flights",
            "query_type": "aggregate",
            "estimated_rows": 1,
            "explanation": "Count total flights"
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        agent = FlightDataSQLAgent()
        
        state = AgentState(
            question="How many flights were there?",
            sql_query="",
            query_result="",
            raw_data=[],
            session_id="test",
            table_schemas=sample_schemas,
            chunk_size=1000,
            total_rows=0,
            current_chunk=0,
            attempts=0,
            relevance="relevant",
            sql_error=False,
            error_message="",
            context_used=0,
            max_context=50000
        )
        
        result_state = agent._workflow_generate_sql(state)
        assert result_state["sql_query"] == "SELECT COUNT(*) as total FROM clean_flights"
        assert not result_state["sql_error"]
    
    @patch('modules.sql_generator.DuckDBHTTPClient')
    def test_sql_execution_chunked(self, mock_db_class, sample_flight_data):
        """Test chunked SQL execution"""
        # Mock DuckDB client
        mock_client = Mock()
        
        # Mock count query response
        mock_client.execute_query.side_effect = [
            ([{"total_count": 1000}], None),  # Count query
            (sample_flight_data, None)        # Data query
        ]
        mock_db_class.return_value = mock_client
        
        agent = FlightDataSQLAgent()
        
        state = AgentState(
            question="Show me all flights",
            sql_query="SELECT * FROM clean_flights",
            query_result="",
            raw_data=[],
            session_id="test",
            table_schemas={},
            chunk_size=1000,
            total_rows=0,
            current_chunk=0,
            attempts=0,
            relevance="relevant",
            sql_error=False,
            error_message="",
            context_used=0,
            max_context=50000
        )
        
        result_state = agent._workflow_execute_sql_chunked(state)
        assert result_state["total_rows"] == 1000
        assert len(result_state["raw_data"]) == 2
        assert not result_state["sql_error"]
    
    @patch('modules.sql_generator.openai.OpenAI')
    def test_query_rewriting(self, mock_openai):
        """Test query rewriting on errors"""
        # Mock OpenAI response for rewriting
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.function_call.arguments = json.dumps({
            "rewritten_question": "What is the total number of flight records in the clean_flights table?",
            "improvements": ["Added table specification", "Made query more specific"]
        })
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        agent = FlightDataSQLAgent()
        
        state = AgentState(
            question="How many flights?",
            sql_query="",
            query_result="",
            raw_data=[],
            session_id="test",
            table_schemas={},
            chunk_size=1000,
            total_rows=0,
            current_chunk=0,
            attempts=1,
            relevance="relevant",
            sql_error=True,
            error_message="Ambiguous query",
            context_used=0,
            max_context=50000
        )
        
        result_state = agent._workflow_rewrite_question(state)
        assert "total number of flight records" in result_state["question"]
    
    @patch('modules.sql_generator.openai.OpenAI')
    def test_final_answer_generation(self, mock_openai, sample_flight_data):
        """Test final answer generation"""
        # Mock OpenAI response for final answer
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Based on the flight data, there are 2 flights recorded with an average fuel volume of 14,750.25 liters."
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        agent = FlightDataSQLAgent()
        
        state = AgentState(
            question="How many flights were there?",
            sql_query="SELECT COUNT(*) FROM clean_flights",
            query_result="",
            raw_data=sample_flight_data,
            session_id="test",
            table_schemas={},
            chunk_size=1000,
            total_rows=2,
            current_chunk=1,
            attempts=0,
            relevance="relevant",
            sql_error=False,
            error_message="",
            context_used=500,
            max_context=50000
        )
        
        result = agent._workflow_generate_final_answer(state)
        assert result["success"] is True
        assert "flight data" in result["answer"]
        assert "sql_query" in result["metadata"]
        assert result["metadata"]["total_rows"] == 2

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestSQLAgentIntegration:
    """Integration tests for the complete workflow"""
    
    @patch('modules.sql_generator.openai.OpenAI')
    @patch('modules.sql_generator.DuckDBHTTPClient')
    def test_complete_workflow_success(self, mock_db_class, mock_openai, sample_schemas, sample_flight_data):
        """Test complete successful workflow"""
        # Mock OpenAI client
        mock_llm = Mock()
        
        # Mock responses for different workflow steps
        relevance_response = Mock()
        relevance_response.choices = [Mock()]
        relevance_response.choices[0].message.function_call.arguments = json.dumps({
            "relevance": "relevant", "confidence": 0.9
        })
        
        sql_response = Mock()
        sql_response.choices = [Mock()]
        sql_response.choices[0].message.function_call.arguments = json.dumps({
            "sql_query": "SELECT COUNT(*) as total FROM clean_flights",
            "query_type": "aggregate", "estimated_rows": 1, "explanation": "Count flights"
        })
        
        answer_response = Mock()
        answer_response.choices = [Mock()]
        answer_response.choices[0].message.content = "There are 2 flights in the database."
        
        mock_llm.chat.completions.create.side_effect = [
            relevance_response, sql_response, answer_response
        ]
        mock_openai.return_value = mock_llm
        
        # Mock DuckDB client
        mock_db = Mock()
        mock_db.execute_query.side_effect = [
            ([{"total_count": 2}], None),  # Count query
            ([{"total": 2}], None)         # Main query
        ]
        mock_db_class.return_value = mock_db
        
        # Test complete workflow
        agent = FlightDataSQLAgent()
        result = agent.process_query(
            "How many flights are there?",
            "test_session",
            sample_schemas
        )
        
        assert result["success"] is True
        assert "flights" in result["answer"]
        assert "total" in result["metadata"]["sql_query"]
    
    @patch('modules.sql_generator.openai.OpenAI')
    def test_not_relevant_question(self, mock_openai, sample_schemas):
        """Test handling of non-relevant questions"""
        # Mock OpenAI response for irrelevant question
        mock_llm = Mock()
        relevance_response = Mock()
        relevance_response.choices = [Mock()]
        relevance_response.choices[0].message.function_call.arguments = json.dumps({
            "relevance": "not_relevant", "confidence": 0.8
        })
        mock_llm.chat.completions.create.return_value = relevance_response
        mock_openai.return_value = mock_llm
        
        agent = FlightDataSQLAgent()
        result = agent.process_query(
            "What's the weather like today?",
            "test_session", 
            sample_schemas
        )
        
        assert result["success"] is False
        assert "flight operations data" in result["answer"]
        assert result["metadata"]["relevance"] == "not_relevant"

# ============================================================================
# UTILITY TESTS
# ============================================================================

def test_create_sql_agent():
    """Test agent factory function"""
    agent = create_sql_agent()
    assert isinstance(agent, FlightDataSQLAgent)

def test_agent_state_structure():
    """Test AgentState TypedDict structure"""
    state = AgentState(
        question="test",
        sql_query="",
        query_result="",
        raw_data=[],
        session_id="test",
        table_schemas={},
        chunk_size=1000,
        total_rows=0,
        current_chunk=0,
        attempts=0,
        relevance="",
        sql_error=False,
        error_message="",
        context_used=0,
        max_context=50000
    )
    
    assert state["question"] == "test"
    assert state["chunk_size"] == 1000
    assert state["sql_error"] is False

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 