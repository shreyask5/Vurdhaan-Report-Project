"""
SQL Agent for Flight Data Analysis - LangChain Implementation

A simplified SQL agent using LangChain's SQLDatabaseChain for natural language
to SQL conversion and execution with DuckDB.

Author: Flight Data Analysis System
Dependencies: langchain, langchain-openai, duckdb, openai
"""

import os
import logging
from typing import Dict, List, Tuple, Optional, Any
from typing_extensions import TypedDict
from datetime import datetime
import duckdb

# LangChain imports
from langchain.sql_database import SQLDatabase
from langchain.chains import SQLDatabaseChain
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser

from config import Config

logger = logging.getLogger(__name__)

# ============================================================================
# STATE MANAGEMENT (Simplified)
# ============================================================================

class AgentState(TypedDict):
    """Simplified state object for LangChain SQL agent"""
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

class FlightDataSQLOutputParser(BaseOutputParser):
    """Custom output parser for flight data SQL responses"""
    
    def parse(self, text: str) -> str:
        """Parse the LLM output and extract the final answer"""
        # LangChain SQLDatabaseChain returns formatted text
        # We can customize this if needed
        return text.strip()
    
    @property
    def _type(self) -> str:
        return "flight_data_sql_parser"


# ============================================================================
# LANGCHAIN SQL AGENT IMPLEMENTATION
# ============================================================================

class FlightDataSQLAgent:
    """Simplified SQL Agent using LangChain's SQLDatabaseChain"""
    
    def __init__(self, db_path: str = None, session_id: str = None):
        """Initialize the LangChain-based SQL agent"""
        
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
        
        # Initialize LangChain components
        self._setup_langchain_components()
        
        # Test connection
        logger.info("🚀 Initializing LangChain SQL Agent...")
        self._test_connection()
    
    def _setup_langchain_components(self):
        """Setup LangChain SQL database and chain"""
        try:
            # Create SQLDatabase instance for DuckDB
            self.db = SQLDatabase.from_uri(f"duckdb:///{self.db_path}")
            logger.info(f"✅ Connected to DuckDB via LangChain: {self.db_path}")
            
            # Initialize OpenAI LLM
            self.llm = OpenAI(
                api_key=Config.OPENAI_API_KEY,
                model_name=Config.OPENAI_MODEL,
                max_tokens=Config.OPENAI_MAX_TOKENS,
                temperature=0.1
            )
            logger.info("✅ OpenAI LLM initialized successfully")
            
            # Create custom prompt template for flight data
            self.prompt_template = self._create_flight_data_prompt()
            
            # Initialize SQLDatabaseChain
            self.sql_chain = SQLDatabaseChain.from_llm(
                llm=self.llm,
                db=self.db,
                prompt=self.prompt_template,
                verbose=True,
                return_intermediate_steps=True,
                use_query_checker=True,  # Enable query validation
                return_direct=False,  # Return formatted answer, not just SQL result
                top_k=1000  # Default limit for large result sets
            )
            
            # Set custom output parser if needed
            self.sql_chain.output_parser = FlightDataSQLOutputParser()
            
            logger.info("✅ LangChain SQLDatabaseChain initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup LangChain components: {e}")
            raise Exception(f"Could not initialize LangChain SQL agent: {e}")
    
    def _create_flight_data_prompt(self) -> PromptTemplate:
        """Create a custom prompt template optimized for flight data"""
        
        template = """
You are an expert SQL agent for flight operations data analysis using DuckDB.

Given an input question, create a syntactically correct DuckDB query to run, then look at the results and return the answer.

CRITICAL DATABASE CONTEXT:
You are working with flight operations data containing the following main tables:

1. **clean_flights** (19,210 rows) - Main flight operations data
2. **error_flights** (28 rows) - Data quality issues and errors

KEY COLUMNS (use double quotes for names with spaces):
- "Date" (String) - Flight date
- "A/C Registration" (String) - Aircraft registration identifier  
- "Flight" (String) - Flight number
- "A/C Type" (String) - Aircraft type/model
- "ATD (UTC) Block out" (String) - Actual Time Departure
- "ATA (UTC) Block in" (String) - Actual Time Arrival
- "Origin ICAO" (String) - Departure airport ICAO code
- "Destination ICAO" (String) - Arrival airport ICAO code
- "Uplift Volume" (Integer/Float) - Fuel volume uplifted
- "Uplift Density" (Float) - Fuel density
- "Uplift weight" (Float) - Weight of fuel uplifted
- "Remaining Fuel From Prev. Flight" (Integer/Float) - Remaining fuel
- "Block off Fuel" (Float) - Fuel quantity at departure
- "Block on Fuel" (Integer/Float) - Fuel quantity at arrival
- "Fuel Type" (String) - Type of fuel used

DUCKDB SQL REQUIREMENTS:
1. **Always use double quotes** for column names with spaces: "A/C Registration"
2. **Include comprehensive data** - Use SELECT * or list all relevant columns
3. **Handle NULL values** with IS NOT NULL or COALESCE()
4. **Date functions**: Use strptime() for parsing, date_trunc() for grouping
5. **String functions**: Use regexp_matches() for pattern matching
6. **LIMIT results** to 1000 rows max for performance (add LIMIT 1000)

FUEL CALCULATIONS:
- Fuel consumed = "Block off Fuel" - "Block on Fuel"  
- Total fuel available = "Remaining Fuel From Prev. Flight" + "Uplift weight"

COMMON QUERY PATTERNS:
```sql
-- Aircraft performance with complete data
SELECT *, ("Block off Fuel" - "Block on Fuel") as fuel_consumed 
FROM clean_flights 
WHERE "Block off Fuel" IS NOT NULL AND "Block on Fuel" IS NOT NULL
ORDER BY fuel_consumed DESC LIMIT 500;

-- Route analysis  
SELECT *, strptime("ATD (UTC) Block out", '%H:%M') as departure_time
FROM clean_flights
WHERE "Origin ICAO" IS NOT NULL AND "Destination ICAO" IS NOT NULL  
ORDER BY "Date" LIMIT 1000;

-- Error investigation
SELECT * FROM error_flights 
WHERE "Error_Category" = 'specific_error_type'
ORDER BY "Row_Index" LIMIT 100;
```

RESPONSE GUIDELINES:
1. Start with a direct answer to the question
2. Include specific numbers, aircraft registrations, and metrics
3. Highlight important patterns or anomalies  
4. Explain fuel efficiency or operational insights
5. Suggest follow-up analysis if relevant

Unless the user specifies a different number, limit to top 1000 results.

Only use the following tables:
{table_info}

Question: {input}
"""
        
        return PromptTemplate(
            input_variables=["input", "table_info"],
            template=template
        )
    
    def _test_connection(self):
        """Test the database connection"""
        try:
            # Test basic connectivity using LangChain's database
            tables = self.db.get_table_names()
            logger.info(f"✅ Connection test successful! Found tables: {tables}")
            
            # Test a simple query
            test_result = self.db.run("SELECT 1 as test")
            logger.info(f"✅ Test query successful: {test_result}")
            
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            raise
    
    def process_query(self, question: str, session_id: str, table_schemas: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main entry point for processing natural language queries using LangChain"""
        
        logger.info(f"🔍 Processing query for session: {session_id}")
        logger.info(f"📍 Using database: {self.db_path}")
        logger.info(f"❓ Question: {question}")
        
        # Initialize state
        state = AgentState(
            question=question,
            session_id=session_id,
            sql_query="",
            query_result="",
            success=False,
            error_message="",
            metadata={}
        )
        
        try:
            # Check if question is relevant to flight data
            if not self._is_flight_data_relevant(question):
                return self._generate_not_relevant_response()
            
            # Use LangChain SQLDatabaseChain to process the query
            logger.info("🔄 Running LangChain SQLDatabaseChain...")
            
            result = self.sql_chain.invoke({
                "query": question,
                "table_names_to_use": ["clean_flights", "error_flights"]
            })
            
            # Extract information from LangChain result
            if isinstance(result, dict):
                # LangChain returns intermediate steps when return_intermediate_steps=True
                answer = result.get("result", "")
                intermediate_steps = result.get("intermediate_steps", [])
                
                # Extract SQL query from intermediate steps
                sql_query = ""
                query_result = ""
                
                if intermediate_steps:
                    for step in intermediate_steps:
                        if isinstance(step, dict):
                            if "sql_cmd" in step:
                                sql_query = step["sql_cmd"]
                            if "result" in step:
                                query_result = str(step["result"])
                
                state.update({
                    "sql_query": sql_query,
                    "query_result": query_result,
                    "success": True,
                    "metadata": {
                        "sql_query": sql_query,
                        "intermediate_steps": intermediate_steps,
                        "langchain_result": result
                    }
                })
                
                logger.info(f"✅ LangChain processing successful")
                logger.info(f"📊 Generated SQL: {sql_query}")
                
                return {
                    "success": True,
                    "answer": answer,
                    "metadata": state["metadata"]
                }
            
            else:
                # Simple string result
                return {
                    "success": True,
                    "answer": str(result),
                    "metadata": {"langchain_result": result}
                }
                
        except Exception as e:
            logger.error(f"❌ LangChain SQL processing failed: {e}")
            state["error_message"] = str(e)
            state["success"] = False
            
            return {
                "success": False,
                "answer": f"I encountered an error while processing your flight data query: {str(e)}. Please try rephrasing your question or contact support if the issue persists.",
                "error": str(e),
                "metadata": {"error_details": str(e)}
            }
    
    def _is_flight_data_relevant(self, question: str) -> bool:
        """Simple relevance check for flight data questions"""
        flight_keywords = [
            'aircraft', 'flight', 'fuel', 'airport', 'icao', 'registration',
            'departure', 'arrival', 'block', 'uplift', 'route', 'efficiency',
            'consumption', 'aviation', 'airline', 'a/c', 'atd', 'ata'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in flight_keywords)
    
    def _generate_not_relevant_response(self) -> Dict[str, Any]:
        """Generate response for non-flight-data questions"""
        return {
            "success": False,
            "answer": "I can only help with questions about flight operations data, including aircraft performance, fuel consumption, routes, and operational metrics. Please ask a question related to the flight data in our system.",
            "metadata": {"relevance": "not_relevant"}
        }
    
    def get_table_schemas(self) -> Dict[str, Any]:
        """Get table schema information using LangChain's database"""
        try:
            schemas = {}
            table_names = self.db.get_table_names()
            
            for table_name in table_names:
                # Get table info using LangChain's method
                table_info = self.db.get_table_info([table_name])
                schemas[table_name] = {"info": table_info}
                
                # Get sample data
                try:
                    sample_data = self.db.run(f"SELECT * FROM {table_name} LIMIT 5")
                    schemas[table_name]["sample"] = sample_data
                except Exception as e:
                    logger.warning(f"Could not get sample data for {table_name}: {e}")
            
            return schemas
            
        except Exception as e:
            logger.error(f"Failed to get table schemas: {e}")
            return {}
    
    def close(self):
        """Close database connections"""
        try:
            if hasattr(self, 'db') and self.db:
                # LangChain SQLDatabase doesn't have explicit close method
                # but we can close the underlying connection if accessible
                if hasattr(self.db, '_engine') and self.db._engine:
                    self.db._engine.dispose()
                logger.info("✅ Closed LangChain database connection")
        except Exception as e:
            logger.warning(f"Error closing database connection: {e}")


# ============================================================================
# ENHANCED LANGCHAIN AGENT WITH CUSTOM TOOLS
# ============================================================================

class EnhancedFlightDataSQLAgent(FlightDataSQLAgent):
    """Enhanced version with additional LangChain tools and agents"""
    
    def __init__(self, db_path: str = None, session_id: str = None):
        super().__init__(db_path, session_id)
        self._setup_advanced_chains()
    
    def _setup_advanced_chains(self):
        """Setup additional LangChain chains for enhanced functionality"""
        try:
            from langchain.agents import create_sql_agent
            from langchain.agents.agent_toolkits import SQLDatabaseToolkit
            from langchain.agents import AgentType
            
            # Create SQL toolkit
            toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
            
            # Create SQL agent with tools
            self.sql_agent = create_sql_agent(
                llm=self.llm,
                toolkit=toolkit,
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                max_iterations=3,
                early_stopping_method="generate"
            )
            
            logger.info("✅ Enhanced LangChain SQL agent with tools initialized")
            
        except ImportError as e:
            logger.warning(f"Enhanced features not available: {e}")
            self.sql_agent = None
        except Exception as e:
            logger.error(f"Failed to setup enhanced chains: {e}")
            self.sql_agent = None
    
    def process_query_enhanced(self, question: str, session_id: str) -> Dict[str, Any]:
        """Process query using enhanced agent with tools"""
        
        if not self.sql_agent:
            # Fall back to basic chain
            return self.process_query(question, session_id)
        
        try:
            logger.info("🔄 Running enhanced LangChain SQL agent...")
            
            # Use the agent to process the query
            result = self.sql_agent.invoke({"input": question})
            
            return {
                "success": True,
                "answer": result.get("output", ""),
                "metadata": {
                    "agent_result": result,
                    "enhanced": True
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced agent failed, falling back to basic chain: {e}")
            return self.process_query(question, session_id)


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_sql_agent(db_path: str = None, session_id: str = None, enhanced: bool = False) -> FlightDataSQLAgent:
    """Factory function to create SQL agent instance"""
    if enhanced:
        return EnhancedFlightDataSQLAgent(db_path, session_id)
    else:
        return FlightDataSQLAgent(db_path, session_id)


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