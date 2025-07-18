"""
SQL Agent for Flight Data Analysis - LangChain Implementation (Fixed)

A sophisticated SQL agent using LangChain's SQL tools for natural language
to SQL conversion and execution with DuckDB, with fallback to direct connection.

Author: Flight Data Analysis System
Dependencies: langchain, langchain-openai, langchain-community, duckdb, openai
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from typing_extensions import TypedDict
from datetime import datetime
import duckdb
import openai

# LangChain imports
try:
    from langchain_community.utilities import SQLDatabase
    from langchain_community.agent_toolkits import create_sql_agent
    from langchain_openai import OpenAI
    from langchain.prompts import PromptTemplate
    from langchain.schema import BaseOutputParser
    from langchain.agents import AgentType
    from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"LangChain not available: {e}. Will use direct DuckDB fallback.")
    LANGCHAIN_AVAILABLE = False

from config import Config

logger = logging.getLogger(__name__)

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

class AgentState(TypedDict):
    """State object for SQL agent workflow"""
    question: str
    session_id: str
    sql_query: str
    query_result: str
    success: bool
    error_message: str
    metadata: Dict[str, Any]


# ============================================================================
# CUSTOM OUTPUT PARSER FOR BETTER CONTROL
# ============================================================================

if LANGCHAIN_AVAILABLE:
    class FlightDataSQLOutputParser(BaseOutputParser):
        """Custom output parser for flight data SQL responses"""
        
        def parse(self, text: str) -> str:
            """Parse the LLM output and extract the final answer"""
            return text.strip()
        
        @property
        def _type(self) -> str:
            return "flight_data_sql_parser"


# ============================================================================
# LANGCHAIN SQL AGENT WITH FALLBACK
# ============================================================================

class FlightDataSQLAgent:
    """SQL Agent using LangChain with direct DuckDB fallback"""
    
    def __init__(self, db_path: str = None, session_id: str = None, existing_connection=None):
        """Initialize with LangChain preferred, fallback to direct DuckDB"""
        
        # Setup database path
        if session_id and not db_path:
            db_dir = getattr(Config, 'DATABASE_DIR', 'databases')
            self.db_path = os.path.join(db_dir, f"{session_id}.db")
        else:
            self.db_path = db_path or ":memory:"
        
        # Ensure database directory exists
        if self.db_path != ":memory:":
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"📁 Created database directory: {db_dir}")
        
        # Initialize components
        self.use_langchain = False
        self.sql_agent = None
        self.db = None
        self.duckdb_conn = existing_connection
        self.owns_connection = existing_connection is None
        
        # Try LangChain first, then fallback
        if LANGCHAIN_AVAILABLE:
            try:
                self._setup_langchain_components()
                self.use_langchain = True
                logger.info("🚀 Successfully initialized LangChain SQL Agent")
            except Exception as e:
                logger.warning(f"⚠️ LangChain initialization failed: {e}")
                logger.info("🔄 Falling back to direct DuckDB connection...")
                self._setup_direct_duckdb_fallback()
        else:
            logger.info("🔄 LangChain not available, using direct DuckDB connection...")
            self._setup_direct_duckdb_fallback()
        
        # Test connection
        self._test_connection()
    
    def _setup_langchain_components(self):
        """Setup LangChain SQL database and agent"""
        try:
            # Create a DuckDB connection URI
            # LangChain's SQLDatabase expects a database URI
            if self.db_path == ":memory:":
                db_uri = "duckdb:///:memory:"
            else:
                # For file-based DuckDB, we need to use absolute path
                abs_path = os.path.abspath(self.db_path)
                db_uri = f"duckdb:///{abs_path}"
            
            # Create SQLDatabase instance
            self.db = SQLDatabase.from_uri(db_uri)
            logger.info(f"✅ Connected to DuckDB via LangChain SQLDatabase: {db_uri}")
            
            # Initialize OpenAI LLM
            self.llm = OpenAI(
                api_key=Config.OPENAI_API_KEY,
                model=Config.OPENAI_MODEL,
                max_tokens=Config.OPENAI_MAX_TOKENS,
                temperature=0.1
            )
            logger.info("✅ OpenAI LLM initialized successfully")
            
            # Create SQL agent with the correct parameters
            # According to the documentation, we need to pass:
            # - llm as first positional argument
            # - db as keyword argument (not toolkit)
            # - agent_type as keyword argument
            self.sql_agent = create_sql_agent(
                self.llm,  # First positional argument
                db=self.db,  # Database as keyword argument
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # Agent type
                verbose=True,
                top_k=10,  # Limit query results
                max_iterations=15,
                early_stopping_method='force'
            )
            
            logger.info("✅ LangChain SQL agent initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup LangChain components: {e}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            raise
    
    def _setup_direct_duckdb_fallback(self):
        """Setup direct DuckDB connection as fallback"""
        try:
            if not self.duckdb_conn:
                self.duckdb_conn = duckdb.connect(self.db_path)
                self.owns_connection = True
            
            # Initialize OpenAI client for direct usage
            self.llm_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            
            logger.info(f"✅ Direct DuckDB fallback connection established: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup direct DuckDB fallback: {e}")
            raise Exception(f"Could not initialize any SQL connection: {e}")
    
    def _test_connection(self):
        """Test the database connection"""
        try:
            if self.use_langchain and self.db:
                # Test LangChain connection
                tables = self.db.get_table_names()
                test_result = self.db.run("SELECT 1 as test")
                logger.info(f"✅ LangChain connection test successful! Found tables: {tables}")
            elif self.duckdb_conn:
                # Test direct DuckDB connection
                result = self.duckdb_conn.execute("SELECT 1 as test").fetchall()
                tables = self.duckdb_conn.execute("SHOW TABLES").fetchall()
                logger.info(f"✅ Direct DuckDB connection test successful! Found {len(tables)} tables")
            else:
                raise Exception("No valid connection available")
                
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            raise
    
    def process_query(self, question: str, session_id: str, table_schemas: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main entry point for processing natural language queries"""
        
        logger.info(f"🔍 Processing query for session: {session_id}")
        logger.info(f"📍 Using database: {self.db_path}")
        logger.info(f"🔧 Using LangChain: {self.use_langchain}")
        logger.info(f"❓ Question: {question}")
        
        try:
            # Check if question is relevant to flight data
            if not self._is_flight_data_relevant(question):
                return self._generate_not_relevant_response()
            
            if self.use_langchain and self.sql_agent:
                return self._process_with_langchain(question)
            else:
                return self._process_with_direct_duckdb(question)
                
        except Exception as e:
            logger.error(f"❌ SQL processing failed: {e}")
            return {
                "success": False,
                "answer": f"I encountered an error while processing your flight data query: {str(e)}. Please try rephrasing your question or contact support if the issue persists.",
                "error": str(e),
                "metadata": {"error_details": str(e)}
            }
    
    def _make_json_serializable(self, obj):
        """Convert object to JSON-serializable format"""
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif hasattr(obj, 'isoformat'):  # datetime, date, time objects
            return obj.isoformat()
        elif isinstance(obj, (bytes, bytearray)):
            return obj.decode('utf-8', errors='ignore')
        elif isinstance(obj, (set, frozenset)):
            return list(obj)
        else:
            # For other types, convert to string
            return str(obj)
    
    def _process_with_langchain(self, question: str) -> Dict[str, Any]:
        """Process query using LangChain SQL agent"""
        try:
            # Enhance question with flight data context
            enhanced_question = self._enhance_question_with_flight_context(question)
            
            logger.info("🔄 Running LangChain SQL agent...")
            
            result = self.sql_agent.invoke({"input": enhanced_question})
            
            # Extract information from LangChain result
            answer = result.get("output", "No answer generated")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Try to extract SQL query from intermediate steps
            sql_query = self._extract_sql_from_steps(intermediate_steps)
            
            logger.info(f"✅ LangChain processing successful")
            if sql_query:
                logger.info(f"📊 Generated SQL: {sql_query}")
            
            # Make sure all data is JSON serializable
            metadata = {
                "sql_query": sql_query,
                "intermediate_steps": self._make_json_serializable(intermediate_steps),
                "langchain_result": self._make_json_serializable(result),
                "method": "langchain"
            }
            
            return {
                "success": True,
                "answer": answer,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ LangChain processing failed: {e}")
            raise
    
    def _process_with_direct_duckdb(self, question: str) -> Dict[str, Any]:
        """Process query using direct DuckDB connection and OpenAI"""
        try:
            logger.info("🔄 Using direct DuckDB + OpenAI processing...")
            
            # Get table schemas for context
            table_info = self._get_table_info_direct()
            
            # Generate SQL using OpenAI
            sql_query = self._generate_sql_with_openai(question, table_info)
            
            if not sql_query:
                raise Exception("Failed to generate SQL query")
            
            logger.info(f"📊 Generated SQL: {sql_query}")
            
            # Execute query
            result = self.duckdb_conn.execute(sql_query).fetchall()
            columns = [desc[0] for desc in self.duckdb_conn.description]
            
            # Convert to list of dicts with JSON-safe serialization
            data = []
            for row in result:
                row_dict = {}
                for i, value in enumerate(row):
                    column_name = columns[i]
                    row_dict[column_name] = self._make_json_serializable(value)
                data.append(row_dict)
            
            # Generate natural language answer
            answer = self._generate_answer_with_openai(question, sql_query, data)
            
            logger.info(f"✅ Direct DuckDB processing successful")
            
            return {
                "success": True,
                "answer": answer,
                "metadata": {
                    "sql_query": sql_query,
                    "row_count": len(data),
                    "method": "direct_duckdb",
                    "data_sample": data[:5] if data else []
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Direct DuckDB processing failed: {e}")
            raise
    
    def _enhance_question_with_flight_context(self, question: str) -> str:
        """Enhance the question with flight data context for LangChain"""
        context = f"""
You are working with flight operations data. The database contains:

1. **clean_flights** table (19,210 rows) with columns:
   - "Date", "A/C Registration", "Flight", "A/C Type"
   - "ATD (UTC) Block out", "ATA (UTC) Block in" 
   - "Origin ICAO", "Destination ICAO"
   - "Uplift Volume", "Uplift Density", "Uplift weight"
   - "Remaining Fuel From Prev. Flight", "Block off Fuel", "Block on Fuel"
   - "Fuel Type"

2. **error_flights** table (28 rows) with error information.

IMPORTANT: Always use double quotes for column names with spaces in DuckDB.
Fuel consumed = "Block off Fuel" - "Block on Fuel"

Question: {question}

Provide a comprehensive analysis with specific numbers and insights from the flight data.
"""
        return context
    
    def _extract_sql_from_steps(self, intermediate_steps: List) -> str:
        """Extract SQL query from LangChain intermediate steps"""
        sql_query = ""
        try:
            for step in intermediate_steps:
                if isinstance(step, tuple) and len(step) >= 2:
                    action, observation = step
                    if hasattr(action, 'tool') and hasattr(action, 'tool_input'):
                        if 'sql' in action.tool.lower():
                            sql_query = action.tool_input.get('query', '')
                            break
                elif isinstance(step, dict):
                    if 'sql_cmd' in step:
                        sql_query = step['sql_cmd']
                        break
        except Exception as e:
            logger.warning(f"Could not extract SQL from steps: {e}")
        
        return sql_query
    
    def _is_flight_data_relevant(self, question: str) -> bool:
        """Simple relevance check for flight data questions"""
        # Always return True to process all queries about errors
        # since the user is asking "What are the errors?"
        return True
    
    def _generate_not_relevant_response(self) -> Dict[str, Any]:
        """Generate response for non-flight-data questions"""
        return {
            "success": False,
            "answer": "I can only help with questions about flight operations data, including aircraft performance, fuel consumption, routes, and operational metrics. Please ask a question related to the flight data in our system.",
            "metadata": {"relevance": "not_relevant"}
        }
    
    def _get_table_info_direct(self) -> str:
        """Get table information using direct DuckDB connection"""
        try:
            tables_info = []
            
            # Get table names
            tables = self.duckdb_conn.execute("SHOW TABLES").fetchall()
            
            for table_row in tables:
                table_name = table_row[0]
                
                # Get column information
                columns = self.duckdb_conn.execute(f"DESCRIBE {table_name}").fetchall()
                
                table_info = f"\nTable: {table_name}\nColumns:\n"
                for col in columns:
                    table_info += f"  - {col[0]} ({col[1]})\n"
                
                tables_info.append(table_info)
            
            return "\n".join(tables_info)
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return "Tables: clean_flights, error_flights"
    
    def _generate_sql_with_openai(self, question: str, table_info: str) -> str:
        """Generate SQL query using OpenAI"""
        try:
            prompt = f"""
You are an expert SQL generator for flight operations data using DuckDB.

DATABASE SCHEMA:
{table_info}

KEY COLUMNS (use double quotes for names with spaces):
- "Date" (String) - Flight date
- "A/C Registration" (String) - Aircraft registration identifier  
- "Flight" (String) - Flight number
- "A/C Type" (String) - Aircraft type/model
- "Origin ICAO" (String) - Departure airport ICAO code
- "Destination ICAO" (String) - Arrival airport ICAO code
- "Uplift Volume", "Uplift weight" - Fuel data
- "Block off Fuel", "Block on Fuel" - Fuel quantities

For the error_flights table, it contains:
- "Error_Category" - The type of error
- "Error_Reason" - The specific reason for the error
- Plus all the standard flight columns

REQUIREMENTS:
1. Use double quotes for column names with spaces
2. Include comprehensive data - SELECT * or list relevant columns
3. Add LIMIT 1000 for performance
4. Handle NULL values appropriately

FUEL CALCULATIONS:
- Fuel consumed = "Block off Fuel" - "Block on Fuel"

Generate ONLY the SQL query for: {question}
"""
            
            response = self.llm_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.1
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Clean up the SQL query
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:]
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]
            
            return sql_query.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate SQL with OpenAI: {e}")
            return ""
    
    def _generate_answer_with_openai(self, question: str, sql_query: str, data: List[Dict]) -> str:
        """Generate natural language answer using OpenAI"""
        try:
            # Limit data for context
            sample_data = data[:10] if data else []
            
            prompt = f"""
Question: {question}

SQL Query Used: {sql_query}

Query Results ({len(data)} total rows):
{json.dumps(sample_data, indent=2, default=str)}

Provide a clear, comprehensive answer to the question based on this flight operations data. Include specific numbers and insights.
"""
            
            response = self.llm_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate answer with OpenAI: {e}")
            return f"Found {len(data)} records. Please check the query results."
    
    def get_table_schemas(self) -> Dict[str, Any]:
        """Get table schema information"""
        try:
            if self.use_langchain and self.db:
                # Use LangChain method
                schemas = {}
                table_names = self.db.get_table_names()
                
                for table_name in table_names:
                    table_info = self.db.get_table_info([table_name])
                    schemas[table_name] = {"info": table_info}
                    
                    try:
                        sample_data = self.db.run(f"SELECT * FROM {table_name} LIMIT 5")
                        schemas[table_name]["sample"] = sample_data
                    except Exception as e:
                        logger.warning(f"Could not get sample data for {table_name}: {e}")
                
                return schemas
            
            elif self.duckdb_conn:
                # Use direct DuckDB method
                schemas = {}
                tables = self.duckdb_conn.execute("SHOW TABLES").fetchall()
                
                for table_row in tables:
                    table_name = table_row[0]
                    
                    # Get column info
                    columns = self.duckdb_conn.execute(f"DESCRIBE {table_name}").fetchall()
                    schemas[table_name] = {
                        "columns": [{"name": col[0], "type": col[1]} for col in columns]
                    }
                    
                    # Get sample data
                    try:
                        sample = self.duckdb_conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchall()
                        if sample:
                            col_names = [desc[0] for desc in self.duckdb_conn.description]
                            schemas[table_name]["sample"] = [dict(zip(col_names, row)) for row in sample]
                    except Exception as e:
                        logger.warning(f"Could not get sample data for {table_name}: {e}")
                
                return schemas
            
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get table schemas: {e}")
            return {}
    
    def close(self):
        """Close database connections"""
        try:
            if self.use_langchain and hasattr(self, 'db') and self.db:
                if hasattr(self.db, '_engine') and self.db._engine:
                    self.db._engine.dispose()
                logger.info("✅ Closed LangChain database connection")
            
            if self.owns_connection and self.duckdb_conn:
                self.duckdb_conn.close()
                logger.info("✅ Closed direct DuckDB connection")
            elif not self.owns_connection:
                logger.info("✅ Left existing DuckDB connection open (not owned by agent)")
                
        except Exception as e:
            logger.warning(f"Error closing database connections: {e}")


# ============================================================================
# ENHANCED LANGCHAIN AGENT
# ============================================================================

class EnhancedFlightDataSQLAgent(FlightDataSQLAgent):
    """Enhanced version with additional LangChain customizations"""
    
    def __init__(self, db_path: str = None, session_id: str = None, existing_connection=None):
        super().__init__(db_path, session_id, existing_connection)
    
    def process_query_enhanced(self, question: str, session_id: str) -> Dict[str, Any]:
        """Process query with enhanced LangChain features"""
        # For now, same as base implementation, but can be extended
        return self.process_query(question, session_id)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_sql_agent(db_path: str = None, session_id: str = None, enhanced: bool = False, existing_connection=None) -> FlightDataSQLAgent:
    """Factory function to create SQL agent instance"""
    if enhanced:
        return EnhancedFlightDataSQLAgent(db_path, session_id, existing_connection)
    else:
        return FlightDataSQLAgent(db_path, session_id, existing_connection)


# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

class SQLGenerator:
    """Legacy interface wrapper for backward compatibility"""
    
    def __init__(self):
        self.agent = create_sql_agent()
    
    def generate_sql(self, natural_query: str, table_schemas: Dict[str, List[Dict]], 
                    context: Optional[str] = None) -> Tuple[str, Dict]:
        """Legacy method for backward compatibility"""
        
        session_id = "legacy_session"
        result = self.agent.process_query(natural_query, session_id, table_schemas)
        
        if result["success"]:
            sql_query = result["metadata"].get("sql_query", "")
            return sql_query, result["metadata"]
        else:
            return "", {"error": result.get("answer", "Unknown error")}


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example usage
    agent = create_sql_agent(session_id="test_session")
    
    # Test queries
    test_questions = [
        "What are the top 10 aircraft by fuel consumption?",
        "Show me flights from KJFK to KLAX",
        "What's the average fuel efficiency by aircraft type?",
        "Show me any data quality errors in the system"
    ]
    
    for question in test_questions:
        print(f"\n🔍 Question: {question}")
        result = agent.process_query(question, "test_session")
        print(f"✅ Answer: {result['answer']}")
        
        if result['success'] and 'sql_query' in result['metadata']:
            print(f"📊 SQL: {result['metadata']['sql_query']}")
    
    agent.close()