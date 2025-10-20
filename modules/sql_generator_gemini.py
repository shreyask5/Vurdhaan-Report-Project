# sql_generator_gemini.py

"""
SQL Agent for Flight Data Analysis - PostgreSQL Implementation with Google Gemini 2.5 Pro

A sophisticated SQL agent using Google's Gemini 2.5 Pro with function calling for natural language
to SQL conversion and execution with PostgreSQL, featuring single-call orchestrated workflow.

SINGLE-CALL ORCHESTRATED WORKFLOW:
- Gemini 2.5 Pro handles the entire query processing in one invocation
- Uses function calling to execute SQL, retrieve schema, compute statistics
- Supports both summary requests and analytical queries
- Maintains conversation history for multi-turn chat

FEATURES:
- Intent analysis and query improvement
- SQL generation and safe execution via tools
- Comprehensive table summaries with statistics
- Flight-specific analysis (routes, fuel consumption, errors)
- Error handling with intelligent retry logic
- Multi-turn conversation support

Author: Vurdhaan Report Project
Dependencies: google-generativeai, pandas, psycopg2, config
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import psycopg2
import psycopg2.extras

# Google Generative AI
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from google.generativeai.types import content_types

from config import Config

logger = logging.getLogger(__name__)

# ============================================================================
# GEMINI CONFIGURATION
# ============================================================================

def get_gemini_api_key(key: str = "GEMINI_API_KEY_1") -> str:
    """Get Gemini API key from config by key name"""
    api_key = getattr(Config, key, None)
    if not api_key:
        raise ValueError(f"Gemini API key '{key}' not found in configuration")
    return api_key


# ============================================================================
# FUNCTION/TOOL DECLARATIONS FOR GEMINI
# ============================================================================

def create_function_declarations() -> List[FunctionDeclaration]:
    """Create function declarations for Gemini's function calling"""

    return [
        # SQL Execution
        FunctionDeclaration(
            name="run_sql",
            description="Execute a SQL query against the PostgreSQL database and return results. Use this for analytical queries that need data retrieval.",
            parameters={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to execute. Must be a valid PostgreSQL query."
                    }
                },
                "required": ["sql"]
            }
        ),

        # Schema Information
        FunctionDeclaration(
            name="get_database_schema",
            description="Get complete database schema information including all tables, columns, data types, and sample data.",
            parameters={
                "type": "object",
                "properties": {}
            }
        ),

        FunctionDeclaration(
            name="get_table_info",
            description="Get detailed information about a specific table including column definitions and row count.",
            parameters={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table (clean_flights or error_flights)"
                    }
                },
                "required": ["table_name"]
            }
        ),

        FunctionDeclaration(
            name="get_sample_rows",
            description="Get sample rows from a table for data exploration.",
            parameters={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of rows to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["table_name"]
            }
        ),

        # Summary Generation
        FunctionDeclaration(
            name="generate_table_summary",
            description="Generate a comprehensive statistical summary of a table including column analysis, data distribution, and flight-specific metrics.",
            parameters={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to summarize"
                    }
                },
                "required": ["table_name"]
            }
        ),

        # Flight-Specific Analysis
        FunctionDeclaration(
            name="compute_fuel_statistics",
            description="Compute detailed fuel consumption statistics for flights.",
            parameters={
                "type": "object",
                "properties": {}
            }
        ),

        FunctionDeclaration(
            name="compute_route_statistics",
            description="Compute statistics about flight routes (origin-destination pairs).",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of top routes to return (default: 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        ),

        FunctionDeclaration(
            name="compute_aircraft_statistics",
            description="Compute statistics about aircraft registrations and usage.",
            parameters={
                "type": "object",
                "properties": {}
            }
        ),

        # SQL Validation
        FunctionDeclaration(
            name="validate_sql_query",
            description="Validate a SQL query without executing it. Returns whether the query is valid.",
            parameters={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "The SQL query to validate"
                    }
                },
                "required": ["sql"]
            }
        )
    ]


# ============================================================================
# TOOL IMPLEMENTATION FUNCTIONS
# ============================================================================

class GeminiFlightDataAgent:
    """SQL Agent using Gemini 2.5 Pro with function calling for flight data analysis"""

    def __init__(self, db_manager, session_id: str = None, max_attempts: int = 3, key: str = "GEMINI_API_KEY_1"):
        """
        Initialize Gemini SQL Agent with database manager

        Args:
            db_manager: PostgreSQL database manager instance
            session_id: Session identifier
            max_attempts: Maximum retry attempts for failed queries
            key: API key identifier from config (e.g., "GEMINI_API_KEY_1")
        """

        self.session_id = session_id or "default_session"
        self.max_attempts = max_attempts
        self.key = key

        # Database manager
        if not db_manager:
            raise ValueError("db_manager is required - cannot be None")
        self.db_manager = db_manager

        # Initialize Gemini
        api_key = get_gemini_api_key(key)
        genai.configure(api_key=api_key)

        # Create model with function calling
        self.model = genai.GenerativeModel(
            model_name=Config.GEMINI_MODEL,
            tools=[Tool(function_declarations=create_function_declarations())]
        )

        # Conversation history for chat support
        self.chat_history = []

        logger.info(f"🚀 Successfully initialized Gemini SQL Agent with {Config.GEMINI_MODEL} for session: {self.session_id}")
        logger.info(f"🔑 Using API key: {key}")

    # ========================================================================
    # TOOL IMPLEMENTATION METHODS
    # ========================================================================

    def _run_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        try:
            logger.info(f"🔍 Executing SQL: {sql[:200]}...")

            data, error = self.db_manager.execute_query(sql)

            if error:
                return {
                    "success": False,
                    "error": error,
                    "rows": []
                }

            return {
                "success": True,
                "rows": data[:100],  # Limit to 100 rows for response size
                "total_rows": len(data),
                "truncated": len(data) > 100
            }
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "rows": []
            }

    def _get_database_schema(self) -> Dict[str, Any]:
        """Get complete database schema information"""
        try:
            schema_info = {}
            table_info = self.db_manager.get_table_info()

            for table_name, info in table_info.items():
                columns = []
                for col in info['schema']:
                    columns.append({
                        "name": col["column_name"],
                        "type": col["data_type"],
                        "nullable": col.get("nullable", True)
                    })

                schema_info[table_name] = {
                    "row_count": info['row_count'],
                    "columns": columns
                }

            return {
                "success": True,
                "tables": schema_info
            }
        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific table"""
        try:
            table_info = self.db_manager.get_table_info()

            if table_name not in table_info:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found"
                }

            info = table_info[table_name]
            return {
                "success": True,
                "table_name": table_name,
                "row_count": info['row_count'],
                "columns": [
                    {
                        "name": col["column_name"],
                        "type": col["data_type"],
                        "nullable": col.get("nullable", True)
                    }
                    for col in info['schema']
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_sample_rows(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """Get sample rows from a table"""
        try:
            sql = f'SELECT * FROM "{table_name}" LIMIT {limit}'
            data, error = self.db_manager.execute_query(sql)

            if error:
                return {
                    "success": False,
                    "error": error
                }

            return {
                "success": True,
                "rows": data,
                "count": len(data)
            }
        except Exception as e:
            logger.error(f"Failed to get sample rows: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_table_summary(self, table_name: str) -> Dict[str, Any]:
        """Generate comprehensive table summary with statistics"""
        try:
            from modules.sql_generator import generate_table_summary

            summary_md = generate_table_summary(self.db_manager, table_name, 'public', 5)

            return {
                "success": True,
                "summary": summary_md
            }
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _compute_fuel_statistics(self) -> Dict[str, Any]:
        """Compute fuel consumption statistics"""
        try:
            sql = '''
                SELECT
                    AVG("Block off Fuel" - "Block on Fuel") as avg_fuel_consumed,
                    MIN("Block off Fuel" - "Block on Fuel") as min_fuel_consumed,
                    MAX("Block off Fuel" - "Block on Fuel") as max_fuel_consumed,
                    STDDEV("Block off Fuel" - "Block on Fuel") as std_fuel_consumed,
                    COUNT(*) as total_flights
                FROM clean_flights
                WHERE "Block off Fuel" IS NOT NULL AND "Block on Fuel" IS NOT NULL
            '''

            data, error = self.db_manager.execute_query(sql)

            if error:
                return {"success": False, "error": error}

            return {
                "success": True,
                "statistics": data[0] if data else {}
            }
        except Exception as e:
            logger.error(f"Failed to compute fuel statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _compute_route_statistics(self, limit: int = 10) -> Dict[str, Any]:
        """Compute route statistics"""
        try:
            sql = f'''
                SELECT
                    "Origin ICAO" || ' → ' || "Destination ICAO" as route,
                    COUNT(*) as flight_count,
                    AVG("Block off Fuel" - "Block on Fuel") as avg_fuel
                FROM clean_flights
                GROUP BY "Origin ICAO", "Destination ICAO"
                ORDER BY flight_count DESC
                LIMIT {limit}
            '''

            data, error = self.db_manager.execute_query(sql)

            if error:
                return {"success": False, "error": error}

            return {
                "success": True,
                "routes": data
            }
        except Exception as e:
            logger.error(f"Failed to compute route statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _compute_aircraft_statistics(self) -> Dict[str, Any]:
        """Compute aircraft statistics"""
        try:
            sql = '''
                SELECT
                    "A/C Registration",
                    COUNT(*) as flight_count,
                    AVG("Block off Fuel" - "Block on Fuel") as avg_fuel,
                    MIN("Date") as first_flight,
                    MAX("Date") as last_flight
                FROM clean_flights
                GROUP BY "A/C Registration"
                ORDER BY flight_count DESC
                LIMIT 20
            '''

            data, error = self.db_manager.execute_query(sql)

            if error:
                return {"success": False, "error": error}

            return {
                "success": True,
                "aircraft": data
            }
        except Exception as e:
            logger.error(f"Failed to compute aircraft statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _validate_sql_query(self, sql: str) -> Dict[str, Any]:
        """Validate SQL query without executing"""
        try:
            is_valid, error = self.db_manager.validate_sql(sql)

            return {
                "success": True,
                "valid": is_valid,
                "error": error if not is_valid else None
            }
        except Exception as e:
            logger.error(f"Failed to validate SQL: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # FUNCTION CALL DISPATCHER
    # ========================================================================

    def _execute_function_call(self, function_call) -> str:
        """Execute a function call and return JSON result"""
        function_name = function_call.name
        function_args = dict(function_call.args)

        logger.info(f"📞 Function call: {function_name} with args: {function_args}")

        # Dispatch to appropriate function
        if function_name == "run_sql":
            result = self._run_sql(function_args.get("sql", ""))
        elif function_name == "get_database_schema":
            result = self._get_database_schema()
        elif function_name == "get_table_info":
            result = self._get_table_info(function_args.get("table_name", ""))
        elif function_name == "get_sample_rows":
            result = self._get_sample_rows(
                function_args.get("table_name", ""),
                function_args.get("limit", 5)
            )
        elif function_name == "generate_table_summary":
            result = self._generate_table_summary(function_args.get("table_name", ""))
        elif function_name == "compute_fuel_statistics":
            result = self._compute_fuel_statistics()
        elif function_name == "compute_route_statistics":
            result = self._compute_route_statistics(function_args.get("limit", 10))
        elif function_name == "compute_aircraft_statistics":
            result = self._compute_aircraft_statistics()
        elif function_name == "validate_sql_query":
            result = self._validate_sql_query(function_args.get("sql", ""))
        else:
            result = {
                "success": False,
                "error": f"Unknown function: {function_name}"
            }

        return json.dumps(result, default=str)

    # ========================================================================
    # MAIN QUERY PROCESSING
    # ========================================================================

    def process_query(self, question: str, session_id: str = None) -> Dict[str, Any]:
        """
        Process a natural language query using Gemini's function calling

        This is a single-call orchestrated approach where Gemini handles:
        1. Intent analysis and query improvement
        2. Function calls to execute SQL or retrieve data
        3. Comprehensive analysis and response generation

        Args:
            question: Natural language question
            session_id: Optional session ID

        Returns:
            Dict with success status, answer, metadata, and optional table_rows
        """
        session_id = session_id or self.session_id
        logger.info(f"🔍 Processing query for session: {session_id}")
        logger.info(f"🗄️ Using database: {self.db_manager.db_name}")
        logger.info(f"❓ Question: {question}")

        try:
            # Create system instruction
            system_instruction = """You are an expert flight operations data analyst with access to a PostgreSQL database containing flight data.

AVAILABLE TABLES:
- clean_flights: Main flight operations data with details like aircraft registration, routes, fuel consumption, timestamps
- error_flights: Data quality errors and issues in flight operations

YOUR TASK:
1. Analyze the user's question to understand their intent
2. Determine if they want:
   - A summary/overview of a table
   - Specific analytical insights (requires SQL queries)
3. Use the available functions to:
   - Get schema information if needed
   - Generate summaries for overview requests
   - Execute SQL queries for analytical questions
   - Compute flight-specific statistics (fuel, routes, aircraft)
4. Provide comprehensive, professional analysis of the results

IMPORTANT GUIDELINES:
- For summary requests (e.g., "what are the errors?", "tell me about the data"), use generate_table_summary
- For analytical queries, use run_sql to execute queries
- Always include specific numbers and metrics in your analysis
- Identify patterns, trends, and anomalies
- Use professional aviation terminology
- Provide operational insights when relevant

RESPONSE FORMAT:
- Start with a concise summary of key findings
- Provide detailed analysis with specific metrics
- Include operational recommendations if relevant
- Highlight any data quality issues or limitations"""

            # Add user question to chat history
            self.chat_history.append({
                "role": "user",
                "parts": [question]
            })

            # Start chat session with history
            chat = self.model.start_chat(history=self.chat_history[:-1])  # Exclude the last message we just added

            # Send message
            response = chat.send_message(question)

            # Handle function calls
            max_iterations = 10  # Prevent infinite loops
            iteration = 0

            while response.candidates[0].content.parts[0].function_call and iteration < max_iterations:
                iteration += 1
                logger.info(f"🔄 Function call iteration {iteration}")

                function_calls = [
                    part.function_call
                    for part in response.candidates[0].content.parts
                    if hasattr(part, 'function_call') and part.function_call
                ]

                # Execute function calls
                function_responses = []
                for fc in function_calls:
                    function_result = self._execute_function_call(fc)
                    function_responses.append(
                        content_types.to_part({
                            "function_response": {
                                "name": fc.name,
                                "response": {"result": function_result}
                            }
                        })
                    )

                # Send function responses back to model
                response = chat.send_message(function_responses)

            # Extract final answer
            final_answer = response.text

            # Add assistant response to history
            self.chat_history.append({
                "role": "model",
                "parts": [final_answer]
            })

            logger.info(f"✅ Query processed successfully")

            return {
                "success": True,
                "answer": final_answer,
                "metadata": {
                    "session_id": session_id,
                    "database": self.db_manager.db_name,
                    "model": Config.GEMINI_MODEL,
                    "function_calls": iteration,
                    "original_question": question
                }
            }

        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "answer": f"I encountered an error while processing your query: {str(e)}",
                "error": str(e),
                "metadata": {
                    "session_id": session_id,
                    "database": self.db_manager.db_name,
                    "model": Config.GEMINI_MODEL,
                    "original_question": question
                }
            }

    def get_conversation_summary(self) -> str:
        """Generate a summary of the conversation history"""
        if not self.chat_history:
            return "No conversation history available."

        try:
            summary_prompt = "Please provide a concise summary of our conversation so far, highlighting the key questions asked and insights discovered about the flight data."

            chat = self.model.start_chat(history=self.chat_history)
            response = chat.send_message(summary_prompt)

            return response.text
        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {e}")
            return f"Error generating summary: {str(e)}"

    def clear_history(self):
        """Clear conversation history"""
        self.chat_history = []
        logger.info("🧹 Conversation history cleared")

    def close(self):
        """Close database connections"""
        logger.info(f"🔗 Gemini SQL Agent closed for session: {self.session_id}")


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_gemini_sql_agent(db_manager, session_id: str = None, max_attempts: int = 3,
                            key: str = "GEMINI_API_KEY_1") -> GeminiFlightDataAgent:
    """
    Factory function to create Gemini SQL agent instance with existing database manager

    Args:
        db_manager: Existing PostgreSQL database manager (required)
        session_id: Session identifier
        max_attempts: Maximum retry attempts for failed queries
        key: API key identifier from config (e.g., "GEMINI_API_KEY_1")

    Returns:
        GeminiFlightDataAgent instance
    """

    if not db_manager:
        raise ValueError("db_manager is required and cannot be None")

    logger.info("🔧 Creating Gemini-based SQL Agent with existing database manager")
    logger.info(f"🗄️ Session database: {getattr(db_manager, 'db_name', 'unknown')}")
    logger.info(f"🆔 Session ID: {session_id or 'default'}")
    logger.info(f"🔑 API Key: {key}")

    return GeminiFlightDataAgent(db_manager, session_id, max_attempts, key)


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print("🚀 Gemini SQL Agent Example")
    print("=" * 80)

    try:
        from modules.database import PostgreSQLManager

        # This is just an example - in production, use appropriate paths
        test_session_id = "test_gemini_session"
        print(f"📊 Creating database manager for session: {test_session_id}")

        db_manager = PostgreSQLManager(test_session_id)
        print(f"✅ Database manager created for database: {db_manager.db_name}")

        # Create Gemini agent
        print(f"🤖 Creating Gemini SQL agent...")
        agent = create_gemini_sql_agent(
            db_manager=db_manager,
            session_id=test_session_id,
            max_attempts=3,
            key="GEMINI_API_KEY_1"
        )
        print(f"✅ Gemini SQL agent created successfully")

        # Test query
        test_question = "What tables are available in the database?"
        print(f"\n❓ Test Question: {test_question}")

        result = agent.process_query(test_question)

        print(f"\n📊 Success: {result['success']}")
        print(f"💬 Answer: {result['answer'][:200]}...")

        print(f"\n✅ Test completed successfully!")

        agent.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
