import logging
import json
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import openai
from config import Config
from .database import DuckDBManager
from .sql_generator import SQLGenerator

logger = logging.getLogger(__name__)

class FlightOpsRAG:
    """Main RAG engine for flight operations queries"""
    
    def __init__(self, session_id: str, db_manager: DuckDBManager):
        self.session_id = session_id
        self.db_manager = db_manager
        self.sql_generator = SQLGenerator()
        self.conversation_history = []
        openai.api_key = Config.OPENAI_API_KEY
        
    def process_query(self, natural_query: str) -> Dict[str, Any]:
        """Process natural language query through SQL-first RAG pipeline"""
        
        try:
            # Step 1: Query Classification
            query_type = self._classify_query(natural_query)
            
            # Step 2: Get table schemas
            table_info = self.db_manager.get_table_info()
            table_schemas = {
                table: info['schema'] 
                for table, info in table_info.items()
            }
            
            # Step 3: Generate SQL
            sql_query, sql_metadata = self.sql_generator.generate_sql(
                natural_query, 
                table_schemas,
                context=self._get_conversation_context()
            )
            
            # Step 4: Validate SQL
            is_valid, validation_error = self.db_manager.validate_sql(sql_query)
            
            if not is_valid:
                # Try to fix the SQL
                sql_query = self._fix_sql_query(sql_query, validation_error, table_schemas)
                is_valid, validation_error = self.db_manager.validate_sql(sql_query)
                
                if not is_valid:
                    return self._create_error_response(
                        "I couldn't generate a valid query. Could you please rephrase your question?",
                        validation_error
                    )
            
            # Step 5: Execute query
            results, execution_error = self.db_manager.execute_query(sql_query)
            
            if execution_error:
                return self._create_error_response(
                    "There was an error executing the query.",
                    execution_error
                )
            
            # Step 6: Generate natural language response
            response = self._generate_response(
                natural_query,
                sql_query,
                results,
                sql_metadata
            )
            
            # Step 7: Update conversation history
            self._update_conversation_history(natural_query, sql_query, response)
            
            return {
                'status': 'success',
                'query': natural_query,
                'sql': sql_query,
                'results': results[:100] if len(results) > 100 else results,  # Limit results
                'result_count': len(results),
                'response': response,
                'metadata': {
                    'query_type': query_type,
                    'sql_metadata': sql_metadata,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            return self._create_error_response(
                "I encountered an unexpected error while processing your query.",
                str(e)
            )
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['sum', 'total', 'average', 'mean', 'count', 'max', 'min']):
            return 'aggregate'
        elif any(word in query_lower for word in ['compare', 'versus', 'vs', 'between']):
            return 'comparison'
        elif any(word in query_lower for word in ['trend', 'over time', 'pattern', 'analysis']):
            return 'analysis'
        else:
            return 'select'
    
    def _get_conversation_context(self) -> str:
        """Get relevant conversation context"""
        if not self.conversation_history:
            return ""
        
        # Get last 3 queries for context
        recent_queries = self.conversation_history[-3:]
        context = "Previous queries in this conversation:\n"
        
        for item in recent_queries:
            context += f"- {item['query']}\n"
        
        return context
    
    def _fix_sql_query(self, sql: str, error: str, table_schemas: Dict) -> str:
        """Attempt to fix SQL query based on error"""
        try:
            fix_prompt = f"""Fix this SQL query that has an error.

Original SQL:
{sql}

Error:
{error}

Available tables and columns:
{json.dumps(table_schemas, indent=2)}

Return only the corrected SQL query."""

            response = openai.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Fix SQL queries to be DuckDB compatible."},
                    {"role": "user", "content": fix_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            fixed_sql = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if fixed_sql.startswith("```"):
                fixed_sql = fixed_sql.split("```")[1].replace("sql", "").strip()
            
            return fixed_sql
            
        except Exception as e:
            logger.error(f"Failed to fix SQL: {e}")
            return sql
    
    def _generate_response(self, query: str, sql: str, results: List[Dict], sql_metadata: Dict) -> str:
        """Generate natural language response from query results"""
        
        # Handle empty results
        if not results:
            return "I couldn't find any data matching your query. Please try rephrasing or asking about different criteria."
        
        # Prepare results summary
        result_summary = self._summarize_results(results)
        
        prompt = f"""Generate a natural, conversational response to this query about flight operations.

User Query: {query}
SQL Query Type: {sql_metadata.get('query_type', 'select')}
Result Count: {len(results)}

Result Summary:
{result_summary}

Instructions:
1. Provide a clear, concise answer to the user's question
2. Include specific numbers and findings from the data
3. Highlight any interesting patterns or insights
4. Use aviation terminology appropriately
5. Format numbers for readability (e.g., thousands separators)
6. If showing a list, limit to top 5-10 items
7. Suggest related questions they might want to ask

Keep the response conversational and helpful."""

        try:
            response = openai.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful flight operations data analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return f"I found {len(results)} results for your query. The data shows {result_summary}"
    
    def _summarize_results(self, results: List[Dict]) -> str:
        """Create a summary of query results"""
        if not results:
            return "No results found"
        
        # For large result sets, summarize
        if len(results) > 10:
            summary = f"Found {len(results)} total results. "
            summary += f"Showing first 10:\n{json.dumps(results[:10], indent=2, default=str)}"
        else:
            summary = json.dumps(results, indent=2, default=str)
        
        return summary
    
    def _update_conversation_history(self, query: str, sql: str, response: str):
        """Update conversation history"""
        self.conversation_history.append({
            'query': query,
            'sql': sql,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 10 queries
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def _create_error_response(self, user_message: str, error_details: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'status': 'error',
            'response': user_message,
            'error': error_details,
            'timestamp': datetime.now().isoformat()
        }