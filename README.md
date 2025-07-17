# Vurdhaan Report Project

Flight data validation and CORSIA reporting system.

## New Features

### Automatic CSV Generation
The `generate_error_report()` function now automatically creates two CSV files alongside the JSON error report:

1. **`clean_data.csv`** - Contains all rows without validation errors
2. **`errors_data.csv`** - Contains only error rows with detailed error information

This happens automatically whenever error validation is performed.

## Usage

### Command Line Processing
```bash
# Process existing JSON error report
python process_errors.py path/to/error_report.json path/to/original_data.csv

# Test the functionality
python test_auto_csv_generation.py
```

### Programmatic Usage
```python
from helpers.clean import validate_and_process_file

# This will automatically generate clean_data.csv and errors_data.csv
is_valid, processed_path, validated_df, error_json_path = validate_and_process_file(
    file_path="data.csv",
    result_df=df,
    ref_df=reference_df
)
```

## Output Files

- `error_report.json` - Detailed error report in JSON format
- `clean_data.csv` - Clean data without validation errors  
- `errors_data.csv` - Error rows with metadata (category, reason, affected columns)


# Flight Operations SQL-First RAG Chatbot

A natural language interface for querying flight operations data using DuckDB and OpenAI GPT-4.

## Features

- **SQL-First RAG Architecture**: Converts natural language queries to SQL for precise data retrieval
- **DuckDB Integration**: High-performance in-process SQL database
- **Session Management**: Isolated database instances per chat session
- **Real-time Chat Interface**: Modern, responsive web interface
- **Automatic Schema Detection**: Intelligently parses CSV files
- **Error Handling**: Comprehensive validation and error recovery

## Quick Start

### Prerequisites

- Python 3.9+
- OpenAI API key
- CSV files with flight data

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd flight-ops-rag