# sql_generator.py

"""
SQL Agent for Flight Data Analysis - PostgreSQL Implementation with Dual LLM Architecture

A sophisticated SQL agent using LangChain's SQL tools and LangGraph for natural language
to SQL conversion and execution with PostgreSQL, featuring:

DUAL LLM ARCHITECTURE:
- GPT-4.1 (gpt-4-turbo): Query analysis, improvement, and strategic decision-making
- GPT-4o-mini: SQL generation, execution, and detailed response generation

WORKFLOW:
1. GPT-4.1 analyzes the user question and determines if it's a summary request
2. GPT-4.1 improves the query for better SQL generation
3. GPT-4o-mini generates optimized SQL queries
4. GPT-4o-mini provides comprehensive analysis of results

Author: Flight Data Analysis System
Dependencies: langchain, langchain-openai, langchain-community, psycopg2, openai, langgraph

REQUIRED CONFIG.PY ADDITIONS:
```python
class Config:
    # Existing config...
    
    # Dual LLM Configuration
    OPENAI_ANALYSIS_MODEL = os.getenv('OPENAI_ANALYSIS_MODEL', 'gpt-4-turbo')
    OPENAI_ANALYSIS_TEMPERATURE = float(os.getenv('OPENAI_ANALYSIS_TEMPERATURE', 0.1))
    OPENAI_ANALYSIS_MAX_TOKENS = int(os.getenv('OPENAI_ANALYSIS_MAX_TOKENS', 1000))
    
    OPENAI_EXECUTION_MODEL = os.getenv('OPENAI_EXECUTION_MODEL', 'gpt-4o-mini')
    OPENAI_EXECUTION_TEMPERATURE = float(os.getenv('OPENAI_EXECUTION_TEMPERATURE', 0.1))
    OPENAI_EXECUTION_MAX_TOKENS = int(os.getenv('OPENAI_EXECUTION_MAX_TOKENS', 4096))
```
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from typing_extensions import TypedDict
from datetime import datetime
import psycopg2
import psycopg2.extras
import openai
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

# LangChain imports - REQUIRED
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
# SUMMARY DETECTION AND QUERY IMPROVEMENT WITH GPT-4.1
# ============================================================================

class QueryAnalysis(BaseModel):
    """Model for query analysis results"""
    is_summary_request: bool = Field(
        description="Whether the question is asking for a table summary or overview"
    )
    improved_query: str = Field(
        description="An improved, more specific version of the original question"
    )
    target_table: str = Field(
        description="The most appropriate table for this query (clean_flights or error_flights)",
        default="clean_flights"
    )
    query_type: str = Field(
        description="Type of query: summary, analytical, specific_data, or exploratory"
    )
    complexity_level: str = Field(
        description="Complexity level: simple, medium, complex"
    )

def analyze_and_improve_query(question: str) -> QueryAnalysis:
    """Use GPT-4.1 with function calling to analyze and improve the query"""
    
    # Initialize GPT-4.1 for query analysis
    analysis_llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        model=getattr(Config, 'OPENAI_ANALYSIS_MODEL', 'gpt-4-turbo'),
        temperature=getattr(Config, 'OPENAI_ANALYSIS_TEMPERATURE', 0.1),
        max_tokens=getattr(Config, 'OPENAI_ANALYSIS_MAX_TOKENS', 1000)
    )
    
    system_prompt = """You are an expert flight data analyst. Analyze user questions about flight operations data and improve them for better SQL query generation.

AVAILABLE TABLES:
- clean_flights: Main flight operations data with details like aircraft registration, routes, fuel consumption, timestamps
- error_flights: Data quality errors and issues in flight operations

ANALYSIS GUIDELINES:
1. Determine if the user wants a table summary/overview vs specific data queries
2. Improve the question to be more specific and SQL-friendly
3. Identify the most appropriate target table
4. Assess query complexity for proper processing

EXAMPLES:
- "What are the errors?" → Summary request for error_flights table
- "Show me fuel consumption" → Specific data query for clean_flights table
- "Tell me about the data" → Summary request for clean_flights table
- "Which flights used the most fuel?" → Analytical query for clean_flights table
"""
    
    analysis_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Analyze and improve this flight data question: {question}")
    ])
    
    try:
        structured_llm = analysis_llm.with_structured_output(QueryAnalysis)
        analyzer = analysis_prompt | structured_llm
        result = analyzer.invoke({"question": question})
        
        logger.info(f"🧠 GPT-4.1 Analysis - Summary: {result.is_summary_request}, "
                   f"Table: {result.target_table}, Type: {result.query_type}")
        logger.info(f"📝 Improved query: {result.improved_query}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze query with GPT-4.1: {e}")
        # Fallback to simple analysis
        return QueryAnalysis(
            is_summary_request=any(keyword in question.lower() for keyword in [
                'summary', 'overview', 'describe', 'stats', 'what is in', 'tell me about'
            ]),
            improved_query=question,
            target_table="error_flights" if "error" in question.lower() else "clean_flights",
            query_type="exploratory",
            complexity_level="medium"
        )


def analyze_and_improve_query(question: str) -> QueryAnalysis:
    """Use GPT-4.1 with function calling to analyze and improve the query"""
    
    # Initialize GPT-4.1 for query analysis
    analysis_llm = ChatOpenAI(
        api_key=Config.OPENAI_API_KEY,
        model=getattr(Config, 'OPENAI_ANALYSIS_MODEL', 'gpt-4-turbo'),
        temperature=getattr(Config, 'OPENAI_ANALYSIS_TEMPERATURE', 0.1),
        max_tokens=getattr(Config, 'OPENAI_ANALYSIS_MAX_TOKENS', 1000)
    )
    
    system_prompt = """You are an expert flight data analyst. Analyze user questions about flight operations data and improve them for better SQL query generation.

AVAILABLE TABLES:
- clean_flights: Main flight operations data with details like aircraft registration, routes, fuel consumption, timestamps
- error_flights: Data quality errors and issues in flight operations

ANALYSIS GUIDELINES:
1. Determine if the user wants a table summary/overview vs specific data queries
2. Improve the question to be more specific and SQL-friendly
3. Identify the most appropriate target table
4. Assess query complexity for proper processing

EXAMPLES:
- "What are the errors?" → Summary request for error_flights table
- "Show me fuel consumption" → Specific data query for clean_flights table
- "Tell me about the data" → Summary request for clean_flights table
- "Which flights used the most fuel?" → Analytical query for clean_flights table
"""
    
    analysis_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Analyze and improve this flight data question: {question}")
    ])
    
    try:
        structured_llm = analysis_llm.with_structured_output(QueryAnalysis)
        analyzer = analysis_prompt | structured_llm
        result = analyzer.invoke({"question": question})
        
        logger.info(f"🧠 GPT-4.1 Analysis - Summary: {result.is_summary_request}, "
                   f"Table: {result.target_table}, Type: {result.query_type}")
        logger.info(f"📝 Improved query: {result.improved_query}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze query with GPT-4.1: {e}")
        # Fallback to simple analysis
        return QueryAnalysis(
            is_summary_request=any(keyword in question.lower() for keyword in [
                'summary', 'overview', 'describe', 'stats', 'what is in', 'tell me about'
            ]),
            improved_query=question,
            target_table="error_flights" if "error" in question.lower() else "clean_flights",
            query_type="exploratory",
            complexity_level="medium"
        )


def generate_table_summary(db_manager, table_name: str, schema: str = 'public', max_top: int = 5) -> str:
    """Generate a detailed summary of a PostgreSQL table with comprehensive statistics"""
    
    # Use the database manager's connection
    conn = db_manager.conn
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        logger.info(f"📊 Generating summary for table: {table_name} in session: {db_manager.session_id}")
        
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
            f"\n**Session**: `{db_manager.session_id}`",
            f"**Database**: `{db_manager.db_name}`",
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
        logger.info(f"✅ Generated summary for {table_name}: {len(summary)} lines")
        return "\n".join(summary)
        
    except Exception as e:
        if cursor:
            cursor.close()
        logger.error(f"Failed to generate table summary: {e}")
        raise


# ============================================================================
# POSTGRESQL SQL AGENT WITH LANGGRAPH
# ============================================================================

class FlightDataPostgreSQLAgent:
    """SQL Agent using LangGraph for PostgreSQL with GPT-4.1 analysis and GPT-4o-mini execution"""
    
    def __init__(self, db_manager: PostgreSQLManager = None, 
                 session_id: str = None, 
                 max_attempts: int = 3,
                 db_config: Dict[str, str] = None):
        """Initialize SQL Agent with PostgreSQL support and dual LLM setup"""
        
        self.session_id = session_id or "default_session"
        self.max_attempts = max_attempts
        
        # Initialize database manager
        if db_manager:
            self.db_manager = db_manager
        else:
            self.db_manager = PostgreSQLManager(self.session_id, db_config)
        
        # Get SQLAlchemy engine for LangChain
        self.engine = create_engine(self.db_manager.get_connection_string())
        
        # Initialize GPT-4.1 for query analysis and improvement
        self.analysis_llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model=getattr(Config, 'OPENAI_ANALYSIS_MODEL', 'gpt-4-turbo'),
            temperature=getattr(Config, 'OPENAI_ANALYSIS_TEMPERATURE', 0.1),
            max_tokens=getattr(Config, 'OPENAI_ANALYSIS_MAX_TOKENS', 1000)
        )
        
        # Initialize GPT-4o-mini for SQL generation and answer generation
        self.execution_llm = ChatOpenAI(
            api_key=Config.OPENAI_API_KEY,
            model=getattr(Config, 'OPENAI_EXECUTION_MODEL', 'gpt-4o-mini'),
            temperature=getattr(Config, 'OPENAI_EXECUTION_TEMPERATURE', 0.1),
            max_tokens=getattr(Config, 'OPENAI_EXECUTION_MAX_TOKENS', 4096)
        )
        
        # Build the workflow
        self._build_workflow()
        
        logger.info(f"🚀 Successfully initialized PostgreSQL SQL Agent with dual LLM setup for session: {self.session_id}")
        logger.info(f"🧠 Analysis LLM: gpt-4-turbo | 🔧 Execution LLM: gpt-4o-mini")
    
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
        """Get database schema information using the session database manager"""
        try:
            # Use the database manager's get_table_info method
            table_info = self.db_manager.get_table_info()
            schema = ""
            
            for table_name, info in table_info.items():
                schema += f"\nTable: {table_name} ({info['row_count']} rows)\n"
                
                for column in info['schema']:
                    col_name = column["column_name"]
                    col_type = column["data_type"]
                    nullable = "NULL" if column.get("nullable", True) else "NOT NULL"
                    
                    schema += f"  - {col_name}: {col_type} {nullable}\n"
                
                # Add sample data using the database manager
                try:
                    sample_data, error = self.db_manager.execute_query(f'SELECT * FROM "{table_name}" LIMIT 3')
                    if not error and sample_data:
                        schema += "  Sample data:\n"
                        for row in sample_data:
                            schema += f"    {dict(row)}\n"
                except Exception as e:
                    logger.warning(f"Could not get sample data for {table_name}: {e}")
            
            logger.info(f"📋 Retrieved schema for {len(table_info)} tables from session database")
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get database schema: {e}")
            return "Error: Could not retrieve database schema"
    
    def _convert_nl_to_sql(self, state: AgentState) -> AgentState:
        """Convert natural language question to SQL query using GPT-4o-mini"""
        question = state["question"]
        schema = self._get_database_schema()
        
        logger.info(f"🔄 Converting question to SQL using GPT-4o-mini: {question}")
        
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
            # Use GPT-4o-mini for SQL generation
            structured_llm = self.execution_llm.with_structured_output(ConvertToSQL)
            sql_generator = convert_prompt | structured_llm
            result = sql_generator.invoke({"question": question})
            
            # Handle structured output
            if isinstance(result, dict):
                state["sql_query"] = result.get("sql_query", "")
            else:
                state["sql_query"] = getattr(result, "sql_query", "")
            
            logger.info(f"📊 Generated SQL with GPT-4o-mini: {state['sql_query']}")
            
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
        """Generate a human-readable answer from query results using GPT-4o-mini for complex analysis"""
        sql_query = state.get("sql_query", "")
        query_rows = state.get("query_rows", [])
        question = state["question"]
        
        logger.info("📝 Generating human-readable answer with GPT-4o-mini")
        
        # Limit data for context window
        sample_data = query_rows[:50] if query_rows else []
        
        system_prompt = """You are an expert flight operations data analyst using GPT-4o-mini for complex analysis. 
Your task is to convert SQL query results into clear, comprehensive, and insightful natural language responses.

ANALYSIS REQUIREMENTS:
1. Provide specific numbers, statistics, and quantitative insights
2. Identify patterns, trends, and anomalies in the data
3. Offer operational insights relevant to flight operations
4. Use professional aviation terminology where appropriate
5. Structure the response with clear sections and key findings
6. Highlight any data quality issues or limitations

RESPONSE FORMAT:
- Start with a concise summary of key findings
- Provide detailed analysis with specific metrics
- Include operational recommendations if relevant
- End with any caveats or additional insights"""
        
        # Build context based on results
        if not query_rows:
            context = "The query returned no results."
        else:
            context = f"""
Original Question: {question}

SQL Query Executed: {sql_query}

Query Results Summary:
- Total rows returned: {len(query_rows)}
- Data sample (first {len(sample_data)} rows):

{json.dumps(sample_data, indent=2, default=str)}
"""
        
        # Escape curly braces in context for prompt template
        safe_context = context.replace('{', '{{').replace('}', '}}')
        generate_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", safe_context + "\n\nProvide a comprehensive analysis and answer to the original question based on this flight operations data.")
        ])
        
        try:
            # Use GPT-4o-mini for complex analysis and answer generation
            chain = generate_prompt | self.execution_llm | StrOutputParser()
            answer = chain.invoke({})
            state["final_answer"] = answer
            logger.info("✅ Generated comprehensive analysis with GPT-4o-mini")
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            state["final_answer"] = f"Found {len(query_rows)} results but could not generate comprehensive analysis."
        
        return state
    
    def _regenerate_query(self, state: AgentState) -> AgentState:
        """Regenerate the SQL query by rewriting the question using GPT-4.1"""
        question = state["question"]
        error_message = state.get("error_message", "")
        
        logger.info(f"🔄 Regenerating query with GPT-4.1 (attempt {state['attempts'] + 1}/{state['max_attempts']})")
        
        # Escape curly braces in error_message for prompt template
        safe_error_message = error_message.replace('{', '{{').replace('}', '}}')
        system_prompt = (
            "You are an expert flight data analyst using GPT-4.1 for query improvement.\n"
            "Given the original question and the SQL execution error, rewrite the question to be more specific, "
            "clearer, and likely to generate working SQL. Consider the database schema and common SQL pitfalls.\n\n"
            "COMMON ISSUES TO AVOID:\n"
            "- Column name case sensitivity and special characters\n"
            "- Missing table qualifiers\n"
            "- Incorrect date/time formats\n"
            "- Ambiguous joins or relationships\n"
            "- NULL value handling\n\n"
            "Preserve all necessary details for accurate data retrieval while making the question more SQL-friendly."
        )
        rewrite_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", f"""Original Question: {{question}}\nSQL Error encountered: {safe_error_message}\n\nRewrite the question to avoid this error and be more specific for SQL generation:""")
        ])
        
        try:
            # Use GPT-4.1 for intelligent query rewriting
            structured_llm = self.analysis_llm.with_structured_output(RewrittenQuestion)
            rewriter = rewrite_prompt | structured_llm
            result = rewriter.invoke({})
            
            # Handle structured output
            if isinstance(result, dict):
                state["question"] = result.get("question", "")
            else:
                state["question"] = getattr(result, "question", "")
            
            state["attempts"] += 1
            logger.info(f"📝 GPT-4.1 rewritten question: {state['question']}")
            
        except Exception as e:
            logger.error(f"Failed to rewrite question with GPT-4.1: {e}")
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
        logger.info(f"🗄️ Using database: {self.db_manager.db_name}")
        logger.info(f"❓ Original question: {question}")

        # --- STEP 1: ANALYZE AND IMPROVE QUERY WITH GPT-4.1 ---
        try:
            query_analysis = analyze_and_improve_query(question)
            improved_question = query_analysis.improved_query
            target_table = query_analysis.target_table
            is_summary = query_analysis.is_summary_request
            query_type = query_analysis.query_type
            complexity = query_analysis.complexity_level
            
            logger.info(f"🧠 GPT-4.1 Analysis Complete:")
            logger.info(f"   - Summary Request: {is_summary}")
            logger.info(f"   - Target Table: {target_table}")
            logger.info(f"   - Query Type: {query_type}")
            logger.info(f"   - Complexity: {complexity}")
            logger.info(f"   - Improved Question: {improved_question}")
            
        except Exception as e:
            logger.error(f"Failed to analyze query with GPT-4.1: {e}")
            # Fallback to original question
            improved_question = question
            target_table = 'error_flights' if 'error' in question.lower() else 'clean_flights'
            is_summary = any(keyword in question.lower() for keyword in [
                'summary', 'overview', 'describe', 'stats', 'what is in', 'tell me about'
            ])
            query_type = "exploratory"
            complexity = "medium"

        # --- STEP 2: HANDLE SUMMARY REQUESTS ---
        if is_summary:
            logger.info(f"📊 Processing summary request for table: {target_table}")
            try:
                summary_md = generate_table_summary(self.db_manager, target_table)
                return {
                    "success": True,
                    "answer": summary_md,
                    "metadata": {
                        "method": "summary", 
                        "table": target_table, 
                        "session_id": session_id,
                        "database": self.db_manager.db_name,
                        "original_question": question,
                        "improved_question": improved_question,
                        "query_type": query_type,
                        "complexity": complexity,
                        "analysis_model": "gpt-4-turbo"
                    }
                }
            except Exception as e:
                logger.error(f"Failed to generate summary: {e}")
                return {
                    "success": False,
                    "answer": f"Could not generate summary for {target_table}: {e}",
                    "error": str(e),
                    "metadata": {
                        "method": "summary", 
                        "table": target_table, 
                        "session_id": session_id,
                        "database": self.db_manager.db_name,
                        "original_question": question,
                        "analysis_model": "gpt-4-turbo"
                    }
                }

        # --- STEP 3: NORMAL FLOW WITH IMPROVED QUESTION ---
        logger.info(f"🔄 Processing analytical query with improved question")
        
        # Ensure max_attempts is always an integer
        max_attempts = self.max_attempts if isinstance(self.max_attempts, int) and self.max_attempts > 0 else 3
        initial_state = {
            "question": improved_question,  # Use improved question from GPT-4.1
            "session_id": session_id,
            "sql_query": "",
            "query_result": None,
            "query_rows": [],
            "success": False,
            "error_message": "",
            "attempts": 0,
            "max_attempts": max_attempts,
            "metadata": {
                "original_question": question,
                "improved_question": improved_question,
                "target_table": target_table,
                "query_type": query_type,
                "complexity": complexity,
                "analysis_model": "gpt-4-turbo",
                "execution_model": "gpt-4o-mini",
                "database": self.db_manager.db_name
            },
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
                    "session_id": session_id,
                    "database": self.db_manager.db_name,
                    "method": "langgraph",
                    "original_question": question,
                    "improved_question": improved_question,
                    "target_table": target_table,
                    "query_type": query_type,
                    "complexity": complexity,
                    "analysis_model": "gpt-4-turbo",
                    "execution_model": "gpt-4o-mini"
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
                "metadata": {
                    "session_id": session_id, 
                    "database": self.db_manager.db_name,
                    "method": "langgraph",
                    "original_question": question,
                    "improved_question": improved_question,
                    "analysis_model": "gpt-4-turbo",
                    "execution_model": "gpt-4o-mini"
                }
            }
    
    def get_table_schemas(self) -> Dict[str, Any]:
        """Get table schema information using the database manager"""
        return self.db_manager.get_table_info()
    
    def close(self):
        """Close database connections - delegates to database manager"""
        if hasattr(self, 'db_manager') and self.db_manager:
            # Note: We don't close the db_manager here since it might be used elsewhere
            # The calling code (app4.py) should manage the db_manager lifecycle
            logger.info(f"🔗 SQL Agent closed for session: {self.session_id}")
        if hasattr(self, 'engine'):
            self.engine.dispose()
            logger.info("✅ SQLAlchemy engine disposed")
        logger.info("✅ SQL Agent connections cleaned up")


# ============================================================================
# FACTORY FUNCTIONS - UPDATED FOR SESSION-BASED DATABASE ARCHITECTURE
# ============================================================================

def create_sql_agent(db_manager, session_id: str = None, max_attempts: int = 3, 
                    db_config: Dict[str, str] = None, use_langgraph: bool = True) -> FlightDataPostgreSQLAgent:
    """
    Factory function to create SQL agent instance with existing database manager
    
    Args:
        db_manager: Existing PostgreSQL database manager (required)
        session_id: Session identifier
        max_attempts: Maximum retry attempts for failed queries
        db_config: Database configuration (ignored when db_manager is provided)
        use_langgraph: Use LangGraph implementation (always True now, for backward compatibility)
    
    Returns:
        FlightDataPostgreSQLAgent instance
    """
    
    if not db_manager:
        raise ValueError("db_manager is required and cannot be None")
    
    logger.info("🔧 Creating LangGraph-based SQL Agent with existing database manager")
    logger.info(f"🗄️ Session database: {getattr(db_manager, 'db_name', 'unknown')}")
    logger.info(f"🆔 Session ID: {session_id or 'default'}")
    
    return FlightDataPostgreSQLAgent(db_manager, session_id, max_attempts)


# ============================================================================
# BACKWARD COMPATIBILITY - UPDATED FOR SESSION-BASED ARCHITECTURE
# ============================================================================

class SQLGenerator:
    """Legacy interface wrapper for backward compatibility with session-based database"""
    
    def __init__(self, db_manager=None, session_id: str = None):
        """Initialize with existing database manager"""
        if not db_manager:
            raise ValueError("db_manager is required for session-based architecture")
        
        self.agent = create_sql_agent(db_manager, session_id, 3, None, True)
    
    def generate_sql(self, natural_query: str, table_schemas: Dict[str, List[Dict]] = None, 
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
    # Example showing integration with session-based database architecture
    # This demonstrates how the SQL agent works with your existing database.py setup
    
    print("🚀 SQL Agent Example with Session-Based PostgreSQL")
    print("=" * 80)
    
    # Step 1: Create a database manager (like in your app4.py)
    try:
        # Import your database manager
        from modules.database import PostgreSQLManager
        
        # Create a test session
        test_session_id = "test_session_123"
        print(f"📊 Creating database manager for session: {test_session_id}")
        
        # Initialize database manager (this creates the session database)
        db_manager = PostgreSQLManager(test_session_id)
        print(f"✅ Database manager created for database: {db_manager.db_name}")
        
        # Step 2: Create SQL agent with existing database manager (like in your app4.py)
        print(f"🤖 Creating SQL agent with existing database manager...")
        agent = create_sql_agent(
            db_manager=db_manager,        # Your existing database manager
            session_id=test_session_id,   # Session ID
            max_attempts=3,               # Max retry attempts
            db_config=None,               # Not used (db_manager provided)
            use_langgraph=True            # Always True now (backward compatibility)
        )
        print(f"✅ SQL agent created successfully")
        
        # Step 3: Check if tables exist (requires CSV data to be loaded first)
        table_info = agent.get_table_schemas()
        if not table_info:
            print("⚠️  No tables found in session database")
            print("   In your app4.py, CSV data should be loaded via:")
            print("   db_manager.load_csv_data(clean_csv_path, error_csv_path)")
        else:
            print(f"📋 Available tables: {list(table_info.keys())}")
            
            # Step 4: Test queries (only if tables exist)
            test_questions = [
                # Summary requests (will be detected by GPT-4.1)
                "What are the errors?",
                "Give me an overview of the flight data",
                
                # Analytical queries (will be improved by GPT-4.1, executed by GPT-4o-mini)
                "Show me the top 5 flights by fuel consumption",
                "What aircraft types are in the data?",
            ]
            
            print(f"\n🔬 Testing dual LLM workflow...")
            for question in test_questions:
                print(f"\n" + "-" * 60)
                print(f"❓ Question: {question}")
                print(f"-" * 60)
                
                result = agent.process_query(question)
                
                print(f"📊 Success: {result['success']}")
                if result['success']:
                    print(f"💬 Answer: {result['answer'][:200]}...")
                    
                    # Show the dual LLM workflow information
                    metadata = result['metadata']
                    print(f"\n🔧 Workflow Details:")
                    print(f"   Database: {metadata.get('database', 'N/A')}")
                    print(f"   Method: {metadata.get('method', 'N/A')}")
                    print(f"   Analysis Model: {metadata.get('analysis_model', 'N/A')}")
                    print(f"   Execution Model: {metadata.get('execution_model', 'N/A')}")
                    
                    if metadata.get('sql_query'):
                        print(f"   SQL Generated: {metadata['sql_query'][:100]}...")
                        print(f"   Rows Returned: {metadata.get('row_count', 0)}")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        # Step 5: Clean up
        print(f"\n🧹 Cleaning up...")
        agent.close()
        # Note: Don't close db_manager here in real usage - let the calling code manage it
        # db_manager.close()  # Commented out for this example
        
        print(f"\n" + "=" * 80)
        print("🎯 SESSION-BASED SQL AGENT INTEGRATION COMPLETE")
        print("   ✅ Works with your existing database.py architecture")
        print("   ✅ Each chat session gets its own PostgreSQL database")
        print("   ✅ GPT-4.1 handles query analysis and improvement")
        print("   ✅ GPT-4o-mini handles SQL generation and analysis")
        print("=" * 80)
        
    except ImportError as e:
        print(f"❌ Could not import database module: {e}")
        print("   Make sure your database.py module is available")
    except Exception as e:
        print(f"❌ Error in example: {e}")
        print("   This is expected if PostgreSQL is not set up or CSV data not loaded")
        
        # Show the basic usage pattern anyway
        print(f"\n📖 BASIC USAGE PATTERN (from your app4.py):")
        print(f"```python")
        print(f"# 1. Create database manager for session")
        print(f"db_manager = DuckDBManager(session_id, session['db_path'])")
        print(f"")
        print(f"# 2. Load CSV data into session database")
        print(f"db_manager.load_csv_data(clean_csv_path, error_csv_path)")
        print(f"")
        print(f"# 3. Create SQL agent with database manager")
        print(f"sql_agent = create_sql_agent(db_manager, session_id, 3, None, True)")
        print(f"")
        print(f"# 4. Process queries")
        print(f"result = sql_agent.process_query('What are the errors?')")
        print(f"```")