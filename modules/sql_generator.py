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
# SUMMARY DETECTION AND GENERATION
# ============================================================================

def is_summary_request(question: str) -> bool:
    """Detect if the question is asking for a summary"""
    summary_keywords = [
        'summary', 'summarize', 'summarise', 'overview', 'describe',
        'statistics', 'stats', 'breakdown', 'analysis', 'profile',
        'what is in', 'tell me about', 'show me the data',
        'table info', 'table information', 'data profile'
    ]
    
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in summary_keywords)


def generate_table_summary(conn, table_name: str, schema: str = 'public', max_top: int = 5) -> str:
    """Generate a detailed summary of a PostgreSQL table with comprehensive statistics"""
    import psycopg2
    import psycopg2.extras
    
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # 1. Get column names and types
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table_name))
        columns = cursor.fetchall()
        
        # 2. Get total row count
        cursor.execute(f'SELECT COUNT(*) as count FROM "{table_name}"')
        total_rows = cursor.fetchone()['count']
        
        # 3. Get table size
        cursor.execute("""
            SELECT pg_size_pretty(pg_total_relation_size(%s)) as size
        """, (table_name,))
        table_size = cursor.fetchone()['size']
        
        # Start building summary
        summary = [
            f"# 📊 Table Summary: `{table_name}`",
            f"\n## Overview",
            f"- **Total Rows**: {total_rows:,}",
            f"- **Total Columns**: {len(columns)}",
            f"- **Table Size**: {table_size}",
            f"\n## Column Details\n"
        ]
        
        # 4. Analyze each column
        for col_info in columns:
            col = col_info['column_name']
            dtype = col_info['data_type']
            nullable = col_info['is_nullable']
            
            summary.append(f"### 📋 Column: `{col}`")
            summary.append(f"- **Type**: {dtype}")
            summary.append(f"- **Nullable**: {nullable}")
            
            # Get null count
            cursor.execute(f'''
                SELECT 
                    COUNT(*) - COUNT("{col}") as null_count,
                    ROUND(100.0 * (COUNT(*) - COUNT("{col}")) / COUNT(*), 2) as null_percentage
                FROM "{table_name}"
            ''')
            null_info = cursor.fetchone()
            summary.append(f"- **Null Values**: {null_info['null_count']:,} ({null_info['null_percentage']}%)")
            
            # Analyze based on data type
            if dtype in ('integer', 'bigint', 'numeric', 'double precision', 'real', 'smallint', 'decimal'):
                # Numeric analysis
                cursor.execute(f'''
                    SELECT 
                        AVG("{col}")::numeric(10,2) AS avg_value,
                        MIN("{col}") AS min_value,
                        MAX("{col}") AS max_value,
                        STDDEV("{col}")::numeric(10,2) AS std_dev,
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}") AS q1,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY "{col}") AS median,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}") AS q3
                    FROM "{table_name}"
                    WHERE "{col}" IS NOT NULL
                ''')
                stats = cursor.fetchone()
                
                if stats and stats['avg_value'] is not None:
                    summary.append("\n**📈 Statistical Summary:**")
                    summary.append(f"- Average: {stats['avg_value']:,.2f}")
                    summary.append(f"- Min: {stats['min_value']:,}")
                    summary.append(f"- Max: {stats['max_value']:,}")
                    summary.append(f"- Std Dev: {stats['std_dev']:,.2f}" if stats['std_dev'] else "- Std Dev: N/A")
                    summary.append(f"- Quartiles: Q1={stats['q1']:,}, Median={stats['median']:,}, Q3={stats['q3']:,}")
                
            elif dtype in ('date', 'timestamp', 'timestamp without time zone', 'timestamp with time zone'):
                # Date/time analysis
                cursor.execute(f'''
                    SELECT 
                        MIN("{col}") AS earliest,
                        MAX("{col}") AS latest,
                        MAX("{col}") - MIN("{col}") AS date_range
                    FROM "{table_name}"
                    WHERE "{col}" IS NOT NULL
                ''')
                date_stats = cursor.fetchone()
                
                if date_stats and date_stats['earliest']:
                    summary.append("\n**📅 Date Range:**")
                    summary.append(f"- Earliest: {date_stats['earliest']}")
                    summary.append(f"- Latest: {date_stats['latest']}")
                    summary.append(f"- Range: {date_stats['date_range']}")
                
            elif dtype in ('character varying', 'text', 'varchar', 'char'):
                # Text analysis
                cursor.execute(f'''
                    SELECT 
                        COUNT(DISTINCT "{col}") as distinct_count,
                        AVG(LENGTH("{col}")) as avg_length,
                        MIN(LENGTH("{col}")) as min_length,
                        MAX(LENGTH("{col}")) as max_length
                    FROM "{table_name}"
                    WHERE "{col}" IS NOT NULL
                ''')
                text_stats = cursor.fetchone()
                
                if text_stats:
                    summary.append("\n**📝 Text Statistics:**")
                    summary.append(f"- Distinct Values: {text_stats['distinct_count']:,}")
                    summary.append(f"- Avg Length: {text_stats['avg_length']:.1f}" if text_stats['avg_length'] else "- Avg Length: N/A")
                    summary.append(f"- Length Range: {text_stats['min_length']} - {text_stats['max_length']}")
                
                # Top values
                cursor.execute(f'''
                    SELECT "{col}", COUNT(*) AS frequency
                    FROM "{table_name}"
                    WHERE "{col}" IS NOT NULL
                    GROUP BY "{col}"
                    ORDER BY frequency DESC
                    LIMIT %s
                ''', (max_top,))
                top_values = cursor.fetchall()
                
                if top_values:
                    summary.append(f"\n**🔝 Top {len(top_values)} Values:**")
                    for row in top_values:
                        summary.append(f"- `{row['frequency']:,}x` → {row[col]}")
            
            summary.append("")  # Add blank line between columns
        
        # 5. Add any special analysis for flight data tables
        if table_name == 'clean_flights':
            summary.append("\n## ✈️ Flight-Specific Analysis")
            
            # Most common routes
            cursor.execute('''
                SELECT 
                    "Origin ICAO" || ' → ' || "Destination ICAO" as route,
                    COUNT(*) as flight_count
                FROM clean_flights
                GROUP BY "Origin ICAO", "Destination ICAO"
                ORDER BY flight_count DESC
                LIMIT 5
            ''')
            routes = cursor.fetchall()
            
            if routes:
                summary.append("\n**Most Common Routes:**")
                for route in routes:
                    summary.append(f"- {route['route']}: {route['flight_count']:,} flights")
            
            # Fuel efficiency stats
            cursor.execute('''
                SELECT 
                    AVG("Block off Fuel" - "Block on Fuel") as avg_fuel_consumed,
                    MAX("Block off Fuel" - "Block on Fuel") as max_fuel_consumed
                FROM clean_flights
                WHERE "Block off Fuel" IS NOT NULL AND "Block on Fuel" IS NOT NULL
            ''')
            fuel_stats = cursor.fetchone()
            
            if fuel_stats and fuel_stats['avg_fuel_consumed']:
                summary.append("\n**⛽ Fuel Consumption:**")
                summary.append(f"- Average Fuel Consumed: {fuel_stats['avg_fuel_consumed']:,.2f}")
                summary.append(f"- Maximum Fuel Consumed: {fuel_stats['max_fuel_consumed']:,.2f}")
        
        elif table_name == 'error_flights':
            summary.append("\n## ❌ Error Analysis")
            
            # Error distribution
            cursor.execute('''
                SELECT 
                    "Error_Category",
                    COUNT(*) as error_count,
                    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
                FROM error_flights
                GROUP BY "Error_Category"
                ORDER BY error_count DESC
            ''')
            errors = cursor.fetchall()
            
            if errors:
                summary.append("\n**Error Distribution:**")
                for error in errors:
                    summary.append(f"- {error['Error_Category']}: {error['error_count']} ({error['percentage']}%)")
        
        cursor.close()
        return "\n".join(summary)
        
    except Exception as e:
        cursor.close()
        logger.error(f"Failed to generate table summary: {e}")
        raise


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
                
                # Add primary key info
                pk_constraint = inspector.get_pk_constraint(table_name)
                is_pk = col_name in pk_constraint.get("constrained_columns", [])
                pk_info = ", PRIMARY KEY" if is_pk else ""
                
                # Add foreign key info
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
                            schema += f"    {dict(row)}\n"
            except Exception as e:
                logger.warning(f"Could not get sample data for {table_name}: {e}")
        
        return schema
    
    def _convert_nl_to_sql(self, state: AgentState) -> AgentState:
        """Convert natural language question to SQL query"""
        question = state["question"]
        schema = self._get_database_schema()
        
        logger.info(f"🔄 Converting question to SQL: {question}")
        
        # Escape curly braces in schema for prompt template
        safe_schema = schema.replace('{', '{{').replace('}', '}}')
        system_prompt = (
            "You are an expert SQL generator for flight operations data using PostgreSQL.\n\n"
            "DATABASE SCHEMA:\n"
            f"{safe_schema}\n\n"
            "KEY POINTS:\n"
            "1. Use double quotes for column names with spaces or special characters\n"
            "2. PostgreSQL is case-sensitive for quoted identifiers\n"
            "3. For date comparisons, use proper PostgreSQL date functions\n"
            "4. Handle NULL values appropriately\n"
            "5. Use LIMIT to prevent overwhelming results\n\n"
            "FUEL CALCULATIONS:\n"
            "- Fuel consumed = \"Block off Fuel\" - \"Block on Fuel\"\n\n"
            "Generate ONLY the SQL query without any explanation or markdown formatting.\n"
        )
        
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
        
        # Escape curly braces in context for prompt template
        safe_context = context.replace('{', '{{').replace('}', '}}')
        generate_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", safe_context + "\n\nProvide a clear, comprehensive answer to the question based on this data.")
        ])
        
        try:
            chain = generate_prompt | self.llm | StrOutputParser()
            answer = chain.invoke({})
            # Append markdown table of rows if available
            if sample_data:
                headers = list(sample_data[0].keys())
            state["final_answer"] = answer
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
        
        # Escape curly braces in error_message for prompt template
        safe_error_message = error_message.replace('{', '{{').replace('}', '}}')
        system_prompt = (
            "You are an assistant that reformulates questions to enable better SQL query generation.\n"
            "Given the original question and the error encountered, rewrite the question to be more specific \n"
            "and avoid the error. Preserve all necessary details for accurate data retrieval."
        )
        rewrite_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", f"""Original Question: {{question}}\nError encountered: {safe_error_message}\n\nRewrite the question to avoid this error and be more specific:""")
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
        session_id = session_id or self.session_id
        logger.info(f"🔍 Processing query for session: {session_id}")
        logger.info(f"❓ Question: {question}")

        # --- SUMMARY DETECTION ---
        if is_summary_request(question):
            # Try to detect table name from question, fallback to clean_flights
            table_name = 'clean_flights'
            if 'error' in question.lower():
                table_name = 'error_flights'
            try:
                summary_md = generate_table_summary(self.db_manager.conn, table_name)
                return {
                    "success": True,
                    "answer": summary_md,
                    "metadata": {"method": "summary", "table": table_name, "session_id": session_id}
                }
            except Exception as e:
                logger.error(f"Failed to generate summary: {e}")
                return {
                    "success": False,
                    "answer": f"Could not generate summary: {e}",
                    "error": str(e),
                    "metadata": {"method": "summary", "table": table_name, "session_id": session_id}
                }

        # --- NORMAL FLOW ---
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
            result = self.app.invoke(initial_state)
            response = {
                "success": result.get("success", False),
                "answer": result.get("final_answer") or result.get("query_result", "No answer generated"),
                "metadata": {
                    "sql_query": result.get("sql_query", ""),
                    "row_count": len(result.get("query_rows", [])),
                    "attempts": result.get("attempts", 0),
                    "session_id": session_id
                },
                "table_rows": result.get("query_rows", [])
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