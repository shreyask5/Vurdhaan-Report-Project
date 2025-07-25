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
    
    def __init__(self, db_path: str = None, session_id: str = None):
        # If session_id is provided, construct the database path
        if session_id and not db_path:
            db_dir = getattr(Config, 'DATABASE_DIR', 'databases')
            self.db_path = os.path.join(db_dir, f"{session_id}.db")
        else:
            self.db_path = db_path or ":memory:"
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Connect to local DuckDB database"""
        try:
            # Ensure the database directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"📁 Created database directory: {db_dir}")
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"🔗 Connected to local DuckDB: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to local DuckDB: {e}")
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
        """Get schema information for all tables with min/max values"""
        try:
            # Get list of tables
            tables_data, error = self.execute_query("SHOW TABLES")
            if error:
                return {}
            
            schemas = {}
            for table_row in tables_data:
                table_name = table_row.get('name', list(table_row.values())[0])
                
                # Get basic schema for this table
                schema_data, error = self.execute_query(f"DESCRIBE {table_name}")
                if error or not schema_data:
                    continue
                
                # Enhance schema with min/max values and statistics
                enhanced_schema = []
                for column_info in schema_data:
                    column_name = column_info.get('column_name', column_info.get('name', 'unknown'))
                    column_type = column_info.get('column_type', column_info.get('type', 'unknown'))
                    
                    # Create enhanced column info
                    enhanced_column = {
                        'column_name': column_name,
                        'data_type': column_type,
                        'nullable': column_info.get('nullable'),
                        'default': column_info.get('default'),
                        'extra': column_info.get('extra')
                    }
                    
                    # Get min/max and statistics for appropriate data types
                    stats = self._get_column_statistics(table_name, column_name, column_type)
                    enhanced_column.update(stats)
                    
                    enhanced_schema.append(enhanced_column)
                
                schemas[table_name] = enhanced_schema
            
            return schemas
            
        except Exception as e:
            logger.error(f"Failed to get table schemas: {e}")
            return {}

    def _get_column_statistics(self, table_name: str, column_name: str, column_type: str) -> Dict[str, Any]:
        """Get statistics (min/max, count, etc.) for a specific column"""
        stats = {
            'min_value': None,
            'max_value': None,
            'null_count': None,
            'distinct_count': None,
            'sample_values': []
        }
        
        try:
            # Escape column name with double quotes for DuckDB
            escaped_column = f'"{column_name}"'
            
            # Determine if column is numeric, date, or text
            is_numeric = any(t in column_type.upper() for t in ['INT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC', 'REAL', 'BIGINT'])
            is_date = any(t in column_type.upper() for t in ['DATE', 'TIME', 'TIMESTAMP'])
            is_text = any(t in column_type.upper() for t in ['VARCHAR', 'TEXT', 'STRING', 'CHAR'])
            
            # Get basic statistics
            basic_stats_query = f"""
            SELECT 
                COUNT(*) as total_count,
                COUNT({escaped_column}) as non_null_count,
                COUNT(*) - COUNT({escaped_column}) as null_count,
                COUNT(DISTINCT {escaped_column}) as distinct_count
            FROM {table_name}
            """
            
            basic_stats, error = self.execute_query(basic_stats_query)
            if not error and basic_stats:
                stats_row = basic_stats[0]
                stats['total_count'] = stats_row.get('total_count', 0)
                stats['non_null_count'] = stats_row.get('non_null_count', 0)
                stats['null_count'] = stats_row.get('null_count', 0)
                stats['distinct_count'] = stats_row.get('distinct_count', 0)
            
            # Get min/max based on data type
            if is_numeric or is_date:
                minmax_query = f"""
                SELECT 
                    MIN({escaped_column}) as min_value,
                    MAX({escaped_column}) as max_value
                FROM {table_name}
                WHERE {escaped_column} IS NOT NULL
                """
                
                minmax_data, error = self.execute_query(minmax_query)
                if not error and minmax_data:
                    stats['min_value'] = minmax_data[0].get('min_value')
                    stats['max_value'] = minmax_data[0].get('max_value')
            
            elif is_text:
                # For text columns, get min/max by length and alphabetical order
                text_stats_query = f"""
                SELECT 
                    MIN(LENGTH({escaped_column})) as min_length,
                    MAX(LENGTH({escaped_column})) as max_length,
                    MIN({escaped_column}) as min_alphabetical,
                    MAX({escaped_column}) as max_alphabetical
                FROM {table_name}
                WHERE {escaped_column} IS NOT NULL AND {escaped_column} != ''
                """
                
                text_stats, error = self.execute_query(text_stats_query)
                if not error and text_stats:
                    stats['min_length'] = text_stats[0].get('min_length')
                    stats['max_length'] = text_stats[0].get('max_length')
                    stats['min_value'] = text_stats[0].get('min_alphabetical')
                    stats['max_value'] = text_stats[0].get('max_alphabetical')
            
            # Get sample values for better context
            sample_query = f"""
            SELECT DISTINCT {escaped_column}
            FROM {table_name}
            WHERE {escaped_column} IS NOT NULL
            ORDER BY {escaped_column}
            LIMIT 5
            """
            
            sample_data, error = self.execute_query(sample_query)
            if not error and sample_data:
                stats['sample_values'] = [row[column_name] for row in sample_data]
            
            # For categorical data, get top values
            if is_text and stats.get('distinct_count', 0) < 50:  # Only for columns with reasonable number of distinct values
                top_values_query = f"""
                SELECT {escaped_column}, COUNT(*) as frequency
                FROM {table_name}
                WHERE {escaped_column} IS NOT NULL
                GROUP BY {escaped_column}
                ORDER BY frequency DESC
                LIMIT 10
                """
                
                top_values, error = self.execute_query(top_values_query)
                if not error and top_values:
                    stats['top_values'] = [
                        {'value': row[column_name], 'frequency': row['frequency']} 
                        for row in top_values
                    ]
            
            logger.debug(f"📊 Got statistics for {table_name}.{column_name}: {stats}")
            
        except Exception as e:
            logger.warning(f"Failed to get statistics for {table_name}.{column_name}: {e}")
        
        return stats
    
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
    
    def __init__(self, db_path: str = None, session_id: str = None):
        # Initialize the client with session-specific database
        self.client = DuckDBLocalClient(db_path, session_id)
        
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
        logger.info(f"📍 Database path: {self.client.db_path}")
        is_connected, connection_msg = self.client.test_connection()
        if is_connected:
            logger.info(f"✅ Local DuckDB connection successful: {connection_msg}")
        else:
            logger.error(f"❌ Local DuckDB connection failed: {connection_msg}")
        
    def process_query(self, question: str, session_id: str, table_schemas: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for processing natural language queries"""
        
        # Log the session and database info
        logger.info(f"🔍 Processing query for session: {session_id}")
        logger.info(f"📍 Using database: {self.client.db_path}")
        
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

AVAILABLE TABLES:
1. clean_flights - Main flight operations data
2. error_flights - Data quality issues and errors

COLUMN REFERENCE:
Common Columns (both tables):
- "Date" (String) - Flight date
- "A/C Registration" (String) - Aircraft registration identifier
- "Flight" (String) - Flight number
- "A/C Type" (String) - Aircraft type/model
- "ATD (UTC) Block out" (String) - Actual Time Departure (Block Out)
- "ATA (UTC) Block in" (String) - Actual Time Arrival (Block In)
- "Origin ICAO" (String) - Departure airport ICAO code
- "Destination ICAO" (String) - Arrival airport ICAO code
- "Uplift Volume" (Integer/Float) - Fuel volume uplifted
- "Uplift Density" (Float) - Fuel density
- "Uplift weight" (Float) - Weight of fuel uplifted
- "Remaining Fuel From Prev. Flight" (Integer/Float) - Remaining fuel from previous flight
- "Block off Fuel" (Float) - Fuel quantity at block off
- "Block on Fuel" (Integer/Float) - Fuel quantity at block on
- "Fuel Type" (String) - Type of fuel used

Error-specific columns (error_flights only):
- "Error_Category" (String) - Type of error encountered
- "Error_Reason" (String) - Detailed error description
- "Row_Index" (Integer) - Original row number with error
- "Affected_Columns" (String) - Columns affected by error
- "Cell_Data" (String) - Original cell data that caused error

CRITICAL QUERY REQUIREMENTS:
1. **ALWAYS SELECT ALL COLUMNS**: Use SELECT * or explicitly list ALL columns for complete row data
2. **PROVIDE COMPLETE ROW CONTEXT**: Include all available columns to give full context for each record
3. **NEVER use SELECT column_name only**: Always include the complete row information
4. **When aggregating**: Still include key identifying columns and use GROUP BY appropriately

MANDATORY COLUMN SELECTION PATTERNS:
✅ CORRECT: SELECT * FROM clean_flights WHERE...
✅ CORRECT: SELECT "Date", "A/C Registration", "Flight", "A/C Type", "ATD (UTC) Block out", "ATA (UTC) Block in", "Origin ICAO", "Destination ICAO", "Uplift Volume", "Uplift Density", "Uplift weight", "Remaining Fuel From Prev. Flight", "Block off Fuel", "Block on Fuel", "Fuel Type" FROM clean_flights WHERE...
❌ INCORRECT: SELECT "A/C Registration" FROM clean_flights
❌ INCORRECT: SELECT "Flight", "Origin ICAO" FROM clean_flights

FOR AGGREGATIONS WITH COMPLETE DATA:
- When grouping, include representative complete rows using window functions
- Use ROW_NUMBER() or FIRST() to get complete sample rows within groups
- Always provide full context even in summary queries

DuckDB-Specific Guidelines:
1. Use double quotes for column names with spaces: "A/C Registration"
2. Date functions: strptime() for parsing, date_trunc() for grouping
3. String functions: regexp_matches() for pattern matching
4. Use LIMIT for large datasets (recommend LIMIT 1000 for initial queries)
5. Handle NULL values with COALESCE() or IS NOT NULL
6. For time calculations, convert string times to timestamps first

QUERY PATTERNS WITH COMPLETE ROW DATA:
Flight Operations:
- Aircraft performance: SELECT *, calculated_metrics FROM table GROUP BY aircraft_id
- Route analysis: SELECT *, route_metrics FROM table GROUP BY route
- Fuel efficiency: SELECT *, ("Block off Fuel" - "Block on Fuel") as fuel_consumed FROM table

Data Quality:
- Check error_flights: SELECT * FROM error_flights WHERE "Error_Category" = '...'
- Join with complete data: SELECT cf.*, ef.* FROM clean_flights cf JOIN error_flights ef ON ...

FUEL CALCULATIONS WITH COMPLETE DATA:
- Fuel consumed = "Block off Fuel" - "Block on Fuel"
- Total fuel on board = "Remaining Fuel From Prev. Flight" + "Uplift weight"
- Fuel efficiency = Fuel consumed / Flight time

EXAMPLE QUERIES WITH COMPLETE ROW DATA:
1. Top fuel consuming aircraft with complete flight details:
   ```sql
   SELECT *, 
          ("Block off Fuel" - "Block on Fuel") as fuel_consumed
   FROM clean_flights 
   WHERE ("Block off Fuel" - "Block on Fuel") IS NOT NULL
   ORDER BY fuel_consumed DESC
   LIMIT 100
   ```

2. Route analysis with complete flight information:
   ```sql
   SELECT *,
          ("Block off Fuel" - "Block on Fuel") as fuel_consumed,
          "Uplift weight" as fuel_uplifted
   FROM clean_flights
   WHERE "Origin ICAO" IS NOT NULL AND "Destination ICAO" IS NOT NULL
   ORDER BY "Date", "ATD (UTC) Block out"
   LIMIT 500
   ```

3. Error investigation with complete context:
   ```sql
   SELECT ef.*,
          cf.*
   FROM error_flights ef
   LEFT JOIN clean_flights cf ON (
       ef."A/C Registration" = cf."A/C Registration" AND 
       ef."Flight" = cf."Flight" AND 
       ef."Date" = cf."Date"
   )
   ORDER BY ef."Error_Category", ef."Row_Index"
   ```

4. Aircraft performance with full operational context:
   ```sql
   WITH fuel_analysis AS (
       SELECT *,
              ("Block off Fuel" - "Block on Fuel") as fuel_consumed,
              ("Remaining Fuel From Prev. Flight" + "Uplift weight") as total_fuel_available
       FROM clean_flights
       WHERE "Block off Fuel" IS NOT NULL AND "Block on Fuel" IS NOT NULL
   )
   SELECT *
   FROM fuel_analysis
   WHERE fuel_consumed > 0
   ORDER BY fuel_consumed DESC
   LIMIT 200
   ```

5. Time-based analysis with complete flight records:
   ```sql
   SELECT *,
          strptime("ATD (UTC) Block out", '%H:%M') as departure_time,
          strptime("ATA (UTC) Block in", '%H:%M') as arrival_time
   FROM clean_flights
   WHERE "ATD (UTC) Block out" IS NOT NULL 
     AND "ATA (UTC) Block in" IS NOT NULL
   ORDER BY "Date", departure_time
   LIMIT 300
   ```

SUMMARY QUERIES WITH SAMPLE COMPLETE ROWS:
When user asks for summaries, provide both aggregated data AND sample complete rows:

```sql
-- Example: Aircraft summary with sample complete rows
WITH aircraft_summary AS (
    SELECT "A/C Registration",
           COUNT(*) as flight_count,
           AVG("Block off Fuel" - "Block on Fuel") as avg_fuel_consumption,
           MIN("Date") as first_flight_date,
           MAX("Date") as last_flight_date
    FROM clean_flights
    GROUP BY "A/C Registration"
),
sample_flights AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY "A/C Registration" ORDER BY "Date" DESC) as rn
    FROM clean_flights
)
SELECT s.*, 
       a.flight_count,
       a.avg_fuel_consumption,
       a.first_flight_date,
       a.last_flight_date
FROM sample_flights s
JOIN aircraft_summary a ON s."A/C Registration" = a."A/C Registration"
WHERE s.rn = 1  -- Most recent flight per aircraft
ORDER BY a.avg_fuel_consumption DESC
```

REMEMBER: The goal is to always provide complete, comprehensive row data that gives full operational context for every query, enabling thorough analysis and understanding of the flight operations.

Generate efficient, accurate DuckDB SQL queries that ALWAYS return complete row information."""


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
        """Build detailed schema context with statistics for SQL generation"""
        context = []
        
        for table_name, schema in schemas.items():
            context.append(f"\n📊 Table: {table_name}")
            
            if isinstance(schema, list):
                for col in schema[:15]:  # Limit columns to prevent context overflow
                    col_name = col.get('column_name', 'unknown')
                    col_type = col.get('data_type', 'unknown')
                    
                    # Build column description with statistics
                    col_desc = f"  - {col_name} ({col_type})"
                    
                    # Add min/max if available
                    if col.get('min_value') is not None and col.get('max_value') is not None:
                        min_val = col['min_value']
                        max_val = col['max_value']
                        
                        # Format values based on type
                        if isinstance(min_val, (int, float)):
                            col_desc += f" [Range: {min_val} to {max_val}]"
                        else:
                            # For strings, show length range if available
                            if col.get('min_length') is not None:
                                col_desc += f" [Length: {col['min_length']}-{col['max_length']} chars]"
                            else:
                                col_desc += f" [Range: '{min_val}' to '{max_val}']"
                    
                    # Add distinct count
                    if col.get('distinct_count') is not None:
                        total_count = col.get('total_count', 0)
                        distinct_count = col['distinct_count']
                        if total_count > 0:
                            uniqueness_pct = round((distinct_count / total_count) * 100, 1)
                            col_desc += f" [{distinct_count} distinct values, {uniqueness_pct}% unique]"
                    
                    # Add null count if significant
                    if col.get('null_count', 0) > 0:
                        null_count = col['null_count']
                        total_count = col.get('total_count', 0)
                        if total_count > 0:
                            null_pct = round((null_count / total_count) * 100, 1)
                            col_desc += f" [{null_pct}% nulls]"
                    
                    # Add sample values for categorical data
                    if col.get('sample_values'):
                        samples = col['sample_values'][:3]  # Show first 3 samples
                        sample_str = "', '".join(str(v) for v in samples)
                        col_desc += f" [Examples: '{sample_str}']"
                    
                    # Add top values for categorical data
                    if col.get('top_values'):
                        top_vals = col['top_values'][:3]  # Show top 3
                        top_str = ", ".join(f"'{v['value']}' ({v['frequency']})" for v in top_vals)
                        col_desc += f" [Top values: {top_str}]"
                    
                    context.append(col_desc)
                
                if len(schema) > 15:
                    context.append(f"  ... and {len(schema) - 15} more columns")
        
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

def create_sql_agent(db_path: str = None, session_id: str = None) -> FlightDataSQLAgent:
    """Factory function to create SQL agent instance"""
    return FlightDataSQLAgent(db_path, session_id)

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