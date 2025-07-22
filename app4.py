"""
Unified Flight Data Analysis Application

Combines CSV validation, error handling, CORSIA reporting, and natural language
chat interface with SQL agent for comprehensive flight data analysis.

Features:
- CSV upload and validation
- Error detection and reporting
- CORSIA report generation  
- Natural language chat interface with SQL agent
- Session management for chat and file processing
- Automatic CSV generation (clean_data.csv, errors_data.csv)
- All print statements logged to file
"""

import sys
import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from flask_cors import CORS
import uuid
from datetime import datetime
import pandas as pd
import shutil
from werkzeug.utils import secure_filename
import chardet
import traceback
import brotli
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Import configurations
from config import Config

# Import modules for chat functionality
from modules.session_manager import SessionManager
from modules.database import DuckDBManager
from modules.sql_generator import create_sql_agent
from modules.utils import setup_logging, validate_csv_file, format_query_results

# Import existing helpers for validation and reporting
from helpers.clean import validate_and_process_file, safe_json_load, create_compressed_error_report
from helpers.corsia import build_report

# ============================================================================
# LOGGING SETUP - Redirect all print statements to log file
# ============================================================================

class PrintLogger:
    """Custom logger to capture all print statements"""
    
    def __init__(self, log_file_path='app.log'):
        self.log_file_path = log_file_path
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Setup logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, mode='a', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)  # Also keep console output
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def write(self, message):
        """Write method for stdout/stderr redirection"""
        if message.strip():  # Only log non-empty messages
            self.logger.info(message.strip())
        
        # Also write to original stdout for console visibility
        self.original_stdout.write(message)
        self.original_stdout.flush()
    
    def flush(self):
        """Flush method for stdout/stderr redirection"""
        self.original_stdout.flush()
    
    def start_logging(self):
        """Start capturing print statements"""
        sys.stdout = self
        sys.stderr = self
        self.logger.info("="*50)
        self.logger.info("APPLICATION STARTED")
        self.logger.info("="*50)
    
    def stop_logging(self):
        """Stop capturing print statements"""
        self.logger.info("="*50)
        self.logger.info("APPLICATION STOPPED")
        self.logger.info("="*50)
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Initialize print logger
print_logger = PrintLogger('logs/flight_data_app.log')
print_logger.start_logging()

# Force all print statements to go through our logger
import builtins
original_print = builtins.print

# Setup logging (disable other loggers to avoid conflicts)
logging.getLogger('werkzeug').disabled = True
logging.getLogger('apscheduler').disabled = True

# Custom print function that ensures logging
def log_print(*args, **kwargs):
    """Custom print function that ensures logging"""
    message = ' '.join(str(arg) for arg in args)
    print_logger.logger.info(message)

# Replace print with our custom function throughout the app
# (You can use log_print() instead of print() for explicit logging)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # Enable CORS for all routes

# Enable detailed error messages
app.config['PROPAGATE_EXCEPTIONS'] = True

# Configuration for file uploads
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Store file metadata in memory (in production, use a database)
file_metadata = {}

# Initialize session manager for chat functionality
session_manager = SessionManager()

# Setup scheduler for cleanup
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=session_manager.cleanup_expired_sessions,
    trigger="interval",
    hours=1,
    id='cleanup_sessions',
    name='Clean up expired sessions',
    replace_existing=True
)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
atexit.register(lambda: print_logger.stop_logging())

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def detect_encoding(file_path):
    """Detect file encoding with better handling"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            
        encoding = result['encoding']
        confidence = result['confidence']
        
        print(f"Detected encoding: {encoding} (confidence: {confidence}) for file: {file_path}")
        
        # If confidence is low, fallback to common encodings
        if confidence < 0.7:
            print(f"Low confidence encoding detection, trying fallback encodings...")
            for fallback_encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=fallback_encoding) as f:
                        f.read()
                    print(f"Successfully using fallback encoding: {fallback_encoding}")
                    return fallback_encoding
                except UnicodeDecodeError:
                    continue
        
        return encoding if encoding else 'utf-8'
    except Exception as e:
        print(f"Error detecting encoding for {file_path}: {e}")
        return 'utf-8'

def cleanup_old_uploads():
    """Remove uploads older than 24 hours"""
    import time
    current_time = time.time()
    
    print(f"Starting cleanup of old uploads...")
    
    for file_id in list(file_metadata.keys()):
        folder = file_metadata[file_id]['folder']
        metadata_path = os.path.join(folder, 'metadata.json')
        
        if os.path.exists(metadata_path):
            # Check file age
            file_age = current_time - os.path.getmtime(metadata_path)
            if file_age > 86400:  # 24 hours
                print(f"Cleaning up old upload: {file_id} (age: {file_age/3600:.1f} hours)")
                # Remove folder and metadata
                shutil.rmtree(folder, ignore_errors=True)
                del file_metadata[file_id]
    
    print(f"Cleanup completed. Remaining uploads: {len(file_metadata)}")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    print(f"404 Error: {error}")
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def handle_500_error(e):
    error_details = {
        'error': str(e),
        'traceback': traceback.format_exc()
    }
    print(f"500 Error: {error_details}")
    return jsonify(error_details), 500

# ============================================================================
# MAIN ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main validation interface"""
    print("Serving main validation interface")
    return render_template('index4.html')

@app.route('/chat')
def chat_interface():
    """Serve the chat interface"""
    print("Serving chat interface")
    return render_template('chat.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files"""
    print(f"Serving static file: {path}")
    return send_from_directory('static', path)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    print("Health check requested")
    stats = session_manager.get_session_stats()
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'session_stats': stats,
        'file_metadata_count': len(file_metadata)
    }), 200

# ============================================================================
# FILE UPLOAD AND VALIDATION ROUTES (from app2.py)
# ============================================================================

@app.route('/upload', methods=['POST'])
def upload_csv():
    """Handle CSV file upload and initial validation"""
    print("Starting CSV upload and validation process")
    
    try:
        # Check if file is present
        if 'file' not in request.files:
            print("Error: No file provided in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            print("Error: No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension
        if not file.filename.lower().endswith('.csv'):
            print(f"Error: Invalid file type. File: {file.filename}")
            return jsonify({'error': 'Only CSV files are allowed'}), 400
        
        print(f"Processing uploaded file: {file.filename}")
        
        # Get validation parameters
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        date_format = request.form.get('date_format', 'DMY')
        flight_starts_with = request.form.get('flight_starts_with', '')
        
        print(f"Validation parameters - Start: {start_date}, End: {end_date}, Format: {date_format}, Flight prefix: {flight_starts_with}")
        
        # Convert date strings to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Create unique folder for this upload
        file_id = str(uuid.uuid4())
        file_folder = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        os.makedirs(file_folder, exist_ok=True)
        
        print(f"Created upload folder: {file_folder} with ID: {file_id}")
        
        # Save uploaded file
        original_path = os.path.join(file_folder, 'original.csv')
        file.save(original_path)
        print(f"Saved original file to: {original_path}")
        
        # Detect encoding
        encoding = detect_encoding(original_path)
        
        # Load CSV
        print(f"Loading CSV with encoding: {encoding}")
        result_df = pd.read_csv(original_path, encoding=encoding, encoding_errors='replace')
        print(f"Loaded CSV with {len(result_df)} rows and {len(result_df.columns)} columns")
        
        # Load reference data
        ref_csv_path = os.path.join(os.getcwd(), 'airports.csv')
        ref_encoding = detect_encoding(ref_csv_path)
        ref_df = pd.read_csv(ref_csv_path, encoding=ref_encoding, encoding_errors='replace')
        print(f"Loaded reference data with {len(ref_df)} rows")
        
        # Run validation
        print("Starting validation process...")
        is_valid, processed_path, validated_df, error_json_path = validate_and_process_file(
            file_path=original_path,
            result_df=result_df,
            ref_df=ref_df,
            date_format=date_format,
            flight_starts_with=flight_starts_with,
            start_date=start_date,
            end_date=end_date
        )
        
        # Store metadata
        file_metadata[file_id] = {
            'folder': file_folder,
            'original_path': original_path,
            'start_date': start_date,
            'end_date': end_date,
            'date_format': date_format,
            'flight_starts_with': flight_starts_with,
            'upload_time': datetime.now().isoformat(),
            'is_valid': is_valid,
            'processed_path': processed_path,
            'error_json_path': error_json_path,
            'filename': file.filename
        }
        
        # Save metadata to file
        metadata_path = os.path.join(file_folder, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(file_metadata[file_id], f, default=str, ensure_ascii=False)

        print(f"File uploaded and validated - ID: {file_id}, Valid: {is_valid}")
        
        # Return response
        return jsonify({
            'file_id': file_id,
            'is_valid': is_valid,
            'filename': file.filename
        }), 200
        
    except Exception as e:
        print(f"Upload failed with error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/errors/<file_id>', methods=['GET'])
def get_errors(file_id):
    """Return compressed error JSON for a file"""
    print(f"Getting errors for file ID: {file_id}")
    
    try:
        # Check if file exists
        if file_id not in file_metadata:
            print(f"File ID not found: {file_id}")
            return jsonify({'error': 'File not found'}), 404
        
        # Get paths
        file_folder = file_metadata[file_id]['folder']
        compressed_path = os.path.join(file_folder, 'error_report.lzs')
        error_json_path = file_metadata[file_id].get('error_json_path')
        
        print(f"Looking for compressed error report at: {compressed_path}")
        print(f"Original error JSON at: {error_json_path}")
        
        # Check if compressed file exists
        if os.path.exists(compressed_path):
            print("Serving existing compressed error report")
            # Serve existing compressed file
            with open(compressed_path, 'r', encoding='utf-8') as f:
                compressed_data = f.read()
            
            return Response(
                compressed_data,
                headers={
                    'Content-Type': 'text/plain',
                    'X-Compression': 'lzstring',
                    'Cache-Control': 'no-cache'
                }
            )
        
        # If compressed file doesn't exist but original JSON does, create compressed version
        if error_json_path and os.path.exists(error_json_path):
            print("Creating compressed error report from original JSON")
            # Load original error data
            error_data = safe_json_load(error_json_path)
            if error_data:
                try:
                    # Field mappings (same as in helper)
                    field_map = {
                        "Date": "d", "A/C Registration": "r", "Flight": "f", "A/C Type": "t",
                        "ATD (UTC) Block out": "o", "ATA (UTC) Block in": "i", 
                        "Origin ICAO": "or", "Destination ICAO": "de", "Uplift Volume": "uv",
                        "Uplift Density": "ud", "Uplift weight": "uw", 
                        "Remaining Fuel From Prev. Flight": "rf", "Block off Fuel": "bf",
                        "Block on Fuel": "bo", "Fuel Type": "ft"
                    }
                    reverse_field_map = {v: k for k, v in field_map.items()}
                    
                    compressed_data = create_compressed_error_report(error_data, field_map, reverse_field_map)
                    
                    # Save compressed file for future use
                    with open(compressed_path, 'w', encoding='utf-8') as f:
                        f.write(compressed_data)
                    
                    print("Successfully created and saved compressed error report")
                    
                    return Response(
                        compressed_data,
                        headers={
                            'Content-Type': 'text/plain',
                            'X-Compression': 'lzstring',
                            'Cache-Control': 'no-cache'
                        }
                    )
                except Exception as e:
                    print(f"Failed to compress error data: {e}")
        
        # Fallback: return empty error structure
        print("Returning empty error structure as fallback")
        empty_error_data = {
            'summary': {'total_errors': 0, 'error_rows': 0, 'categories': {}},
            'rows_data': {},
            'categories': []
        }
        
        return jsonify(empty_error_data), 200
        
    except Exception as e:
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(f"Error in get_errors: {error_details}")
        return jsonify(error_details), 500

@app.route('/upload/<file_id>', methods=['PUT'])
def update_csv(file_id):
    """Handle CSV corrections and re-validation"""
    print(f"Updating CSV for file ID: {file_id}")
    
    try:
        # Check if file exists
        if file_id not in file_metadata:
            print(f"File ID not found: {file_id}")
            return jsonify({'error': 'File not found'}), 404
        
        data = request.get_json()
        
        # Check if ignoring errors
        if data.get('ignore_errors'):
            print("Ignoring errors for file")
            file_metadata[file_id]['errors_ignored'] = True
            return jsonify({'success': True, 'message': 'Errors ignored'}), 200
        
        # Check if re-validating
        if data.get('revalidate'):
            print("Re-validating file")
            return rerun_validation(file_id)
        
        # Handle corrections
        corrections = data.get('corrections', [])
        if not corrections:
            print("No corrections provided")
            return jsonify({'error': 'No corrections provided'}), 400
        
        print(f"Processing {len(corrections)} corrections")
        
        # Load the current CSV
        file_path = file_metadata[file_id]['original_path']
        encoding = detect_encoding(file_path)
        df = pd.read_csv(file_path, encoding=encoding, encoding_errors='replace')
        
        # Apply corrections
        for i, correction in enumerate(corrections):
            row_idx = correction.get('row')
            column = correction.get('column')
            new_value = correction.get('new_value')
            
            print(f"Applying correction {i+1}/{len(corrections)}: Row {row_idx}, Column {column}, New value: {new_value}")
            
            if row_idx is not None and column and row_idx < len(df):
                # Convert row_idx to integer if it's a string
                if isinstance(row_idx, str):
                    row_idx = int(row_idx)
                
                # Handle data type conversion properly
                if column in df.columns:
                    current_dtype = df[column].dtype
                    
                    try:
                        if pd.api.types.is_numeric_dtype(current_dtype):
                            if new_value == '' or new_value is None:
                                if pd.api.types.is_integer_dtype(current_dtype):
                                    new_value = pd.NA
                                else:
                                    new_value = float('nan')
                            else:
                                if pd.api.types.is_integer_dtype(current_dtype):
                                    new_value = int(float(new_value))
                                else:
                                    new_value = float(new_value)
                        else:
                            new_value = str(new_value) if new_value is not None else ''
                    
                    except (ValueError, TypeError) as e:
                        print(f"Could not convert '{new_value}' to {current_dtype}, using string: {e}")
                        new_value = str(new_value) if new_value is not None else ''
                
                df.at[row_idx, column] = new_value
        
        # Save corrected CSV
        corrected_path = os.path.join(file_metadata[file_id]['folder'], 'corrected.csv')
        df.to_csv(corrected_path, index=False, encoding='utf-8')
        print(f"Saved corrected CSV to: {corrected_path}")
        
        # Update metadata
        file_metadata[file_id]['original_path'] = corrected_path
        
        # Re-run validation
        print("Re-running validation on corrected file")
        return rerun_validation(file_id)
        
    except Exception as e:
        print(f"CSV update failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

def rerun_validation(file_id):
    """Re-run validation on a file"""
    print(f"Re-running validation for file ID: {file_id}")
    
    try:
        metadata = file_metadata[file_id]
        
        # Load CSV
        file_path = metadata['original_path']
        encoding = detect_encoding(file_path)
        result_df = pd.read_csv(file_path, encoding=encoding, encoding_errors='replace')
        
        # Load reference data
        ref_csv_path = os.path.join(os.getcwd(), 'airports.csv')
        ref_encoding = detect_encoding(ref_csv_path)
        ref_df = pd.read_csv(ref_csv_path, encoding=ref_encoding, encoding_errors='replace')
        
        # Run validation
        is_valid, processed_path, validated_df, error_json_path = validate_and_process_file(
            file_path=file_path,
            result_df=result_df,
            ref_df=ref_df,
            date_format=metadata['date_format'],
            flight_starts_with=metadata['flight_starts_with'],
            start_date=metadata['start_date'],
            end_date=metadata['end_date']
        )
        
        # Update metadata
        file_metadata[file_id]['is_valid'] = is_valid
        file_metadata[file_id]['processed_path'] = processed_path
        file_metadata[file_id]['error_json_path'] = error_json_path
        
        # Clear any existing compressed file to force regeneration
        file_folder = metadata['folder']
        compressed_path = os.path.join(file_folder, 'error_report.lzs')
        if os.path.exists(compressed_path):
            os.remove(compressed_path)
            print("Removed existing compressed error report")
        
        print(f"Re-validation completed for {file_id}: valid={is_valid}")
        
        return jsonify({
            'success': True,
            'is_valid': is_valid
        }), 200
        
    except Exception as e:
        print(f"Re-validation failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/report/<file_id>', methods=['POST'])
def build_report_endpoint(file_id):
    """Generate CORSIA report"""
    print(f"Building report for file ID: {file_id}")
    
    try:
        # Check if file exists
        if file_id not in file_metadata:
            print(f"File ID not found: {file_id}")
            return jsonify({'error': 'File not found'}), 404
        
        metadata = file_metadata[file_id]
        
        # Check if file is valid or errors were ignored
        if not metadata.get('is_valid') and not metadata.get('errors_ignored'):
            print("Cannot generate report - file has unresolved errors")
            return jsonify({'error': 'Cannot generate report - file has unresolved errors'}), 400
        
        # Get processed CSV path
        processed_path = metadata.get('processed_path')
        flight_starts_with = metadata.get('flight_starts_with')
        if not processed_path or not os.path.exists(processed_path):
            # Use original if processed doesn't exist
            processed_path = metadata['original_path']
        
        print(f"Using processed file: {processed_path}")
        print(f"Flight starts with: {flight_starts_with}")
        
        # Define output path for Excel report
        output_path = os.path.join(metadata['folder'], 'template_filled.xlsx')
        
        try:
            # Call build_report function
            print("Calling build_report function...")
            build_report(processed_path, flight_starts_with)
            print("Report generation completed successfully")
        except Exception as e:
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            print(f"Error in build_report: {error_details}")
            return jsonify(error_details), 500
        
        # Send file to client
        print(f"Sending report file: {output_path}")
        return send_file(
            output_path,
            as_attachment=True,
            download_name='template_filled.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(f"Error in build_report_endpoint: {error_details}")
        return jsonify(error_details), 500

# ============================================================================
# CHAT AND SQL AGENT ROUTES (from app3.py + SQL agent integration)
# ============================================================================

@app.route('/chat/initialize', methods=['POST'])
def initialize_chat_session():
    """Initialize new chat session with DuckDB and CSV data"""
    print(f"🏗️ [DEBUG] Session Creation → initialize_chat_session called with data: {request.get_json()}")
    sys.stdout.flush()
    
    try:
        data = request.get_json()
        
        # Support both direct file paths and file_id-based initialization
        if 'file_id' in data:
            
            # Initialize from existing file validation
            file_id = data['file_id']
            print(f"📂 [DEBUG] Session Creation → Using file_id initialization: {file_id}")
            sys.stdout.flush()
            
            if file_id not in file_metadata:
                print(f"❌ [ERROR] File ID not found: {file_id}")
                return jsonify({'error': 'File ID not found'}), 404
            
            metadata = file_metadata[file_id]
            file_folder = metadata['folder']
            print(f"📁 [DEBUG] Session Creation → File folder located: {file_folder}")
            sys.stdout.flush()
            
            # Look for auto-generated CSV files
            clean_csv = os.path.join(file_folder, 'clean_data.csv')
            error_csv = os.path.join(file_folder, 'errors_data.csv')
            print(f"📊 [DEBUG] Data Loading → Looking for CSV files:")
            sys.stdout.flush()
            print(f"📊 [DEBUG] Data Loading → Clean CSV: {clean_csv}")
            sys.stdout.flush()
            print(f"📊 [DEBUG] Data Loading → Error CSV: {error_csv}")
            sys.stdout.flush()
            
            # If auto-generated files don't exist, try to create them
            if not os.path.exists(clean_csv) or not os.path.exists(error_csv):
                print("📊 [DEBUG] Auto-generated CSV files not found, attempting to create them...")
                
                # Try to regenerate from existing error JSON
                error_json_path = metadata.get('error_json_path')
                if error_json_path and os.path.exists(error_json_path):
                    print(f"📊 [DEBUG] Using error JSON: {error_json_path}")
                    from helpers.clean import process_error_json_to_csvs
                    
                    # Load original data
                    original_path = metadata['original_path']
                    encoding = detect_encoding(original_path)
                    original_df = pd.read_csv(original_path, encoding=encoding, encoding_errors='replace')
                    
                    # Generate CSVs
                    clean_csv, error_csv = process_error_json_to_csvs(
                        error_json_path, original_df, file_folder
                    )
                    print(f"📊 [DEBUG] Generated CSV files: clean={clean_csv}, error={error_csv}")
                else:
                    print("❌ [ERROR] No error data available to generate CSV files")
                    return jsonify({'error': 'No error data available to generate CSV files'}), 400
            
            # Validate CSV files exist
            if not os.path.exists(clean_csv):
                print(f"❌ [ERROR] Clean CSV file not found: {clean_csv}")
                return jsonify({'error': f'Clean CSV file not found: {clean_csv}'}), 400
            if not os.path.exists(error_csv):
                print(f"❌ [ERROR] Error CSV file not found: {error_csv}")
                return jsonify({'error': f'Error CSV file not found: {error_csv}'}), 400
                
        else:
            # Direct initialization with file paths
            print("📂 [DEBUG] Session Creation → Using direct file path initialization")
            required_fields = ['clean_data_csv', 'error_data_csv']
            for field in required_fields:
                if field not in data:
                    print(f"❌ [ERROR] Missing required field: {field}")
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            clean_csv = data['clean_data_csv']
            error_csv = data['error_data_csv']
            print(f"📊 [DEBUG] Using provided CSV paths: clean={clean_csv}, error={error_csv}")
        
        # Validate CSV files
        print("🔍 [DEBUG] Validating CSV files...")
        is_valid, message = validate_csv_file(clean_csv)
        if not is_valid:
            print(f"❌ [ERROR] Clean CSV validation failed: {message}")
            return jsonify({'error': f'Clean CSV validation failed: {message}'}), 400
        
        is_valid, message = validate_csv_file(error_csv)
        if not is_valid:
            print(f"❌ [ERROR] Error CSV validation failed: {message}")
            return jsonify({'error': f'Error CSV validation failed: {message}'}), 400
        
        print("✅ [DEBUG] CSV validation successful")
        
        # Create session - use file_id as session_id if specified
        if data.get('use_file_id_as_session_id') and 'file_id' in data:
            session_id = data['file_id']  # Use file_id as session_id
            print(f"🆔 [DEBUG] Using file_id as session_id: {session_id}")
            session_id, session_data = session_manager.create_session_with_id(session_id, clean_csv, error_csv)
        else:
            print("🆔 [DEBUG] Creating new session with generated ID")
            session_id, session_data = session_manager.create_session(clean_csv, error_csv)
        
        print(f"🎯 [DEBUG] Session created: {session_id}")
        
        # Initialize DuckDB
        try:
            print("🗄️ [DEBUG] Initializing DuckDB...")
            db_manager = DuckDBManager(session_id, session_data['db_path'])
            
            # Load CSV data
            print("📥 [DEBUG] Loading CSV data into DuckDB...")
            load_result = db_manager.load_csv_data(clean_csv, error_csv)
            print(f"📥 [DEBUG] CSV data loaded: {load_result}")
            
            # Update session status
            session_manager.update_session(session_id, {
                'status': 'active',
                'database_info': load_result,
                'file_id': data.get('file_id')  # Store file_id if provided
            })
            
            # Close DB connection (will be reopened for each query)
            db_manager.close()
            
            print(f"✅ [SUCCESS] Chat session initialized: {session_id} with {load_result}")
            
            return jsonify({
                'session_id': session_id,
                'status': 'initialized',
                'database_info': load_result,
                'expires_at': session_data['expires_at']
            }), 200
            
        except Exception as e:
            # Clean up on failure
            print(f"❌ [ERROR] Database initialization failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            session_manager.delete_session(session_id)
            return jsonify({'error': f'Database initialization failed: {str(e)}'}), 500
        
    except Exception as e:
        print(f"❌ [ERROR] Failed to initialize chat session: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat/<session_id>/query', methods=['POST'])
def process_chat_query(session_id):
    """Process natural language query via SQL agent"""
    print(f"🤖 [CHAT] Processing query for session: {session_id}")
    try:
        # Validate session
        session = session_manager.get_session(session_id)
        if not session:
            print(f"❌ [ERROR] Invalid or expired session: {session_id}")
            return jsonify({'error': 'Invalid or expired session'}), 404
        # Get query from request
        data = request.get_json()
        query = data.get('query', '').strip()
        if not query:
            print("❌ [ERROR] No query provided")
            return jsonify({'error': 'No query provided'}), 400
        print(f"🔍 [CHAT] Processing query: '{query}'")
        # Initialize database connection
        db_manager = DuckDBManager(session_id, session['db_path'])
        # Get table schemas for SQL agent
        print("🗄️ [CHAT] Getting table schemas...")
        table_schemas = db_manager.get_table_info()
        print(f"📊 [CHAT] Available tables: {list(table_schemas.keys())}")
        # Initialize SQL agent
        print("🤖 [CHAT] Initializing SQL agent...")
        sql_agent = create_sql_agent(db_manager, session_id, 3, None, True)
        # Process query through SQL agent
        print("⚡ [CHAT] Processing query through SQL agent...")
        agent_result = sql_agent.process_query(query)
        # Update session
        session_manager.update_session(session_id, {
            'message_count': session.get('message_count', 0) + 1,
            'last_query': query
        })
        # Format results for response
        if agent_result['success']:
            print("✅ [CHAT] Query processed successfully")
            result = {
                'status': 'success',
                'response': agent_result['answer'],
                'sql_query': agent_result['metadata'].get('sql_query'),
                'total_rows': agent_result.get('metadata', {}).get('row_count', 0)
            }
            # Handle table data separately
            if 'table_rows' in agent_result and agent_result['table_rows']:
                result['table_data'] = agent_result['table_rows']
                result['total_rows'] = len(agent_result['table_rows'])
                print(f"📊 [CHAT] Sending {len(agent_result['table_rows'])} data rows")
        else:
            print(f"❌ [CHAT] Query processing failed: {agent_result.get('error', 'Unknown error')}")
            result = {
                'status': 'error',
                'response': agent_result['answer'],
                'error': agent_result.get('error', 'Query processing failed')
            }
        # Close database connection
        db_manager.close()
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ [ERROR] Failed to process query: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'response': 'I encountered an error processing your query. Please try again.'
        }), 500

@app.route('/chat/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    """Get session status and database info"""
    print(f"📊 [STATUS] Getting status for session: {session_id}")
    
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            print(f"❌ [ERROR] Session not found: {session_id}")
            return jsonify({'error': 'Session not found'}), 404
        
        status_info = {
            'session_id': session_id,
            'status': session.get('status', 'unknown'),
            'created_at': session.get('created_at'),
            'expires_at': session.get('expires_at'),
            'message_count': session.get('message_count', 0),
            'database_info': session.get('database_info', {}),
            'file_id': session.get('file_id')
        }
        
        print(f"✅ [STATUS] Session status retrieved: {status_info}")
        return jsonify(status_info), 200
        
    except Exception as e:
        print(f"❌ [ERROR] Failed to get session status: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat/<session_id>/export', methods=['GET'])
def export_session(session_id):
    """Export session conversation history"""
    print(f"📤 [EXPORT] Exporting session: {session_id}")
    
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            print(f"❌ [ERROR] Session not found: {session_id}")
            return jsonify({'error': 'Session not found'}), 404
        
        # Create export data
        export_data = {
            'session_id': session_id,
            'created_at': session.get('created_at'),
            'exported_at': datetime.now().isoformat(),
            'database_info': session.get('database_info', {}),
            'message_count': session.get('message_count', 0),
            'file_id': session.get('file_id')
        }
        
        print(f"✅ [EXPORT] Session exported successfully")
        return jsonify(export_data), 200
        
    except Exception as e:
        print(f"❌ [ERROR] Failed to export session: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# INTEGRATION ROUTE: OPEN CHAT FROM VALIDATION
# ============================================================================

@app.route('/open-chat/<file_id>', methods=['POST'])
def open_chat_from_validation(file_id):
    """Create a chat session from validation results"""
    print(f"🔄 [INTEGRATION] Opening chat from validation file: {file_id}")
    
    try:
        # Check if file exists
        if file_id not in file_metadata:
            print(f"❌ [ERROR] File not found: {file_id}")
            return jsonify({'error': 'File not found'}), 404
        
        # Initialize chat session with the file data, using file_id as session_id
        chat_init_data = {'file_id': file_id, 'use_file_id_as_session_id': True}
        
        print(f"🏗️ [INTEGRATION] Initializing chat session with data: {chat_init_data}")
        
        # Call the chat initialization endpoint internally
        with app.test_request_context('/chat/initialize', method='POST', json=chat_init_data):
            response = initialize_chat_session()
            
            if response[1] == 200:  # Success
                result = response[0].get_json()
                print(f"✅ [SUCCESS] Opened chat session from validation file {file_id}: {result['session_id']}")
                return jsonify({
                    'success': True,
                    'session_id': result['session_id'],
                    'chat_url': f'/chat?session_id={result["session_id"]}'
                }), 200
            else:
                # Forward the error response
                print(f"❌ [ERROR] Failed to initialize chat session: {response}")
                return response
        
    except Exception as e:
        print(f"❌ [ERROR] Failed to open chat from validation: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ADDITIONAL LOGGING ROUTES
# ============================================================================

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get recent log entries"""
    print("📋 [LOGS] Getting recent log entries")
    
    try:
        log_file_path = 'logs/flight_data_app.log'
        if not os.path.exists(log_file_path):
            print(f"❌ [ERROR] Log file not found: {log_file_path}")
            return jsonify({'error': 'Log file not found'}), 404
        
        # Get last 100 lines
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-100:]  # Last 100 lines
        
        print(f"📋 [LOGS] Retrieved {len(recent_lines)} recent log entries")
        return jsonify({
            'logs': recent_lines,
            'total_lines': len(lines),
            'recent_lines': len(recent_lines)
        }), 200
        
    except Exception as e:
        print(f"❌ [ERROR] Failed to get logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logs/clear', methods=['POST'])
def clear_logs():
    """Clear log file"""
    print("🧹 [LOGS] Clearing log file")
    
    try:
        log_file_path = 'logs/flight_data_app.log'
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write('')
        
        print("✅ [LOGS] Log file cleared successfully")
        return jsonify({'message': 'Log file cleared'}), 200
        
    except Exception as e:
        print(f"❌ [ERROR] Failed to clear logs: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# STARTUP AND CLEANUP
# ============================================================================

if __name__ == '__main__':
    # Run cleanup on startup
    print("🚀 Starting Unified Flight Data Analysis Application")
    print("🧹 Running startup cleanup...")
    cleanup_old_uploads()
    
    print("✅ Application startup complete")
    print("="*50)
    
    # Start Flask app
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=Config.FLASK_ENV == 'development',
            use_reloader=False
        )
    except Exception as e:
        print(f"❌ [CRITICAL] Application failed to start: {e}")
        print(f"Traceback: {traceback.format_exc()}")
    finally:
        print("🛑 Application shutting down...")
        print_logger.stop_logging()