# Flight Data SQL Agent

A sophisticated SQL agent that converts natural language questions into SQL queries for flight operations data analysis, with automatic chunking, error handling, and iterative query refinement.

## 🚀 Features

- **Natural Language to SQL**: Converts plain English questions into DuckDB-compatible SQL queries
- **Automatic Chunking**: Handles large datasets by automatically chunking results to respect LLM context limits
- **Error Recovery**: Iterative query refinement with up to 3 retry attempts
- **Domain Expertise**: Specialized for flight operations data with aviation-specific knowledge
- **Context Management**: Intelligent token counting and context window optimization
- **Relevance Checking**: Filters out non-aviation questions automatically

## 🏗️ Architecture

The SQL Agent follows a sophisticated workflow:

1. **Relevance Check** - Determines if the question relates to flight data
2. **SQL Generation** - Converts natural language to DuckDB SQL
3. **Chunked Execution** - Executes queries with automatic pagination
4. **Error Handling** - Retries with improved queries if errors occur
5. **Answer Generation** - Creates human-readable responses from results

## 📋 Requirements

### System Requirements
- Python 3.8+
- Access to DuckDB HTTP server (default: `80.225.222.10:8080`)
- OpenAI API key for LLM functionality

### Python Dependencies
```bash
pip install -r requirements.txt
```

Key dependencies:
- `openai>=1.12.0` - For LLM functionality
- `requests>=2.25.0` - For DuckDB HTTP client
- `pydantic>=2.5.0` - For structured output
- `typing_extensions>=4.9.0` - For advanced typing

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in your project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=128000

# DuckDB Configuration (optional, defaults shown)
DUCKDB_HOST=80.225.222.10
DUCKDB_PORT=8080

# Application Settings
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
LOG_LEVEL=INFO
```

### DuckDB Server Setup
The SQL agent connects to a DuckDB HTTP server. Ensure your server is running:

```bash
# If running your own DuckDB server
duckdb --http-port 8080 your_database.db
```

Or use the community server at `80.225.222.10:8080` (default).

## 🚦 Quick Start

### Basic Usage

```python
from modules.sql_generator import create_sql_agent

# Initialize the agent
agent = create_sql_agent()

# Example table schemas (normally from database)
schemas = {
    "clean_flights": [
        {"column_name": "Date", "column_type": "VARCHAR"},
        {"column_name": "A/C Registration", "column_type": "VARCHAR"},
        {"column_name": "Flight", "column_type": "VARCHAR"},
        {"column_name": "Origin ICAO", "column_type": "VARCHAR"},
        {"column_name": "Destination ICAO", "column_type": "VARCHAR"},
        {"column_name": "Fuel Volume", "column_type": "DOUBLE"}
    ]
}

# Process a natural language query
result = agent.process_query(
    question="How many flights were there in total?",
    session_id="my_session_123",
    table_schemas=schemas
)

# Handle the response
if result["success"]:
    print(f"Answer: {result['answer']}")
    print(f"SQL Used: {result['metadata']['sql_query']}")
    print(f"Rows: {result['metadata']['total_rows']}")
else:
    print(f"Error: {result['answer']}")
```

### Example Queries

The SQL agent can handle various types of flight data questions:

```python
queries = [
    "How many flights were there in total?",
    "What is the average fuel consumption per flight?", 
    "Show me flights from KJFK to EGLL",
    "Which aircraft registration has the highest fuel usage?",
    "What are the most common error types in the data?",
    "Show me all flights on 01/01/2024"
]

for query in queries:
    result = agent.process_query(query, "session_1", schemas)
    print(f"Q: {query}")
    print(f"A: {result['answer']}\n")
```

## 🧪 Testing

### Run the Example Script
```bash
python sql_agent_example.py
```

This will:
1. Test connection to DuckDB server
2. Run example queries
3. Demonstrate key features
4. Show structured output

### Run Unit Tests
```bash
pytest tests/test_sql_agent.py -v
```

## 🔧 Advanced Configuration

### Custom Chunking
```python
# Adjust chunk size based on your data
agent = create_sql_agent()
agent.chunk_size = 500  # Smaller chunks for complex data
```

### Custom DuckDB Server
```python
from modules.sql_generator import DuckDBHTTPClient

# Custom server configuration
client = DuckDBHTTPClient(host="your-server.com", port=9000)
```

### Error Handling
```python
result = agent.process_query("your question", "session_id", schemas)

if not result["success"]:
    if "relevance" in result["metadata"]:
        print("Question not related to flight data")
    elif "attempts" in result["metadata"]:
        print(f"Failed after {result['metadata']['attempts']} attempts")
    else:
        print(f"General error: {result['answer']}")
```

## 📊 Output Format

### Successful Response
```json
{
    "success": true,
    "answer": "Based on the flight data, there were 15,432 total flights recorded...",
    "metadata": {
        "sql_query": "SELECT COUNT(*) as total_flights FROM clean_flights",
        "total_rows": 1,
        "chunks_processed": 1,
        "context_used": 245,
        "data_sample": [{"total_flights": 15432}]
    }
}
```

### Error Response
```json
{
    "success": false,
    "answer": "I can only help with questions about flight operations data...",
    "metadata": {
        "relevance": "not_relevant"
    }
}
```

## 🛠️ Troubleshooting

### Common Issues

**DuckDB Connection Failed**
```bash
# Check server status
curl http://80.225.222.10:8080/health

# Verify network connectivity
ping 80.225.222.10
```

**OpenAI API Errors**
- Verify API key in `.env` file
- Check API quota and billing
- Ensure model name is correct

**Context Window Exceeded**
- The agent automatically chunks data
- Reduce `chunk_size` if needed
- Check `context_used` in metadata

**SQL Generation Errors**
- Ensure table schemas are accurate
- Check column names match exactly
- Verify DuckDB syntax compatibility

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed workflow steps
result = agent.process_query(query, session_id, schemas)
```

## 🔒 Security Considerations

- **SQL Injection Protection**: Basic sanitization included
- **Query Limits**: Automatic LIMIT clauses prevent runaway queries
- **Error Boundaries**: Graceful handling of malformed inputs
- **API Key Security**: Store keys in environment variables only

## 🎯 Performance Tips

1. **Schema Optimization**: Provide accurate, minimal schemas
2. **Question Specificity**: More specific questions generate better SQL
3. **Chunk Size Tuning**: Adjust based on your data complexity
4. **Caching**: Consider implementing query result caching
5. **Batch Processing**: Group related questions in single sessions

## 📈 Monitoring

Track key metrics:
- Query success rate
- Average response time
- Context usage patterns
- Error frequency by type

```python
# Example monitoring
result = agent.process_query(query, session_id, schemas)
print(f"Context used: {result['metadata']['context_used']} tokens")
print(f"Chunks processed: {result['metadata']['chunks_processed']}")
```

## 🤝 Contributing

1. Follow the existing code structure
2. Add comprehensive docstrings
3. Include unit tests for new features
4. Update this README for new functionality

## 📄 License

This SQL agent is part of the Flight Data Analysis System.

---

**Need Help?** 
- Check the example script: `sql_agent_example.py`
- Review the test cases: `tests/test_sql_agent.py`
- Enable debug logging for detailed workflow traces 