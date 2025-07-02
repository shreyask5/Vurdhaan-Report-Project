from flask import Flask, request, jsonify, send_file, render_template, Response
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
import pandas as pd
import shutil
from werkzeug.utils import secure_filename
import chardet
import traceback
import brotli

# Import your helper functions (adjust path as needed)
from helpers.clean import validate_and_process_file
from helpers.corsia import build_report

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Enable detailed error messages
app.config['PROPAGATE_EXCEPTIONS'] = True

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Store file metadata in memory (in production, use a database)
file_metadata = {}

# Add error handler
@app.errorhandler(500)
def handle_500_error(e):
    error_details = {
        'error': str(e),
        'traceback': traceback.format_exc()
    }
    app.logger.error(f"500 error: {error_details}")
    return jsonify(error_details), 500


@app.route('/')
def index():
    return render_template('index4.html')


def detect_encoding(file_path):
    """Detect file encoding with better handling"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            
        encoding = result['encoding']
        confidence = result['confidence']
        
        # If confidence is low, fallback to common encodings
        if confidence < 0.7:
            for fallback_encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=fallback_encoding) as f:
                        f.read()
                    return fallback_encoding
                except UnicodeDecodeError:
                    continue
        
        return encoding if encoding else 'utf-8'
    except Exception:
        return 'utf-8'


def safe_json_load(file_path):
    """Safely load JSON file with proper encoding detection"""
    if not os.path.exists(file_path):
        return None
    
    # For JSON files, try common encodings
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    
    # If all fail, try detecting encoding
    detected_encoding = detect_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=detected_encoding) as f:
            return json.load(f)
    except Exception as e:
        app.logger.error(f"Failed to load JSON file {file_path}: {e}")
        return None


def parse_validation_errors(error_json_path):
    """Parse the JSON error file into the format expected by frontend"""
    error_data = safe_json_load(error_json_path)
    if not error_data:
        return []
    
    errors = []
    
    # Parse categories
    for category in error_data.get('categories', []):
        category_name = category.get('name', 'Other')
        
        for error_group in category.get('errors', []):
            reason = error_group.get('reason', '')
            
            for row_error in error_group.get('rows', []):
                if row_error.get('file_level'):
                    # File-level error
                    errors.append({
                        'row': 'File',
                        'column': ', '.join(row_error.get('columns', [])),
                        'value': str(row_error.get('cell_data', '')) if row_error.get('cell_data', '') is not None else '',
                        'message': reason,
                        'category': category_name
                    })
                else:
                    # Row-level error
                    row_idx = row_error.get('row_idx', 0)
                    columns = row_error.get('columns', [])
                    cell_data = row_error.get('cell_data', '')
                    
                    for column in columns:
                        errors.append({
                            'row': row_idx,
                            'column': column,
                            'value': str(cell_data) if cell_data is not None else '',
                            'message': reason,
                            'category': category_name
                        })
    
    return errors


@app.route('/upload', methods=['POST'])
def upload_csv():
    """Handle CSV file upload and initial validation"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file extension
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'Only CSV files are allowed'}), 400
        
        # Get validation parameters
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        date_format = request.form.get('date_format', 'DMY')
        flight_starts_with = request.form.get('flight_starts_with', '')
        
        # Convert date strings to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Create unique folder for this upload
        file_id = str(uuid.uuid4())
        file_folder = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        os.makedirs(file_folder, exist_ok=True)
        
        # Save uploaded file
        original_path = os.path.join(file_folder, 'original.csv')
        file.save(original_path)
        
        # Detect encoding
        encoding = detect_encoding(original_path)
        
        # Load CSV
        result_df = pd.read_csv(original_path, encoding=encoding, encoding_errors='replace')
        
        # Load reference data (adjust path as needed)
        ref_csv_path = os.path.join(os.getcwd(), 'airports.csv')
        ref_encoding = detect_encoding(ref_csv_path)
        ref_df = pd.read_csv(ref_csv_path, encoding=ref_encoding, encoding_errors='replace')
        
        # Run validation
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
            'is_valid' : is_valid,
            'processed_path' : processed_path,
            'error_json_path' : error_json_path
        }
        
        # Save metadata to file
        metadata_path = os.path.join(file_folder, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(file_metadata[file_id], f, default=str, ensure_ascii=False)

        # Return response
        return jsonify({
            'file_id': file_id,
            'is_valid': is_valid
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/errors/<file_id>', methods=['GET'])
def get_errors(file_id):
    """Return compressed error JSON for a file with structure optimization + Brotli"""
    try:
        # Check if file exists
        if file_id not in file_metadata:
            return jsonify({'error': 'File not found'}), 404
        
        # Get paths
        error_json_path = file_metadata[file_id].get('error_json_path')
        file_folder = file_metadata[file_id]['folder']
        compressed_path = os.path.join(file_folder, 'error_report.br')
        
        # Check if compressed file exists
        if os.path.exists(compressed_path):
            # Serve existing compressed file
            with open(compressed_path, 'rb') as f:
                compressed_data = f.read()
            
            return Response(
                compressed_data,
                headers={
                    'Content-Type': 'application/octet-stream',
                    'Content-Encoding': 'br',
                    'Cache-Control': 'no-cache'
                }
            )
        
        # Load original JSON and compress it
        if not error_json_path or not os.path.exists(error_json_path):
            # No errors case
            empty_error_data = {
                'summary': {'total_errors': 0, 'error_rows': 0, 'categories': {}},
                'rows_data': {},
                'categories': []
            }
            compressed_data = compress_error_data(empty_error_data, compressed_path)
        else:
            # Load error data safely
            error_data = safe_json_load(error_json_path)
            if not error_data:
                # Fallback to empty structure if loading failed
                error_data = {
                    'summary': {'total_errors': 0, 'error_rows': 0, 'categories': {}},
                    'rows_data': {},
                    'categories': []
                }
            
            # Ensure the error data has the expected structure
            if 'summary' not in error_data:
                error_data['summary'] = {
                    'total_errors': 0,
                    'error_rows': 0,
                    'categories': {}
                }
            
            if 'rows_data' not in error_data:
                error_data['rows_data'] = {}
            
            if 'categories' not in error_data:
                error_data['categories'] = []
            
            # Compress and save
            compressed_data = compress_error_data(error_data, compressed_path)
        
        return Response(
            compressed_data,
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Encoding': 'br',
                'Cache-Control': 'no-cache'
            }
        )
        
    except Exception as e:
        error_details = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        app.logger.error(f"Error in get_errors: {error_details}")
        return jsonify(error_details), 500


def compress_error_data(error_data, output_path=None):
    """
    Compress error data using structure optimization + Brotli compression
    """
    try:
        # Field mappings to reduce key repetition
        field_map = {
            "Date": "d", "A/C Registration": "r", "Flight": "f", "A/C Type": "t",
            "ATD (UTC) Block out": "o", "ATA (UTC) Block in": "i", 
            "Origin ICAO": "or", "Destination ICAO": "de", "Uplift Volume": "uv",
            "Uplift Density": "ud", "Uplift weight": "uw", 
            "Remaining Fuel From Prev. Flight": "rf", "Block off Fuel": "bf",
            "Block on Fuel": "bo", "Fuel Type": "ft"
        }
        
        # Reverse mapping for client-side decompression
        reverse_field_map = {v: k for k, v in field_map.items()}
        
        # Optimize row data structure
        optimized_rows = {}
        for row_idx, row_data in error_data.get('rows_data', {}).items():
            optimized_row = {}
            
            for key, value in row_data.items():
                if key == 'error':
                    optimized_row['err'] = value
                else:
                    short_key = field_map.get(key, key)
                    
                    # Optimize numeric values
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        rounded_value = round(float(value), 3)
                        if rounded_value == int(rounded_value):
                            value = int(rounded_value)
                        else:
                            value = rounded_value
                    
                    optimized_row[short_key] = value
            
            optimized_rows[row_idx] = optimized_row
        
        # Optimize error structure
        optimized_categories = []
        for category in error_data.get('categories', []):
            category_errors = []
            
            for error_group in category.get('errors', []):
                reason_data = {
                    "r": error_group.get('reason', ''),  # reason
                    "rows": []
                }
                
                for row_error in error_group.get('rows', []):
                    if row_error.get('file_level'):
                        row_entry = {
                            "fl": True,  # file_level
                            "cd": row_error.get('cell_data', ''),  # cell_data
                            "cols": row_error.get('columns', [])
                        }
                    else:
                        row_entry = {
                            "idx": row_error.get('row_idx'),  # row_idx
                            "cd": row_error.get('cell_data', ''),  # cell_data
                            "cols": row_error.get('columns', [])
                        }
                    
                    reason_data["rows"].append(row_entry)
                
                category_errors.append(reason_data)
            
            optimized_categories.append({
                "n": category.get('name', ''),  # name
                "e": category_errors  # errors
            })
        
        # Create optimized report
        summary = error_data.get('summary', {})
        optimized_report = {
            "meta": {
                "fm": reverse_field_map,  # field map for decompression
                "s": {  # summary
                    "te": summary.get('total_errors', 0),  # total_errors
                    "er": summary.get('error_rows', 0),  # error_rows
                    "c": summary.get('categories', {})  # categories
                }
            },
            "rd": optimized_rows,  # rows_data
            "c": optimized_categories  # categories
        }
        
        # Convert to compact JSON
        json_str = json.dumps(optimized_report, separators=(',', ':'), ensure_ascii=False)
        
        # Compress with Brotli
        compressed_data = brotli.compress(json_str.encode('utf-8'))
        
        # Calculate compression stats
        original_size = len(json_str.encode('utf-8'))
        compressed_size = len(compressed_data)
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        app.logger.info(f"JSON Optimization + Brotli Compression:")
        app.logger.info(f"  Original size: {original_size:,} bytes")
        app.logger.info(f"  Compressed size: {compressed_size:,} bytes")
        app.logger.info(f"  Compression ratio: {compression_ratio:.1f}%")
        
        # Save compressed data if output path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(compressed_data)
        
        return compressed_data
        
    except Exception as e:
        app.logger.error(f"Error compressing data: {e}")
        # Fallback: return uncompressed JSON
        json_str = json.dumps(error_data, separators=(',', ':'), ensure_ascii=False)
        return json_str.encode('utf-8')


@app.route('/upload/<file_id>', methods=['PUT'])
def update_csv(file_id):
    """Handle CSV corrections and re-validation"""
    try:
        # Check if file exists
        if file_id not in file_metadata:
            return jsonify({'error': 'File not found'}), 404
        
        data = request.get_json()
        
        # Check if ignoring errors
        if data.get('ignore_errors'):
            file_metadata[file_id]['errors_ignored'] = True
            return jsonify({'success': True, 'message': 'Errors ignored'}), 200
        
        # Check if re-validating
        if data.get('revalidate'):
            # Re-run validation on existing file
            return rerun_validation(file_id)
        
        # Handle corrections
        corrections = data.get('corrections', [])
        if not corrections:
            return jsonify({'error': 'No corrections provided'}), 400
        
        # Load the current CSV
        file_path = file_metadata[file_id]['original_path']
        encoding = detect_encoding(file_path)
        df = pd.read_csv(file_path, encoding=encoding, encoding_errors='replace')
        
        # Apply corrections
        for correction in corrections:
            row_idx = correction.get('row')
            column = correction.get('column')
            new_value = correction.get('new_value')
            
            if row_idx is not None and column and row_idx < len(df):
                # Convert row_idx to integer if it's a string
                if isinstance(row_idx, str):
                    row_idx = int(row_idx)
                
                # Handle data type conversion properly
                if column in df.columns:
                    current_dtype = df[column].dtype
                    
                    # Convert new_value to appropriate type
                    try:
                        if pd.api.types.is_numeric_dtype(current_dtype):
                            # Handle numeric columns
                            if new_value == '' or new_value is None:
                                # Handle empty values for numeric columns
                                if pd.api.types.is_integer_dtype(current_dtype):
                                    new_value = pd.NA  # Use pandas NA for integer columns
                                else:
                                    new_value = float('nan')  # Use NaN for float columns
                            else:
                                # Convert to appropriate numeric type
                                if pd.api.types.is_integer_dtype(current_dtype):
                                    new_value = int(float(new_value))  # Convert through float first to handle '0.0' -> 0
                                else:
                                    new_value = float(new_value)
                        else:
                            # For non-numeric columns, convert to string
                            new_value = str(new_value) if new_value is not None else ''
                    
                    except (ValueError, TypeError) as e:
                        # If conversion fails, convert to string and let pandas handle it
                        print(f"Warning: Could not convert '{new_value}' to {current_dtype}, using string: {e}")
                        new_value = str(new_value) if new_value is not None else ''
                
                # Now assign the properly converted value
                df.at[row_idx, column] = new_value
        
        # Save corrected CSV
        corrected_path = os.path.join(file_metadata[file_id]['folder'], 'corrected.csv')
        df.to_csv(corrected_path, index=False, encoding='utf-8')
        
        # Update metadata
        file_metadata[file_id]['original_path'] = corrected_path
        
        # Re-run validation
        return rerun_validation(file_id)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def rerun_validation(file_id):
    """Re-run validation on a file"""
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
        compressed_path = os.path.join(file_folder, 'error_report.br')
        if os.path.exists(compressed_path):
            os.remove(compressed_path)
        
        return jsonify({
            'success': True,
            'is_valid': is_valid
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/report/<file_id>', methods=['POST'])
def build_report_endpoint(file_id):
    """Generate CORSIA report"""
    try:
        # Check if file exists
        if file_id not in file_metadata:
            return jsonify({'error': 'File not found'}), 404
        
        metadata = file_metadata[file_id]
        
        # Check if file is valid or errors were ignored
        if not metadata.get('is_valid') and not metadata.get('errors_ignored'):
            return jsonify({'error': 'Cannot generate report - file has unresolved errors'}), 400
        
        # Get processed CSV path
        processed_path = metadata.get('processed_path')
        flight_starts_with = metadata.get('flight_starts_with')
        if not processed_path or not os.path.exists(processed_path):
            # Use original if processed doesn't exist
            processed_path = metadata['original_path']
        
        # Define output path for Excel report
        output_path = os.path.join(metadata['folder'], 'template_filled.xlsx')
        
        try:
            # Call build_report function
            build_report(processed_path, flight_starts_with)
        except Exception as e:
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            app.logger.error(f"Error in build_report: {error_details}")
            return jsonify(error_details), 500
        
        # Send file to client
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
        app.logger.error(f"Error in build_report_endpoint: {error_details}")
        return jsonify(error_details), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200


# Cleanup old uploads periodically (optional)
def cleanup_old_uploads():
    """Remove uploads older than 24 hours"""
    import time
    current_time = time.time()
    
    for file_id in list(file_metadata.keys()):
        folder = file_metadata[file_id]['folder']
        metadata_path = os.path.join(folder, 'metadata.json')
        
        if os.path.exists(metadata_path):
            # Check file age
            file_age = current_time - os.path.getmtime(metadata_path)
            if file_age > 86400:  # 24 hours
                # Remove folder and metadata
                shutil.rmtree(folder, ignore_errors=True)
                del file_metadata[file_id]


if __name__ == '__main__':
    # Run cleanup on startup
    cleanup_old_uploads()
    
    # Start Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)