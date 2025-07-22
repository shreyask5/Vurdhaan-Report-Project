# sql_generator.py

"""
SQL Agent for Flight Data Analysis - PostgreSQL Implementation

A sophisticated SQL agent using LangChain's SQL tools and LangGraph for natural language
to SQL conversion and execution with PostgreSQL, with iterative refinement capabilities.

Author: Flight Data Analysis System
Dependencies: langchain, langchain-openai, langchain-community, psycopg2, openai, langgraph
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from typing_extensions import TypedDict
from datetime import datetime
import psycopg2
import openai
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

# LangChain imports
try:
    from langchain_community.utilities import SQLDatabase
    from langchain_community.agent_toolkits import create_sql_agent
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import BaseOutputParser
    from langchain.agents import AgentType
    from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
    from langchain_core.output_parsers import StrOutputParser
    from langgraph.graph import StateGraph, END
    from pydantic import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"LangChain not available: {e}. Will use direct PostgreSQL fallback.")
    LANGCHAIN_AVAILABLE = False

from config import Config
from modules.database import PostgreSQLManager

logger = logging.getLogger(__name__)

# ============================================================================
# STATE MANAGEMENT FOR SQL AGENT
# ============================================================================

class AgentState(TypedDict):
    """State object for SQL agent workflow"""
    question: str
    session_id: str
    sql_query: str
    query_result: Any
    query_rows: List[Dict]
    success: bool
    error_message: str
    attempts: int
    max_attempts: int
    metadata: Dict[str, Any]
    final_answer: str
    sql_error: bool


# ============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# ============================================================================

if LANGCHAIN_AVAILABLE:
    class ConvertToSQL(BaseModel):
        """Model for SQL query generation"""
        sql_query: str = Field(
            description="The SQL query corresponding to the user's natural language question."
        )
    
    class RewrittenQuestion(BaseModel):
        """Model for question rewriting"""
        question: str = Field(
            description="The rewritten question for better SQL generation."
        )


# ============================================================================
# POSTGRESQL SQL AGENT WITH LANGGRAPH
# ============================================================================

class FlightDataPostgreSQLAgent:
    """SQL Agent using LangGraph for PostgreSQL with iterative refinement"""
    
    def __init__(self, db_manager: PostgreSQLManager = None, 
                 session_id: str = None, 
                 max_attempts: int = 3,
                 db_config: Dict[str, str] = None):
        """Initialize SQL Agent with PostgreSQL support"""
        
        self.session_id = session_id or "default_session"
        self.max_attempts = max_attempts
        
        # Initialize database manager
        if db_manager:
            self.db_manager = db_manager
        else:
            self.db_manager = PostgreSQLManager(self.session_id, db_config)
        
        # Get SQLAlchemy engine for LangChain
        self.engine = create_engine(self.db_manager.get_connection_string())
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model=Config.OPENAI_MODEL,
            temperature=0.1,
            max_tokens=min(getattr(Config, 'OPENAI_MAX_TOKENS', 4096), 16384)  # Cap at o4-mini's limit
        )
        
        # Build the workflow
        self._build_workflow()
        
        logger.info(f"🚀 Successfully initialized PostgreSQL SQL Agent for session: {self.session_id}")
    
    def _build_workflow(self):
        """Build the LangGraph workflow for SQL agent"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("convert_to_sql", self._convert_nl_to_sql)
        workflow.add_node("execute_sql", self._execute_sql)
        workflow.add_node("generate_human_readable_answer", self._generate_human_readable_answer)
        workflow.add_node("regenerate_query", self._regenerate_query)
        workflow.add_node("end_max_iterations", self._end_max_iterations)
        
        # Set entry point
        workflow.set_entry_point("convert_to_sql")
        
        # Add edges
        workflow.add_edge("convert_to_sql", "execute_sql")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "execute_sql",
            self._execute_sql_router,
            {
                "generate_answer": "generate_human_readable_answer",
                "regenerate": "regenerate_query",
            }
        )
        
        workflow.add_conditional_edges(
            "regenerate_query",
            self._check_attempts_router,
            {
                "retry": "convert_to_sql",
                "max_iterations": "end_max_iterations",
            }
        )
        
        # End states
        workflow.add_edge("generate_human_readable_answer", END)
        workflow.add_edge("end_max_iterations", END)
        
        # Compile the workflow
        self.app = workflow.compile()
        logger.info("✅ SQL Agent workflow compiled successfully")
    
    def _get_database_schema(self) -> str:
        """Get database schema information"""
        inspector = inspect(self.engine)
        schema = ""
        for table_name in inspector.get_table_names():
            schema += f"\nTable: {table_name}\n"
            for column in inspector.get_columns(table_name):
                col_name = column["name"]
                col_type = str(column["type"])
                nullable = "NULL" if column.get("nullable", True) else "NOT NULL"
                pk_constraint = inspector.get_pk_constraint(table_name)
                is_pk = col_name in pk_constraint.get("constrained_columns", [])
                pk_info = ", PRIMARY KEY" if is_pk else ""
                fk_info = ""
                for fk in inspector.get_foreign_keys(table_name):
                    if col_name in fk.get("constrained_columns", []):
                        ref_table = fk["referred_table"]
                        ref_cols = fk["referred_columns"]
                        fk_info = f", FOREIGN KEY -> {ref_table}({', '.join(ref_cols)})"
                schema += f"  - {col_name}: {col_type} {nullable}{pk_info}{fk_info}\n"
            # Add sample data
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(f'SELECT * FROM "{table_name}" LIMIT 3'))
                    rows = result.fetchall()
                    if rows:
                        schema += "  Sample data:\n"
                        for row in rows:
                            # Use row._mapping if available (SQLAlchemy 1.4+), else fallback
                            try:
                                if hasattr(row, '_mapping'):
                                    row_dict = dict(row._mapping)
                                elif hasattr(row, 'keys'):
                                    row_dict = dict(zip(row.keys(), row))
                                else:
                                    row_dict = dict(row)
                                schema += f"    {row_dict}\n"
                            except Exception as e:
                                schema += f"    [Could not convert row to dict: {e}]\n"
            except Exception as e:
                logger.warning(f"Could not get sample data for {table_name}: {e}")
        return schema
    
    def _convert_nl_to_sql(self, state: AgentState) -> AgentState:
        """Convert natural language question to SQL query"""
        question = state["question"]
        schema = self._get_database_schema()
        
        logger.info(f"🔄 Converting question to SQL: {question}")
        
        system_prompt = f"""You are an expert SQL generator for flight operations data using PostgreSQL.

DATABASE SCHEMA:
{schema}

KEY POINTS:
1. Use double quotes for column names with spaces or special characters
2. PostgreSQL is case-sensitive for quoted identifiers
3. For date comparisons, use proper PostgreSQL date functions
4. Handle NULL values appropriately
5. Use LIMIT to prevent overwhelming results

FUEL CALCULATIONS:
- Fuel consumed = "Block off Fuel" - "Block on Fuel"

Generate ONLY the SQL query without any explanation or markdown formatting.
"""
        
        convert_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Convert this question to SQL: {question}")
        ])
        
        try:
            if LANGCHAIN_AVAILABLE:
                structured_llm = self.llm.with_structured_output(ConvertToSQL)
                sql_generator = convert_prompt | structured_llm
                result = sql_generator.invoke({"question": question})
                # Use dict access for result
                if isinstance(result, dict):
                    state["sql_query"] = result.get("sql_query", "")
                else:
                    state["sql_query"] = getattr(result, "sql_query", "")
            else:
                # Fallback to direct OpenAI
                chain = convert_prompt | self.llm | StrOutputParser()
                state["sql_query"] = chain.invoke({"question": question})
            
            logger.info(f"📊 Generated SQL: {state['sql_query']}")
            
        except Exception as e:
            logger.error(f"Failed to generate SQL: {e}")
            state["sql_query"] = ""
            state["error_message"] = str(e)
        
        return state
    
    def _execute_sql(self, state: AgentState) -> AgentState:
        """Execute the SQL query"""
        sql_query = state.get("sql_query", "").strip()
        
        if not sql_query:
            state["sql_error"] = True
            state["error_message"] = "No SQL query generated"
            return state
        
        logger.info(f"🔍 Executing SQL query: {sql_query[:200]}...")
        
        try:
            # Execute query using db_manager
            data, error = self.db_manager.execute_query(sql_query)
            
            if error:
                state["sql_error"] = True
                state["error_message"] = error
                state["query_result"] = f"Error: {error}"
                logger.error(f"SQL execution error: {error}")
            else:
                state["sql_error"] = False
                state["query_rows"] = data
                state["success"] = True
                
                # Format result for display
                if data:
                    if sql_query.upper().startswith("SELECT"):
                        state["query_result"] = f"Found {len(data)} results"
                    else:
                        affected_rows = data[0].get('affected_rows', 0)
                        state["query_result"] = f"Query executed successfully. {affected_rows} rows affected."
                else:
                    state["query_result"] = "No results found"
                
                logger.info(f"✅ SQL query executed successfully: {len(data)} rows")
                
        except Exception as e:
            state["sql_error"] = True
            state["error_message"] = str(e)
            state["query_result"] = f"Execution error: {str(e)}"
            logger.error(f"SQL execution failed: {e}")
        
        return state
    
    def _generate_human_readable_answer(self, state: AgentState) -> AgentState:
        """Generate a human-readable answer from query results"""
        sql_query = state.get("sql_query", "")
        query_rows = state.get("query_rows", [])
        question = state["question"]
        
        logger.info("📝 Generating human-readable answer")
        
        # Limit data for context window
        sample_data = query_rows[:50] if query_rows else []
        
        system_prompt = """You are an assistant that converts SQL query results into clear, 
comprehensive natural language responses for flight operations data. 
Include specific numbers and insights from the data."""
        
        # Build context based on results
        if not query_rows:
            context = "The query returned no results."
        else:
            context = f"""
Question: {question}

SQL Query: {sql_query}

Query returned {len(query_rows)} total rows.

Sample of results:
{json.dumps(sample_data, indent=2, default=str)}
"""
        
        generate_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", context + "\n\nProvide a clear, comprehensive answer to the question based on this data.")
        ])
        
        try:
            chain = generate_prompt | self.llm | StrOutputParser()
            answer = chain.invoke({})
            state["final_answer"] = answer
            state["query_result"] = answer
            logger.info("✅ Generated human-readable answer")
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            state["final_answer"] = f"Found {len(query_rows)} results but could not generate summary."
        
        return state
    
    def _regenerate_query(self, state: AgentState) -> AgentState:
        """Regenerate the SQL query by rewriting the question"""
        question = state["question"]
        error_message = state.get("error_message", "")
        
        logger.info(f"🔄 Regenerating query (attempt {state['attempts'] + 1}/{state['max_attempts']})")
        
        system_prompt = """You are an assistant that reformulates questions to enable better SQL query generation.
Given the original question and the error encountered, rewrite the question to be more specific 
and avoid the error. Preserve all necessary details for accurate data retrieval."""
        
        rewrite_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", f"""Original Question: {question}
Error encountered: {error_message}

Rewrite the question to avoid this error and be more specific:""")
        ])
        
        try:
            if LANGCHAIN_AVAILABLE:
                structured_llm = self.llm.with_structured_output(RewrittenQuestion)
                rewriter = rewrite_prompt | structured_llm
                result = rewriter.invoke({})
                # Use dict access for result
                if isinstance(result, dict):
                    state["question"] = result.get("question", "")
                else:
                    state["question"] = getattr(result, "question", "")
            else:
                chain = rewrite_prompt | self.llm | StrOutputParser()
                state["question"] = chain.invoke({})
            
            state["attempts"] += 1
            logger.info(f"📝 Rewritten question: {state['question']}")
            
        except Exception as e:
            logger.error(f"Failed to rewrite question: {e}")
            state["attempts"] += 1
        
        return state
    
    def _end_max_iterations(self, state: AgentState) -> AgentState:
        """Handle max iterations reached"""
        logger.warning("⚠️ Maximum attempts reached")
        state["final_answer"] = (
            f"I was unable to process your query after {state['max_attempts']} attempts. "
            f"Last error: {state.get('error_message', 'Unknown error')}. "
            "Please try rephrasing your question or contact support."
        )
        state["query_result"] = state["final_answer"]
        state["success"] = False
        return state
    
    def _execute_sql_router(self, state: AgentState) -> str:
        """Route based on SQL execution result"""
        if not state.get("sql_error", False):
            return "generate_answer"
        else:
            return "regenerate"
    
    def _check_attempts_router(self, state: AgentState) -> str:
        """Route based on number of attempts"""
        if state["attempts"] < state["max_attempts"]:
            return "retry"
        else:
            return "max_iterations"
    
    def process_query(self, question: str, session_id: str = None) -> Dict[str, Any]:
        """Main entry point for processing natural language queries"""
        
        session_id = session_id or self.session_id
        
        logger.info(f"🔍 Processing query for session: {session_id}")
        logger.info(f"❓ Question: {question}")
        
        # Ensure max_attempts is always an integer
        max_attempts = self.max_attempts if isinstance(self.max_attempts, int) and self.max_attempts > 0 else 3
        initial_state = {
            "question": question,
            "session_id": session_id,
            "sql_query": "",
            "query_result": None,
            "query_rows": [],
            "success": False,
            "error_message": "",
            "attempts": 0,
            "max_attempts": max_attempts,
            "metadata": {},
            "final_answer": "",
            "sql_error": False
        }
        
        try:
            # Run the workflow
            result = self.app.invoke(initial_state)
            
            # Prepare response
            response = {
                "success": result.get("success", False),
                "answer": result.get("final_answer") or result.get("query_result", "No answer generated"),
                "metadata": {
                    "sql_query": result.get("sql_query", ""),
                    "row_count": len(result.get("query_rows", [])),
                    "attempts": result.get("attempts", 0),
                    "session_id": session_id
                }
            }
            
            if result.get("error_message"):
                response["error"] = result["error_message"]
            
            logger.info(f"✅ Query processing completed. Success: {response['success']}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            return {
                "success": False,
                "answer": f"I encountered an error while processing your query: {str(e)}",
                "error": str(e),
                "metadata": {"session_id": session_id}
            }
    
    def get_table_schemas(self) -> Dict[str, Any]:
        """Get table schema information"""
        return self.db_manager.get_table_info()
    
    def close(self):
        """Close database connections"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
        if hasattr(self, 'engine'):
            self.engine.dispose()
        logger.info("✅ Closed SQL Agent connections")


# ============================================================================
# DIRECT POSTGRESQL IMPLEMENTATION (FALLBACK)
# ============================================================================

class DirectPostgreSQLAgent:
    """Direct PostgreSQL implementation without LangChain"""
    
    def __init__(self, db_manager: PostgreSQLManager = None,
                 session_id: str = None,
                 max_attempts: int = 3,
                 db_config: Dict[str, str] = None):
        """Initialize direct PostgreSQL agent"""
        
        self.session_id = session_id or "default_session"
        self.max_attempts = max_attempts
        
        # Initialize database manager
        if db_manager:
            self.db_manager = db_manager
        else:
            self.db_manager = PostgreSQLManager(self.session_id, db_config)
        
        # Initialize OpenAI client
        self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        logger.info(f"🚀 Initialized Direct PostgreSQL Agent for session: {self.session_id}")
    
    def _get_table_info_direct(self) -> str:
        """Get table information for context"""
        table_info = self.db_manager.get_table_info()
        
        schema_text = ""
        for table_name, info in table_info.items():
            schema_text += f"\nTable: {table_name} ({info['row_count']} rows)\n"
            schema_text += "Columns:\n"
            
            for col in info['schema']:
                schema_text += f"  - {col['column_name']} ({col['data_type']})"
                if not col.get('nullable', True):
                    schema_text += " NOT NULL"
                schema_text += "\n"
        
        return schema_text
    
    def _generate_sql_with_openai(self, question: str, attempt: int = 0, previous_error: str = None) -> str:
        """Generate SQL using OpenAI directly"""
        table_info = self._get_table_info_direct()
        
        prompt = f"""You are an expert SQL generator for flight operations data using PostgreSQL.

DATABASE SCHEMA:
{table_info}

IMPORTANT NOTES:
1. Use double quotes for column names with spaces: "A/C Registration", "Origin ICAO", etc.
2. PostgreSQL is case-sensitive for quoted identifiers
3. For fuel calculations: Fuel consumed = "Block off Fuel" - "Block on Fuel"
4. Always include LIMIT 1000 for SELECT queries unless specifically asked for all data
5. Handle NULL values appropriately
"""
        
        if previous_error:
            prompt += f"\n\nPREVIOUS ATTEMPT FAILED WITH ERROR:\n{previous_error}\nPlease fix the issue in your SQL.\n"
        
        prompt += f"\n\nGenerate ONLY the SQL query (no explanations) for: {question}"
        
        try:
            response = self.openai_client.chat.completions.create(
                model=getattr(Config, 'OPENAI_MODEL', 'o4-mini'),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,  # Reasonable limit for SQL generation
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
        # Limit data for context
        sample_data = data[:50] if data else []
        
        prompt = f"""Question: {question}

SQL Query Used: {sql_query}

Query Results ({len(data)} total rows):
{json.dumps(sample_data, indent=2, default=str)}

Provide a clear, comprehensive answer to the question based on this flight operations data. 
Include specific numbers and insights.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=getattr(Config, 'OPENAI_MODEL', 'o4-mini'),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,  # More tokens for comprehensive answers
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate answer with OpenAI: {e}")
            return f"Found {len(data)} records. Please check the query results."
    
    def process_query(self, question: str, session_id: str = None) -> Dict[str, Any]:
        """Process query with retry logic"""
        session_id = session_id or self.session_id
        
        logger.info(f"🔍 Processing query for session: {session_id}")
        logger.info(f"❓ Question: {question}")
        
        attempt = 0
        last_error = None
        
        while attempt < self.max_attempts:
            attempt += 1
            logger.info(f"🔄 Attempt {attempt}/{self.max_attempts}")
            
            # Generate SQL
            sql_query = self._generate_sql_with_openai(question, attempt - 1, last_error)
            
            if not sql_query:
                last_error = "Failed to generate SQL query"
                continue
            
            logger.info(f"📊 Generated SQL: {sql_query}")
            
            # Execute query
            data, error = self.db_manager.execute_query(sql_query)
            
            if error:
                last_error = error
                logger.error(f"SQL execution error: {error}")
                continue
            
            # Success! Generate answer
            logger.info(f"✅ Query executed successfully: {len(data)} rows")
            
            answer = self._generate_answer_with_openai(question, sql_query, data)
            
            return {
                "success": True,
                "answer": answer,
                "metadata": {
                    "sql_query": sql_query,
                    "row_count": len(data),
                    "attempts": attempt,
                    "method": "direct_postgresql",
                    "session_id": session_id
                }
            }
        
        # Max attempts reached
        logger.error(f"❌ Failed after {self.max_attempts} attempts")
        return {
            "success": False,
            "answer": f"I was unable to process your query after {self.max_attempts} attempts. Last error: {last_error}",
            "error": last_error,
            "metadata": {
                "attempts": self.max_attempts,
                "session_id": session_id
            }
        }
    
    def close(self):
        """Close database connections"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
        logger.info("✅ Closed Direct PostgreSQL Agent")


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_sql_agent(db_manager: PostgreSQLManager = None,
                    session_id: str = None,
                    max_attempts: int = 3,
                    db_config: Dict[str, str] = None,
                    use_langgraph: bool = True) -> Any:
    """Factory function to create SQL agent instance"""
    
    if use_langgraph and LANGCHAIN_AVAILABLE:
        logger.info("🔧 Creating LangGraph-based SQL Agent")
        return FlightDataPostgreSQLAgent(db_manager, session_id, max_attempts, db_config)
    else:
        logger.info("🔧 Creating Direct PostgreSQL Agent")
        return DirectPostgreSQLAgent(db_manager, session_id, max_attempts, db_config)


# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================

class SQLGenerator:
    """Legacy interface wrapper for backward compatibility"""
    
    def __init__(self):
        self.agent = create_sql_agent(use_langgraph=False)
    
    def generate_sql(self, natural_query: str, table_schemas: Dict[str, List[Dict]], 
                    context: Optional[str] = None) -> Tuple[str, Dict]:
        """Legacy method for backward compatibility"""
        
        result = self.agent.process_query(natural_query)
        
        if result["success"]:
            sql_query = result["metadata"].get("sql_query", "")
            return sql_query, result["metadata"]
        else:
            return "", {"error": result.get("error", "Unknown error")}


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'flight_data',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    # Create agent with custom configuration
    agent = create_sql_agent(
        session_id="test_session",
        max_attempts=3,
        db_config=db_config,
        use_langgraph=True  # Set to False to use direct implementation
    )
    
    # Test queries
    test_questions = [
        "What are the top 10 aircraft by fuel consumption?",
        "Show me flights from KJFK to KLAX",
        "What's the average fuel efficiency by aircraft type?",
        "Show me any data quality errors in the system",
        "What are the errors?"  # Your specific query
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"🔍 Question: {question}")
        print(f"{'='*60}")
        
        result = agent.process_query(question)
        
        print(f"\n📊 Success: {result['success']}")
        print(f"\n💬 Answer:\n{result['answer']}")
        
        if result['success'] and 'sql_query' in result['metadata']:
            print(f"\n🔧 SQL Query:\n{result['metadata']['sql_query']}")
            print(f"\n📈 Rows returned: {result['metadata']['row_count']}")
            print(f"🔄 Attempts: {result['metadata']['attempts']}")
    
    # Clean up
    agent.close()