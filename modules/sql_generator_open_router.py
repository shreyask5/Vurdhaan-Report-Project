# -*- coding: utf-8 -*-
# sql_generator_open_router.py

"""
SQL Agent for Flight Data Analysis - OpenRouter Implementation with Prompt Caching

A sophisticated SQL agent using OpenRouter API (OpenAI-compatible) for natural language
to SQL conversion and execution with PostgreSQL, featuring function calling and intelligent
prompt caching for cost optimization.

OPENROUTER FEATURES:
- Access to 400+ AI models through one API
- OpenAI-compatible interface
- Intelligent prompt caching (90% cost reduction)
- Model flexibility (Gemini, Claude, GPT, Llama, etc.)
- Automatic provider failover

PROMPT CACHING STRATEGY:
- Database schema: Cached with cache_control breakpoint
- System instructions: Cached for reuse across queries
- Tool definitions: Included in system message
- Conversation history: Maintained for multi-turn chat
- Cost savings: Up to 90% on cached tokens

SUPPORTED MODELS (with function calling):
- google/gemini-2.0-flash-exp:free (Free tier)
- google/gemini-2.5-flash (Implicit caching, cost-effective)
- anthropic/claude-3.5-sonnet (Best reasoning, cache_control support)
- anthropic/claude-3.5-haiku (Fast, cheap)
- openai/gpt-4-turbo (Automatic caching)
- deepseek/deepseek-chat (Very cheap, caching supported)

Author: Vurdhaan Report Project
Dependencies: openai (for OpenRouter), pandas, psycopg2, config
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# OpenAI client (works with OpenRouter)
from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)

# ============================================================================
# OPENROUTER CONFIGURATION
# ============================================================================

def get_openrouter_api_key(key: str = "OPENROUTER_API_KEY") -> str:
    """Get OpenRouter API key from config"""
    if key == "OPENROUTER_API_KEY":
        api_key = Config.OPENROUTER_API_KEY
    else:
        # Support for multiple keys if needed
        api_key = getattr(Config, key, None)

    if not api_key:
        raise ValueError(f"OpenRouter API key '{key}' not found in configuration. "
                        "Please set OPENROUTER_API_KEY in your .env file. "
                        "Get your key at: https://openrouter.ai/keys")
    return api_key


# ============================================================================
# TOOL/FUNCTION DEFINITIONS (OpenAI Format for OpenRouter)
# ============================================================================

def create_tool_definitions() -> List[Dict[str, Any]]:
    """
    Create tool definitions in OpenAI format for OpenRouter

    OpenRouter uses the same tool format as OpenAI:
    {
      "type": "function",
      "function": {
        "name": "function_name",
        "description": "...",
        "parameters": {...}
      }
    }
    """

    return [
        # SQL Execution
        {
            "type": "function",
            "function": {
                "name": "run_sql",
                "description": "Execute a SQL query against the PostgreSQL database and return results. Use this for analytical queries that need data retrieval.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "The SQL query to execute. Must be a valid PostgreSQL query."
                        }
                    },
                    "required": ["sql"]
                }
            }
        },

        # Schema Information
        {
            "type": "function",
            "function": {
                "name": "get_database_schema",
                "description": "Get complete database schema information including all tables, columns, data types, and row counts.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },

        {
            "type": "function",
            "function": {
                "name": "get_table_info",
                "description": "Get detailed information about a specific table including column definitions and row count.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table (clean_flights or error_flights)"
                        }
                    },
                    "required": ["table_name"]
                }
            }
        },

        {
            "type": "function",
            "function": {
                "name": "get_sample_rows",
                "description": "Get sample rows from a table for data exploration. The limit parameter is optional and defaults to 5 if not provided.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of rows to return (optional, defaults to 5)"
                        }
                    },
                    "required": ["table_name"]
                }
            }
        },

        # Summary Generation
        {
            "type": "function",
            "function": {
                "name": "generate_table_summary",
                "description": "Generate a comprehensive statistical summary of a table including column analysis, data distribution, and flight-specific metrics.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to summarize"
                        }
                    },
                    "required": ["table_name"]
                }
            }
        },

        # Flight-Specific Analysis
        {
            "type": "function",
            "function": {
                "name": "compute_fuel_statistics",
                "description": "Compute detailed fuel consumption statistics for flights.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },

        {
            "type": "function",
            "function": {
                "name": "compute_route_statistics",
                "description": "Compute statistics about flight routes (origin-destination pairs). The limit parameter is optional and defaults to 10 if not provided.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of top routes to return (optional, defaults to 10)"
                        }
                    },
                    "required": []
                }
            }
        },

        {
            "type": "function",
            "function": {
                "name": "compute_aircraft_statistics",
                "description": "Compute statistics about aircraft registrations and usage.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },

        # SQL Validation
        {
            "type": "function",
            "function": {
                "name": "validate_sql_query",
                "description": "Validate a SQL query without executing it. Returns whether the query is valid.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "The SQL query to validate"
                        }
                    },
                    "required": ["sql"]
                }
            }
        }
    ]


# ============================================================================
# OPENROUTER SQL AGENT WITH PROMPT CACHING
# ============================================================================

class OpenRouterFlightDataAgent:
    """SQL Agent using OpenRouter API with function calling and prompt caching"""

    def __init__(self, db_manager, session_id: str = None, max_attempts: int = 3,
                 key: str = "OPENROUTER_API_KEY", model: str = None):
        """
        Initialize OpenRouter SQL Agent with database manager

        Args:
            db_manager: PostgreSQL database manager instance
            session_id: Session identifier
            max_attempts: Maximum retry attempts for failed queries
            key: API key identifier from config (default: "OPENROUTER_API_KEY")
            model: Model to use (default: from Config.OPENROUTER_MODEL)
        """

        self.session_id = session_id or "default_session"
        self.max_attempts = max_attempts
        self.key = key

        # Database manager
        if not db_manager:
            raise ValueError("db_manager is required - cannot be None")
        self.db_manager = db_manager

        # Initialize OpenAI client pointing to OpenRouter
        api_key = get_openrouter_api_key(key)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # Model configuration
        self.model = model or Config.OPENROUTER_MODEL
        self.temperature = Config.OPENROUTER_TEMPERATURE
        self.max_tokens = Config.OPENROUTER_MAX_TOKENS
        self.enable_caching = Config.OPENROUTER_ENABLE_CACHING

        # Tool definitions
        self.tools = create_tool_definitions()

        # Detect cache support (Anthropic Claude and Google Gemini support cache_control)
        self.supports_cache_control = self._check_cache_support()

        # Message history for conversation
        self.messages = []

        # Track SQL execution for response structure
        self.last_sql_query = None
        self.last_sql_rows = []

        # Build cached system message once
        self.system_message = None
        self._initialize_system_message()

        logger.info(f"[OpenRouter] Successfully initialized SQL Agent")
        logger.info(f"[OpenRouter] Model: {self.model}")
        logger.info(f"[OpenRouter] Caching enabled: {self.enable_caching}")
        logger.info(f"[OpenRouter] Cache control support: {self.supports_cache_control}")
        logger.info(f"[OpenRouter] Session: {self.session_id}")

    def _check_cache_support(self) -> bool:
        """Check if the selected model supports cache_control breakpoints"""
        model_lower = self.model.lower()
        # Anthropic Claude and Google Gemini support cache_control
        return any(x in model_lower for x in ['claude', 'gemini'])

    def _initialize_system_message(self):
        """Initialize the system message with optional caching"""
        try:
            # Get database schema for caching
            schema_info = self._get_database_schema()
            schema_json = json.dumps(schema_info.get('tables', {}), indent=2)

            if not self.enable_caching or not self.supports_cache_control:
                # Simple format for models without cache_control
                system_text = f"""You are an expert flight operations data analyst with access to a PostgreSQL database containing flight data.

AVAILABLE TABLES:
- clean_flights: Main flight operations data with details like aircraft registration, routes, fuel consumption, timestamps
- error_flights: Data quality errors and issues in flight operations

DATABASE SCHEMA:
{schema_json}

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

IMPORTANT - TOKEN OPTIMIZATION:
- When you use run_sql, the table data will be automatically sent to the frontend
- DO NOT include the raw table data in your text response
- Instead, provide analysis, insights, and summaries with specific metrics
- Reference key findings from the data without printing entire rows
- The frontend will display the table separately from your analysis

RESPONSE FORMAT:
- Start with a concise summary of key findings
- Provide detailed analysis with specific metrics
- Include operational recommendations if relevant
- Highlight any data quality issues or limitations"""

                self.system_message = {
                    "role": "system",
                    "content": system_text
                }

            else:
                # Use cache_control breakpoints for Anthropic/Gemini
                self.system_message = {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": """You are an expert flight operations data analyst with access to a PostgreSQL database containing flight data.

AVAILABLE TABLES:
- clean_flights: Main flight operations data with details like aircraft registration, routes, fuel consumption, timestamps
- error_flights: Data quality errors and issues in flight operations"""
                        },
                        {
                            "type": "text",
                            "text": f"""DATABASE SCHEMA (CACHED - DO NOT MODIFY):

{schema_json}""",
                            "cache_control": {"type": "ephemeral"}  # Cache breakpoint 1
                        },
                        {
                            "type": "text",
                            "text": """YOUR TASK AND GUIDELINES:

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

IMPORTANT - TOKEN OPTIMIZATION:
- When you use run_sql, the table data will be automatically sent to the frontend
- DO NOT include the raw table data in your text response
- Instead, provide analysis, insights, and summaries with specific metrics
- Reference key findings from the data without printing entire rows
- The frontend will display the table separately from your analysis

RESPONSE FORMAT:
- Start with a concise summary of key findings
- Provide detailed analysis with specific metrics
- Include operational recommendations if relevant
- Highlight any data quality issues or limitations""",
                            "cache_control": {"type": "ephemeral"}  # Cache breakpoint 2
                        }
                    ]
                }

            logger.info("[OpenRouter] System message initialized with schema")

        except Exception as e:
            logger.error(f"[OpenRouter] Failed to initialize system message: {e}")
            # Fallback to simple system message
            self.system_message = {
                "role": "system",
                "content": "You are an expert flight operations data analyst. Use the available tools to help analyze flight data."
            }

    # ========================================================================
    # TOOL IMPLEMENTATION METHODS
    # ========================================================================

    def _run_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        try:
            logger.info(f"[Tool:run_sql] Executing: {sql[:200]}...")

            # Store query for response metadata
            self.last_sql_query = sql

            data, error = self.db_manager.execute_query(sql)

            if error:
                return {
                    "success": False,
                    "error": error,
                    "rows": []
                }

            # Store full results for response (frontend needs this)
            self.last_sql_rows = data

            return {
                "success": True,
                "rows": data[:100],  # Limit to 100 rows for LLM context
                "total_rows": len(data),
                "truncated": len(data) > 100
            }
        except Exception as e:
            logger.error(f"[Tool:run_sql] Failed: {e}")
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
            logger.error(f"[Tool:get_database_schema] Failed: {e}")
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
            logger.error(f"[Tool:get_table_info] Failed: {e}")
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
            logger.error(f"[Tool:get_sample_rows] Failed: {e}")
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
            logger.error(f"[Tool:generate_table_summary] Failed: {e}")
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
            logger.error(f"[Tool:compute_fuel_statistics] Failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _compute_route_statistics(self, limit: int = 10) -> Dict[str, Any]:
        """Compute route statistics"""
        try:
            sql = f'''
                SELECT
                    "Origin ICAO" || ' -> ' || "Destination ICAO" as route,
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
            logger.error(f"[Tool:compute_route_statistics] Failed: {e}")
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
            logger.error(f"[Tool:compute_aircraft_statistics] Failed: {e}")
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
            logger.error(f"[Tool:validate_sql_query] Failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ========================================================================
    # FUNCTION CALL DISPATCHER
    # ========================================================================

    def _execute_function_call(self, tool_call) -> Dict[str, Any]:
        """Execute a function call and return result"""
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        logger.info(f"[Function Call] {function_name} with args: {function_args}")

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

        return result

    # ========================================================================
    # MAIN QUERY PROCESSING (OpenRouter 3-Step Workflow)
    # ========================================================================

    def process_query(self, question: str, session_id: str = None) -> Dict[str, Any]:
        """
        Process a natural language query using OpenRouter's function calling

        OpenRouter follows a 3-step workflow:
        1. Send initial request with tools + messages
        2. Extract tool_calls from response
        3. Execute tools locally and send results back

        Args:
            question: Natural language question
            session_id: Optional session ID

        Returns:
            Dict with success status, answer, metadata
        """
        session_id = session_id or self.session_id
        logger.info(f"[Query] Processing for session: {session_id}")
        logger.info(f"[Query] Question: {question}")

        # Reset SQL tracking for new query
        self.last_sql_query = None
        self.last_sql_rows = []

        try:
            # Add user message
            self.messages.append({
                "role": "user",
                "content": question
            })

            # Build complete message list with cached system message
            api_messages = [self.system_message] + self.messages

            # Step 1: Call OpenRouter API with tools
            logger.info(f"[API Call] Calling OpenRouter with model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                extra_headers={
                    "HTTP-Referer": Config.OPENROUTER_SITE_URL,
                    "X-Title": Config.OPENROUTER_APP_NAME
                }
            )

            # Step 2 & 3: Handle tool calls in a loop
            max_iterations = 10
            iteration = 0

            while (response.choices[0].message.tool_calls and
                   iteration < max_iterations):
                iteration += 1
                logger.info(f"[Function Calling] Iteration {iteration}")

                assistant_message = response.choices[0].message

                # Add assistant's message with tool calls to history
                tool_calls_data = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]

                self.messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": tool_calls_data
                })

                # Execute each tool call and add results
                for tool_call in assistant_message.tool_calls:
                    result = self._execute_function_call(tool_call)

                    # Add tool result message
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str)
                    })

                # Build message list again (must include tools in every request!)
                api_messages = [self.system_message] + self.messages

                # Call API again with tool results
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=api_messages,
                    tools=self.tools,  # MUST include tools in every request
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    extra_headers={
                        "HTTP-Referer": Config.OPENROUTER_SITE_URL,
                        "X-Title": Config.OPENROUTER_APP_NAME
                    }
                )

            # Extract final answer
            final_answer = response.choices[0].message.content

            # Add final assistant message to history
            self.messages.append({
                "role": "assistant",
                "content": final_answer
            })

            # Extract usage stats for caching analysis
            usage = response.usage
            metadata = {
                "session_id": session_id,
                "database": self.db_manager.db_name,
                "model": self.model,
                "function_calls": iteration,
                "original_question": question,
                "sql_query": self.last_sql_query or "",
                "row_count": len(self.last_sql_rows),
                "tokens": {
                    "prompt": usage.prompt_tokens,
                    "completion": usage.completion_tokens,
                    "total": usage.total_tokens,
                }
            }

            # Add cache stats if available
            if hasattr(usage, 'prompt_tokens_details'):
                details = usage.prompt_tokens_details
                cached_tokens = getattr(details, 'cached_tokens', 0)
                if cached_tokens > 0:
                    metadata["tokens"]["cached"] = cached_tokens
                    metadata["cache_savings_pct"] = (cached_tokens / usage.prompt_tokens * 100)
                    logger.info(f"[Caching] Cached tokens: {cached_tokens} ({metadata['cache_savings_pct']:.1f}%)")

            logger.info(f"[Query] Success! Tokens used: {usage.total_tokens}")

            return {
                "success": True,
                "answer": final_answer,
                "metadata": metadata,
                "table_rows": self.last_sql_rows
            }

        except Exception as e:
            logger.error(f"[Query] Failed: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "answer": f"I encountered an error while processing your query: {str(e)}",
                "error": str(e),
                "metadata": {
                    "session_id": session_id,
                    "database": self.db_manager.db_name,
                    "model": self.model,
                    "original_question": question,
                    "sql_query": "",
                    "row_count": 0
                },
                "table_rows": []
            }

    def get_conversation_summary(self) -> str:
        """Generate a summary of the conversation history"""
        if not self.messages:
            return "No conversation history available."

        try:
            # Build summary request
            summary_messages = [self.system_message] + self.messages + [
                {
                    "role": "user",
                    "content": "Please provide a concise summary of our conversation so far, highlighting the key questions asked and insights discovered about the flight data."
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=summary_messages,
                temperature=0.3,
                max_tokens=self.max_tokens,
                extra_headers={
                    "HTTP-Referer": Config.OPENROUTER_SITE_URL,
                    "X-Title": Config.OPENROUTER_APP_NAME
                }
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"[Summary] Failed: {e}")
            return f"Error generating summary: {str(e)}"

    def clear_history(self):
        """Clear conversation history"""
        self.messages = []
        logger.info("[History] Conversation history cleared")

    def close(self):
        """Close agent (cleanup)"""
        logger.info(f"[OpenRouter] Agent closed for session: {self.session_id}")


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_openrouter_sql_agent(db_manager, session_id: str = None, max_attempts: int = 3,
                                key: str = "OPENROUTER_API_KEY",
                                model: str = None) -> OpenRouterFlightDataAgent:
    """
    Factory function to create OpenRouter SQL agent instance

    Args:
        db_manager: Existing PostgreSQL database manager (required)
        session_id: Session identifier
        max_attempts: Maximum retry attempts for failed queries
        key: API key identifier from config (default: "OPENROUTER_API_KEY")
        model: Model to use (default: from Config.OPENROUTER_MODEL)

    Returns:
        OpenRouterFlightDataAgent instance
    """

    if not db_manager:
        raise ValueError("db_manager is required and cannot be None")

    logger.info("[OpenRouter] Creating SQL Agent with existing database manager")
    logger.info(f"[OpenRouter] Session database: {getattr(db_manager, 'db_name', 'unknown')}")
    logger.info(f"[OpenRouter] Session ID: {session_id or 'default'}")
    logger.info(f"[OpenRouter] API Key: {key}")
    logger.info(f"[OpenRouter] Model: {model or Config.OPENROUTER_MODEL}")

    return OpenRouterFlightDataAgent(db_manager, session_id, max_attempts, key, model)


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print("[OpenRouter] SQL Agent Example")
    print("=" * 80)

    try:
        from modules.database import PostgreSQLManager

        # Example usage
        test_session_id = "test_openrouter_session"
        print(f"[*] Creating database manager for session: {test_session_id}")

        db_manager = PostgreSQLManager(test_session_id)
        print(f"[+] Database manager created: {db_manager.db_name}")

        # Create OpenRouter agent
        print(f"[*] Creating OpenRouter SQL agent...")
        agent = create_openrouter_sql_agent(
            db_manager=db_manager,
            session_id=test_session_id,
            max_attempts=3,
            key="OPENROUTER_API_KEY"
        )
        print(f"[+] OpenRouter SQL agent created successfully")

        # Test query
        test_question = "What tables are available in the database?"
        print(f"\n[?] Test Question: {test_question}")

        result = agent.process_query(test_question)

        print(f"\n[*] Success: {result['success']}")
        print(f"[*] Answer: {result['answer'][:200]}...")

        # Show caching stats if available
        if 'cached' in result.get('metadata', {}).get('tokens', {}):
            print(f"\n[*] Caching Stats:")
            print(f"    Cached tokens: {result['metadata']['tokens']['cached']}")
            print(f"    Cache savings: {result['metadata']['cache_savings_pct']:.1f}%")

        print(f"\n[+] Test completed successfully!")

        agent.close()

    except Exception as e:
        print(f"[-] Error: {e}")
        import traceback
        traceback.print_exc()
