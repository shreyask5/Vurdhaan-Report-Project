"""
SQL Agent for Flight Data Analysis

A sophisticated SQL agent that sits between natural language queries and DuckDB,
with automatic chunking, error handling, and iterative query refinement.

Author: Flight Data Analysis System
Dependencies: openai, requests, pydantic, typing_extensions
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime
import openai
from config import Config
import re
import duckdb

logger = logging.getLogger(__name__)

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

class AgentState(TypedDict):
    """State object that flows through the SQL agent workflow"""
    question: str                    # Original user question
    sql_query: str                  # Generated SQL query
    query_result: str               # Formatted result for LLM
    raw_data: List[Dict]           # Raw query results
    session_id: str                # Current session ID
    table_schemas: Dict[str, Any]  # Available table schemas
    chunk_size: int                # Current chunk size
    total_rows: int                # Total rows in result
    current_chunk: int             # Current chunk being processed
    attempts: int                  # Number of retry attempts
    relevance: str                 # Whether question is relevant
    sql_error: bool               # Whether SQL execution failed
    error_message: str            # Error details if any
    context_used: int             # Tokens used in context
    max_context: int              # Maximum context window


# ============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# ============================================================================

class RelevanceCheck(BaseModel):
    """Model for checking question relevance"""
    relevance: str = Field(
        description="Whether the question relates to flight data. 'relevant' or 'not_relevant'"
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1"
    )

class SQLGeneration(BaseModel):
    """Model for SQL query generation"""
    sql_query: str = Field(
        description="The DuckDB-compatible SQL query for the flight data"
    )
    query_type: str = Field(
        description="Type of query: 'simple', 'aggregate', 'analytical', 'comparison'"
    )
    estimated_rows: int = Field(
        description="Estimated number of rows this query will return"
    )
    explanation: str = Field(
        description="Brief explanation of what the query does"
    )

class QueryRewrite(BaseModel):
    """Model for query rewriting"""
    rewritten_question: str = Field(
        description="Improved version of the original question"
    )
    improvements: List[str] = Field(
        description="List of improvements made to the question"
    )


# =========================================================================
# DUCKDB LOCAL CLIENT (replaces HTTP client)
# =========================================================================

class DuckDBLocalClient:
    """Client for interacting with local DuckDB database"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or ":memory:"
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Connect to local DuckDB database"""
        try:
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"Connected to local DuckDB: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to local DuckDB: {e}")
            raise
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test basic connectivity to the DuckDB database"""
        try:
            logger.info(f"🧪 Testing local DuckDB connectivity...")
            logger.info(f"  📍 Database path: {self.db_path}")
            
            # Test with a simple query
            result = self.conn.execute("SELECT 1 as test").fetchall()
            
            if result and result[0][0] == 1:
                logger.info(f"  ✅ Connection test successful!")
                return True, "Connection successful"
            else:
                return False, "Connection test failed"
                
        except Exception as e:
            error_msg = f"Connection test failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

    def execute_query(self, sql: str, limit: Optional[int] = None, offset: Optional[int] = None) -> Tuple[List[Dict], Optional[str]]:
        """Execute SQL query with optional pagination"""
        try:
            # Add pagination if specified
            if limit is not None:
                if "LIMIT" not in sql.upper():
                    sql += f" LIMIT {limit}"
                if offset is not None and offset > 0:
                    sql += f" OFFSET {offset}"
            
            logger.info(f"Executing query: {sql[:100]}...")
            
            # Execute the query
            result = self.conn.execute(sql).fetchall()
            
            # Get column names
            columns = [desc[0] for desc in self.conn.description]
            
            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in result]
            
            logger.info(f"  ✅ Query successful! Returned {len(data)} records")
            return data, None
                
        except Exception as e:
            error_msg = f"Query execution failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return [], error_msg
    
    def get_table_schemas(self) -> Dict[str, List[Dict]]:
        """Get schema information for all tables"""
        try:
            # Get list of tables
            tables_data, error = self.execute_query("SHOW TABLES")
            if error:
                return {}
            
            schemas = {}
            for table_row in tables_data:
                table_name = table_row.get('name', list(table_row.values())[0])
                
                # Get schema for this table
                schema_data, error = self.execute_query(f"DESCRIBE {table_name}")
                if not error and schema_data:
                    schemas[table_name] = schema_data
            
            return schemas
            
        except Exception as e:
            logger.error(f"Failed to get table schemas: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Closed DuckDB connection")

# =========================================================================
# SQL AGENT IMPLEMENTATION
# =========================================================================

class FlightDataSQLAgent:
    """Main SQL Agent for flight data analysis"""
    
    def __init__(self, db_path: str = None):
        self.client = DuckDBLocalClient(db_path)
        
        # Initialize OpenAI client with error handling
        try:
            self.llm_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            logger.info("✅ OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise Exception(f"Could not initialize OpenAI client: {e}")
        
        self.model = Config.OPENAI_MODEL
        self.max_tokens = Config.OPENAI_MAX_TOKENS
        
        # Context management
        self.max_context_tokens = int(self.max_tokens * 0.7)  # Reserve 30% for response
        self.chunk_size = 1000  # Default chunk size
        
        # Test connection on initialization
        logger.info("🚀 Initializing SQL Agent - Testing local DuckDB connection...")
        is_connected, connection_msg = self.client.test_connection()
        if is_connected:
            logger.info(f"✅ Local DuckDB connection successful: {connection_msg}")
        else:
            logger.error(f"❌ Local DuckDB connection failed: {connection_msg}")
        
    def process_query(self, question: str, session_id: str, table_schemas: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for processing natural language queries"""
        
        # Initialize state
        state = AgentState(
            question=question,
            sql_query="",
            query_result="",
            raw_data=[],
            session_id=session_id,
            table_schemas=table_schemas,
            chunk_size=self.chunk_size,
            total_rows=0,
            current_chunk=0,
            attempts=0,
            relevance="",
            sql_error=False,
            error_message="",
            context_used=0,
            max_context=self.max_context_tokens
        )
        
        try:
            # Execute workflow
            state = self._workflow_check_relevance(state)
            
            if state["relevance"] == "not_relevant":
                return self._generate_not_relevant_response(state)
            
            # Main processing loop with chunking
            while state["attempts"] < 3:
                state = self._workflow_generate_sql(state)
                state = self._workflow_execute_sql_chunked(state)
                
                if not state["sql_error"]:
                    break
                    
                state = self._workflow_rewrite_question(state)
                state["attempts"] += 1
            
            if state["sql_error"]:
                return self._generate_error_response(state)
            
            # Generate final answer
            return self._workflow_generate_final_answer(state)
            
        except Exception as e:
            logger.error(f"Agent workflow failed: {e}")
            return {
                "success": False,
                "answer": "I encountered an error while processing your query. Please try again.",
                "error": str(e)
            }
    
    def _workflow_check_relevance(self, state: AgentState) -> AgentState:
        """Check if the question is relevant to flight data"""
        
        schema_summary = self._build_schema_summary(state["table_schemas"])
        
        system_prompt = f"""You are an expert at determining if questions relate to flight operations data.

Available Data:
{schema_summary}

Flight Data Context:
- Aircraft registrations and flight operations
- Fuel consumption and efficiency metrics
- Airport codes (ICAO) and route information
- Flight times, delays, and operational data
- Error logs and data quality issues

Determine if the user's question can be answered using this flight operations database."""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {state['question']}"}
                ],
                functions=[{
                    "name": "check_relevance",
                    "description": "Check if question relates to flight data",
                    "parameters": RelevanceCheck.model_json_schema()
                }],
                function_call={"name": "check_relevance"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.function_call.arguments)
            state["relevance"] = result["relevance"]
            
        except Exception as e:
            logger.error(f"Relevance check failed: {e}")
            state["relevance"] = "relevant"  # Default to relevant on error
        
        return state
    
    def _workflow_generate_sql(self, state: AgentState) -> AgentState:
        """Generate SQL query from natural language"""
        
        schema_context = self._build_detailed_schema_context(state["table_schemas"])
        
        system_prompt = f"""You are an expert SQL generator for flight operations data using DuckDB.

Database Schema:
{schema_context}

DuckDB-Specific Guidelines:
1. Use double quotes for column names with spaces: "A/C Registration"
2. Date functions: strptime() for parsing, date_trunc() for grouping
3. String functions: regexp_matches() for pattern matching
4. Use LIMIT for large datasets (recommend LIMIT 1000 for initial queries)
5. Handle NULL values with COALESCE() or IS NOT NULL

Flight Data Patterns:
- Aircraft: "A/C Registration", "A/C Type"
- Routes: "Origin ICAO", "Destination ICAO" 
- Fuel: "Fuel Volume", "Fuel Density", "Uplift weight"
- Times: "Block Off Time", "Block On Time", "Flight Time"
- Errors: Check error_flights table for data quality issues

Generate efficient, accurate DuckDB SQL queries."""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate SQL for: {state['question']}"}
                ],
                functions=[{
                    "name": "generate_sql",
                    "description": "Generate DuckDB SQL query",
                    "parameters": SQLGeneration.model_json_schema()
                }],
                function_call={"name": "generate_sql"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.function_call.arguments)
            state["sql_query"] = result["sql_query"]
            
            # Adjust chunk size based on estimated rows
            estimated_rows = result.get("estimated_rows", 1000)
            if estimated_rows > 10000:
                state["chunk_size"] = 500
            elif estimated_rows > 5000:
                state["chunk_size"] = 750
            else:
                state["chunk_size"] = 1000
                
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            state["sql_error"] = True
            state["error_message"] = f"Failed to generate SQL: {str(e)}"
        
        return state
    
    def _workflow_execute_sql_chunked(self, state: AgentState) -> AgentState:
        """Execute SQL with automatic chunking for large results"""
        
        try:
            # First, get total count if it's a SELECT query
            sql = state["sql_query"].strip()
            
            if sql.upper().startswith("SELECT"):
                # Clean SQL for count query: remove trailing semicolons and existing LIMIT/OFFSET
                clean_sql = sql.rstrip(';').strip()
                
                # Remove existing LIMIT and OFFSET clauses for count query
                # We need the total count, not limited count
                sql_lines = clean_sql.split('\n')
                filtered_lines = []
                
                for line in sql_lines:
                    line_upper = line.strip().upper()
                    # Skip lines that start with LIMIT or OFFSET
                    if not (line_upper.startswith('LIMIT ') or line_upper.startswith('OFFSET ')):
                        filtered_lines.append(line)
                
                count_base_sql = '\n'.join(filtered_lines).strip()
                
                # Remove any trailing LIMIT/OFFSET from the end of the query
                import re
                count_base_sql = re.sub(r'\s+LIMIT\s+\d+(\s+OFFSET\s+\d+)?\s*$', '', count_base_sql, flags=re.IGNORECASE)
                
                # Create count query
                count_sql = f"SELECT COUNT(*) as total_count FROM ({count_base_sql}) as subquery"
                
                logger.info(f"🔍 Count query: {count_sql}")
                count_data, error = self.client.execute_query(count_sql)
                
                if error:
                    logger.error(f"❌ Count query failed, testing connection...")
                    logger.error(f"❌ Original SQL: {sql}")
                    logger.error(f"❌ Cleaned SQL: {count_base_sql}")
                    logger.error(f"❌ Count SQL: {count_sql}")
                    is_connected, connection_msg = self.client.test_connection()
                    if not is_connected:
                        state["error_message"] = f"Database connection issue: {connection_msg}. Original error: {error}"
                    else:
                        state["error_message"] = f"Query execution failed: {error}"
                    state["sql_error"] = True
                    return state
                
                total_rows = count_data[0]["total_count"] if count_data else 0
                state["total_rows"] = total_rows
                
                # Execute chunked query using original SQL (but clean it)
                original_clean_sql = sql.rstrip(';').strip()
                all_data = []
                chunk_size = state["chunk_size"]
                current_offset = 0
                
                while current_offset < total_rows:
                    chunk_data, error = self.client.execute_query(
                        original_clean_sql,  # Use cleaned original SQL
                        limit=chunk_size, 
                        offset=current_offset
                    )
                    
                    if error:
                        logger.error(f"❌ Chunk query failed, testing connection...")
                        is_connected, connection_msg = self.client.test_connection()
                        if not is_connected:
                            state["error_message"] = f"Database connection issue: {connection_msg}. Original error: {error}"
                        else:
                            state["error_message"] = f"Query execution failed: {error}"
                        state["sql_error"] = True
                        break
                    
                    all_data.extend(chunk_data)
                    current_offset += chunk_size
                    state["current_chunk"] += 1
                    
                    # Check context limits
                    estimated_tokens = self._estimate_tokens(all_data)
                    if estimated_tokens > state["max_context"]:
                        logger.info(f"Stopping data collection at {len(all_data)} rows due to context limits")
                        break
                
                state["raw_data"] = all_data
                state["context_used"] = self._estimate_tokens(all_data)
                
            else:
                # Non-SELECT query (INSERT, UPDATE, etc.)
                clean_sql = sql.rstrip(';').strip()  # Clean non-SELECT queries too
                result_data, error = self.client.execute_query(clean_sql)
                
                if error:
                    state["sql_error"] = True
                    state["error_message"] = error
                else:
                    state["raw_data"] = result_data
                    state["total_rows"] = len(result_data) if result_data else 0
            
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            state["sql_error"] = True
            state["error_message"] = str(e)
        
        return state
    
    def _workflow_rewrite_question(self, state: AgentState) -> AgentState:
        """Rewrite the question to improve SQL generation"""
        
        system_prompt = """You are an expert at improving natural language questions for flight data analysis.

Common Issues to Fix:
1. Ambiguous date references → Specify exact date ranges
2. Vague aircraft references → Use specific registration or type
3. Missing aggregation details → Specify grouping and metrics
4. Unclear route references → Use ICAO codes when possible

Rewrite the question to be more specific and SQL-friendly while preserving the original intent."""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"""Original question: {state['question']}
Error encountered: {state['error_message']}

Please rewrite this question to be more specific and avoid the error."""}
                ],
                functions=[{
                    "name": "rewrite_question",
                    "description": "Rewrite question for better SQL generation",
                    "parameters": QueryRewrite.model_json_schema()
                }],
                function_call={"name": "rewrite_question"},
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.function_call.arguments)
            state["question"] = result["rewritten_question"]
            
        except Exception as e:
            logger.error(f"Question rewrite failed: {e}")
            # Keep original question if rewrite fails
        
        return state
    
    def _workflow_generate_final_answer(self, state: AgentState) -> Dict[str, Any]:
        """Generate final human-readable answer"""
        
        # Prepare data summary for LLM
        data_summary = self._prepare_data_summary(state["raw_data"], state["total_rows"])
        
        system_prompt = """You are a flight operations analyst providing clear, actionable insights from data.

Guidelines:
1. Start with a direct answer to the user's question
2. Include specific numbers and metrics when available
3. Highlight important patterns or anomalies
4. Suggest follow-up questions if relevant
5. Keep explanations concise but complete
6. Use aviation terminology appropriately"""

        user_prompt = f"""Question: {state['question']}

Data Summary:
{data_summary}

SQL Query Used: {state['sql_query']}

Total Records: {state['total_rows']}
Context Used: {state['context_used']} tokens

Provide a comprehensive answer based on this flight data."""

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            return {
                "success": True,
                "answer": answer,
                "metadata": {
                    "sql_query": state["sql_query"],
                    "total_rows": state["total_rows"],
                    "chunks_processed": state["current_chunk"],
                    "context_used": state["context_used"],
                    "data_sample": state["raw_data"][:5] if state["raw_data"] else []
                }
            }
            
        except Exception as e:
            logger.error(f"Final answer generation failed: {e}")
            return {
                "success": False,
                "answer": "I found the data but encountered an error while generating the response.",
                "error": str(e)
            }
    
    def _generate_not_relevant_response(self, state: AgentState) -> Dict[str, Any]:
        """Generate response for non-relevant questions"""
        return {
            "success": False,
            "answer": "I can only help with questions about flight operations data, including aircraft performance, fuel consumption, routes, and operational metrics. Please ask a question related to the flight data in our system.",
            "metadata": {"relevance": "not_relevant"}
        }
    
    def _generate_error_response(self, state: AgentState) -> Dict[str, Any]:
        """Generate response when all attempts failed"""
        return {
            "success": False,
            "answer": f"I encountered difficulties processing your query after {state['attempts']} attempts. The error was: {state['error_message']}. Please try rephrasing your question or contact support if the issue persists.",
            "metadata": {
                "attempts": state["attempts"],
                "final_error": state["error_message"]
            }
        }
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _build_schema_summary(self, schemas: Dict[str, Any]) -> str:
        """Build a concise schema summary"""
        summary = []
        for table_name, schema in schemas.items():
            column_count = len(schema) if isinstance(schema, list) else 0
            summary.append(f"- {table_name}: {column_count} columns")
        return "\n".join(summary)
    
    def _build_detailed_schema_context(self, schemas: Dict[str, Any]) -> str:
        """Build detailed schema context for SQL generation"""
        context = []
        for table_name, schema in schemas.items():
            context.append(f"\nTable: {table_name}")
            if isinstance(schema, list):
                for col in schema[:10]:  # Limit columns to prevent context overflow
                    col_name = col.get('column_name', col.get('name', 'unknown'))
                    col_type = col.get('column_type', col.get('type', 'unknown'))
                    context.append(f"  - {col_name} ({col_type})")
                if len(schema) > 10:
                    context.append(f"  ... and {len(schema) - 10} more columns")
        return "\n".join(context)
    
    def _estimate_tokens(self, data: List[Dict]) -> int:
        """Estimate token count for data"""
        if not data:
            return 0
        
        # Rough estimation: 4 characters per token
        sample_size = min(len(data), 10)
        sample_text = json.dumps(data[:sample_size])
        estimated_tokens = len(sample_text) * len(data) // (sample_size * 4)
        return estimated_tokens
    
    def _prepare_data_summary(self, data: List[Dict], total_rows: int) -> str:
        """Prepare data summary for final answer generation"""
        if not data:
            return "No data found."
        
        summary = [f"Found {total_rows} total records."]
        
        if len(data) < total_rows:
            summary.append(f"Showing first {len(data)} records due to context limits.")
        
        # Add sample data
        if data:
            summary.append("\nSample Data:")
            for i, row in enumerate(data[:3]):
                summary.append(f"Row {i+1}: {dict(list(row.items())[:5])}")
        
        # Add column information
        if data:
            columns = list(data[0].keys())
            summary.append(f"\nColumns: {', '.join(columns[:10])}")
            if len(columns) > 10:
                summary.append(f"... and {len(columns) - 10} more")
        
        return "\n".join(summary)


# =========================================================================
# MAIN INTERFACE
# =========================================================================

def create_sql_agent(db_path: str = None) -> FlightDataSQLAgent:
    """Factory function to create SQL agent instance"""
    return FlightDataSQLAgent(db_path)

# For backward compatibility
class SQLGenerator:
    """Legacy interface wrapper"""
    
    def __init__(self):
        self.agent = create_sql_agent()
    
    def generate_sql(self, natural_query: str, table_schemas: Dict[str, List[Dict]], 
                    context: Optional[str] = None) -> Tuple[str, Dict]:
        """Legacy method for backward compatibility"""
        
        # Use session_id from context or generate default
        session_id = "legacy_session"
        
        result = self.agent.process_query(natural_query, session_id, table_schemas)
        
        if result["success"]:
            return result["metadata"]["sql_query"], result["metadata"]
        else:
            return "", {"error": result.get("answer", "Unknown error")}