# -*- coding: utf-8 -*-
"""
Secure Flask API Backend for Vurdhaan Report Project (app5.py)
Implements Firebase authentication, RBAC, and secure API endpoints

Features:
- Firebase ID token authentication
- Project management with ownership validation
- Secure file upload and validation
- AI chat with permission checks
- Rate limiting and input validation
- CORS and security headers
"""

import sys
import os
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, g, send_file
from flask_cors import CORS
import pandas as pd

# Configuration
from config import Config

# Middleware
from middleware.auth import FirebaseAuth, require_auth
from middleware.rate_limit import rate_limiter, limit_by_user, limit_expensive, exempt_from_rate_limit
from middleware.validation import (
    validate_json, validate_file, CreateProjectSchema,
    UpdateProjectSchema, ChatQuerySchema, validate_project_id
)

# Services
from services.firebase_service import FirestoreService
from services.project_service import ProjectService
from services.storage_service import StorageService

# Existing helpers
from helpers.clean import validate_and_process_file
from helpers.corsia import build_report
from modules.session_manager import SessionManager
from modules.database import DuckDBManager
from modules.sql_generator import create_sql_agent

# ============================================================================
# INITIALIZATION
# ============================================================================

app = Flask(__name__)
app.config.from_object(Config)

# Firebase
firebase_creds = os.getenv('FIREBASE_CREDENTIALS_PATH')
FirebaseAuth.initialize(firebase_creds)

# CORS
origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, resources={r"/api/*": {"origins": origins, "allow_headers": ["Content-Type", "Authorization"]}})

# Rate Limiter
rate_limiter.init_app(app)

# Services
firestore = FirestoreService()
projects = ProjectService()
storage = StorageService()
sessions = SessionManager()

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

print("[*] Secure API Backend (app5.py) - Ready")

# ============================================================================
# SECURITY HEADERS
# ============================================================================

@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    error_details = {
        'error': 'Internal server error',
        'message': str(e),
        'traceback': traceback.format_exc()
    }
    print("ERROR:", str(e))
    print("TRACEBACK:", traceback.format_exc())
    return jsonify(error_details), 500

@app.errorhandler(429)
def rate_limit_error(e):
    return jsonify({'error': 'Rate limit exceeded'}), 429

# ============================================================================
# HEALTH & INFO
# ============================================================================

@app.route('/api/health', methods=['GET'])
@exempt_from_rate_limit
def health():
    return jsonify({'status': 'healthy', 'version': '5.0.0'}), 200

# ============================================================================
# AUTHENTICATION
# ============================================================================

@app.route('/api/auth/verify', methods=['POST'])
@require_auth
def verify():
    user = firestore.create_or_update_user(g.user['uid'], g.user['email'])
    return jsonify({'success': True, 'user': {'uid': user['uid'], 'email': user['email']}}), 200

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_me():
    user = firestore.get_user(g.user['uid'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'uid': user['uid'],
        'email': user['email'],
        'name': user.get('name'),
        'project_count': user.get('project_count', 0)
    }), 200

# ============================================================================
# PROJECTS
# ============================================================================

@app.route('/api/projects', methods=['GET'])
@require_auth
@limit_by_user("60 per minute")
def list_projects_route():
    status = request.args.get('status')
    limit = min(int(request.args.get('limit', 100)), 100)
    project_list = projects.list_user_projects(g.user['uid'], status, limit)

    formatted = []
    for p in project_list:
        formatted.append({
            'id': p['id'],
            'name': p['name'],
            'status': p['status'],
            'ai_chat_enabled': p.get('ai_chat_enabled', False),
            'save_files_on_server': p.get('save_files_on_server', False),
            'created_at': p['created_at'].isoformat() if isinstance(p['created_at'], datetime) else p['created_at'],
            'has_file': p.get('file_metadata') is not None
        })

    return jsonify({'projects': formatted, 'total': len(formatted)}), 200

@app.route('/api/projects', methods=['POST'])
@require_auth
@limit_expensive("10 per hour")
@validate_json(CreateProjectSchema)
def create_project_route():
    data = g.validated_data
    project = projects.create_project(
        owner_uid=g.user['uid'],
        name=data['name'],
        description=data.get('description'),
        ai_chat_enabled=data.get('ai_chat_enabled', False),
        save_files_on_server=data.get('save_files_on_server', False)
    )
    return jsonify({
        'success': True,
        'project': {
            'id': project['id'],
            'name': project['name'],
            'ai_chat_enabled': project['ai_chat_enabled'],
            'save_files_on_server': project['save_files_on_server']
        }
    }), 201

@app.route('/api/projects/<project_id>', methods=['GET'])
@require_auth
@limit_by_user("60 per minute")
def get_project_route(project_id):
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    return jsonify({
        'id': project['id'],
        'name': project['name'],
        'description': project.get('description', ''),
        'status': project['status'],
        'ai_chat_enabled': project.get('ai_chat_enabled'),
        'save_files_on_server': project.get('save_files_on_server'),
        'validation_status': project.get('validation_status'),
        'file_metadata': project.get('file_metadata')
    }), 200

@app.route('/api/projects/<project_id>', methods=['PUT'])
@require_auth
@limit_by_user("30 per hour")
@validate_json(UpdateProjectSchema)
def update_project_route(project_id):
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    updated = projects.update_project(project_id, g.user['uid'], g.validated_data)
    if not updated:
        return jsonify({'error': 'Not found or unauthorized'}), 404

    return jsonify({'success': True, 'project': {'id': updated['id'], 'name': updated['name']}}), 200

@app.route('/api/projects/<project_id>', methods=['DELETE'])
@require_auth
@limit_by_user("10 per hour")
def delete_project_route(project_id):
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    success = projects.delete_project(project_id, g.user['uid'])
    if not success:
        return jsonify({'error': 'Not found or unauthorized'}), 404

    return jsonify({'success': True}), 200

# ============================================================================
# FILE UPLOAD
# ============================================================================

@app.route('/api/projects/<project_id>/upload', methods=['POST'])
@require_auth
@limit_expensive("10 per hour")
@validate_file('file', ['csv'], max_size_mb=50)
def upload_route(project_id):
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    file = g.validated_file

    try:
        from datetime import datetime as dt
        start_date = dt.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = dt.strptime(request.form['end_date'], '%Y-%m-%d').date()
        date_format = request.form.get('date_format', 'DMY')
        flight_prefix = request.form.get('flight_starts_with', '')
        fuel_method = request.form.get('fuel_method', 'Block Off - Block On')
        print(f"[UPLOAD] Form data parsed: start_date={start_date}, end_date={end_date}, date_format={date_format}")
    except Exception as e:
        print(f"[UPLOAD ERROR] Form data parsing failed: {str(e)}")
        return jsonify({'error': 'Invalid form data', 'details': str(e)}), 400

    try:
        print(f"[UPLOAD] Starting file upload for project {project_id}")
        upload_result = projects.handle_file_upload(project_id, g.user['uid'], file, {
            'start_date': start_date,
            'end_date': end_date
        })
        print(f"[UPLOAD] File uploaded successfully: {upload_result['file_path']}")

        # Check if airports.csv exists
        airports_path = 'airports.csv'
        if not os.path.exists(airports_path):
            print(f"[UPLOAD ERROR] airports.csv not found at {airports_path}")
            return jsonify({'error': 'Reference file airports.csv not found'}), 500

        print(f"[UPLOAD] Reading reference data from {airports_path}")
        # Validation
        ref_df = pd.read_csv(airports_path, encoding='utf-8', encoding_errors='replace')
        print(f"[UPLOAD] Reference data loaded: {len(ref_df)} rows")
        
        print(f"[UPLOAD] Reading uploaded file: {upload_result['file_path']}")
        result_df = pd.read_csv(upload_result['file_path'], encoding='utf-8', encoding_errors='replace')
        result_df.columns = result_df.columns.str.strip()
        print(f"[UPLOAD] Uploaded file loaded: {len(result_df)} rows, columns: {list(result_df.columns)}")

        print(f"[UPLOAD] Starting validation with validate_and_process_file")
        is_valid, processed_path, _, error_json = validate_and_process_file(
            upload_result['file_path'], result_df, ref_df,
            date_format, flight_prefix, start_date, end_date, fuel_method
        )
        print(f"[UPLOAD] Validation completed: is_valid={is_valid}")

        # Store validation parameters in file_metadata for later use (e.g., corrections)
        file_metadata = {
            'filename': file.filename,
            'upload_time': datetime.utcnow().isoformat(),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'date_format': date_format,
            'flight_starts_with': flight_prefix,
            'fuel_method': fuel_method
        }

        projects.update_validation_results(project_id, is_valid, 0, file_metadata)
        print(f"[UPLOAD] Validation results updated in database")

        # Note: error_report.lzs is already saved by validate_and_process_file in the project directory
        # The compressed file is created automatically during validation

        return jsonify({
            'success': True,
            'project_id': project_id,
            'file_id': project_id,
            'is_valid': is_valid,
            'filename': file.filename,
            'has_errors': not is_valid
        }), 200

    except PermissionError as e:
        print(f"[UPLOAD ERROR] Permission denied: {str(e)}")
        return jsonify({'error': 'Unauthorized', 'details': str(e)}), 403
    except FileNotFoundError as e:
        print(f"[UPLOAD ERROR] File not found: {str(e)}")
        return jsonify({'error': 'Required file not found', 'details': str(e)}), 500
    except ImportError as e:
        print(f"[UPLOAD ERROR] Import error: {str(e)}")
        return jsonify({'error': 'Missing dependency', 'details': str(e)}), 500
    except Exception as e:
        print(f"[UPLOAD ERROR] Unexpected error: {str(e)}")
        print(f"[UPLOAD ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

# ============================================================================
# ERROR HANDLING ENDPOINTS
# ============================================================================

@app.route('/api/projects/<project_id>/errors', methods=['GET'])
@require_auth
@limit_by_user("60 per minute")
def get_errors_route(project_id):
    """Get validation errors for a project"""
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    try:
        import json

        # Check temp directory first (where validation saves files)
        temp_path = storage.get_temp_path(project_id)
        project_path = storage.get_project_path(project_id)

        # Try compressed file first (preferred)
        # Check temp directory first, then permanent
        compressed_file = os.path.join(temp_path, 'error_report.lzs')
        if not os.path.exists(compressed_file):
            compressed_file = os.path.join(project_path, 'error_report.lzs')

        json_file = os.path.join(temp_path, 'error_report.json')
        if not os.path.exists(json_file):
            json_file = os.path.join(project_path, 'error_report.json')

        if os.path.exists(compressed_file):
            print(f"[ERRORS] Reading compressed error report: {compressed_file}")
            # Read compressed file and decompress
            with open(compressed_file, 'r') as f:
                compressed_data = f.read()

            # Return compressed data with header indicating compression
            from flask import Response
            response = Response(compressed_data, mimetype='text/plain')
            response.headers['X-Compression'] = 'lzstring'
            return response

        elif os.path.exists(json_file):
            print(f"[ERRORS] Reading JSON error report: {json_file}")
            with open(json_file, 'r') as f:
                error_data = json.load(f)
            return jsonify(error_data), 200
        else:
            # No errors - return empty structure
            print(f"[ERRORS] No error report found for project {project_id}")
            return jsonify({
                'summary': {
                    'total_errors': 0,
                    'error_rows': 0,
                    'categories': {}
                },
                'rows_data': {},
                'categories': []
            }), 200

    except Exception as e:
        print(f"[ERRORS] Get errors failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/corrections', methods=['POST'])
@require_auth
@limit_by_user("30 per hour")
def save_corrections_route(project_id):
    """Save user corrections"""
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    try:
        import json
        import pandas as pd
        from datetime import datetime as dt

        # Retrieve stored validation parameters from file_metadata
        file_meta = project.get('file_metadata', {})
        print(f"[CORRECTIONS] Retrieved file_metadata: {file_meta}")

        corrections = request.json.get('corrections', [])
        if not isinstance(corrections, list):
            return jsonify({'error': 'Invalid corrections payload'}), 400

        # Persist raw corrections for traceability
        temp_path = storage.get_temp_path(project_id)
        os.makedirs(temp_path, exist_ok=True)
        corrections_file = os.path.join(temp_path, 'corrections.json')
        with open(corrections_file, 'w') as f:
            json.dump(corrections, f)

        # Determine base CSV to apply corrections on
        # Check both temp and permanent directories
        temp_path_dir = storage.get_temp_path(project_id)
        project_path = storage.get_project_path(project_id)

        candidate_files = []
        # Check temp directory first (where uploads are initially saved)
        for filename in ['original.csv', 'reordered.csv', 'trimmed.csv', 'clean_data.csv']:
            candidate_files.append(os.path.join(temp_path_dir, filename))
        # Then check permanent directory
        for filename in ['original.csv', 'reordered.csv', 'trimmed.csv', 'clean_data.csv']:
            candidate_files.append(os.path.join(project_path, filename))

        base_csv = next((p for p in candidate_files if os.path.exists(p)), None)
        if not base_csv:
            print(f"[CORRECTIONS ERROR] No base CSV found. Checked paths: {candidate_files}")
            return jsonify({'error': 'Base CSV not found for project'}), 404

        print(f"[CORRECTIONS] Applying {len(corrections)} corrections on: {base_csv}")

        # Load CSV with robust encoding
        try:
            df = pd.read_csv(base_csv, encoding='utf-8', encoding_errors='replace')
        except Exception:
            df = pd.read_csv(base_csv)

        # Apply corrections with dtype-aware conversion (mirrors app4.py semantics)
        applied = 0
        for i, corr in enumerate(corrections):
            row_idx = corr.get('row') or corr.get('row_idx')
            column = corr.get('column')
            new_value = corr.get('new_value')

            if row_idx is None or not column:
                continue

            # Normalize row index to int if possible
            try:
                row_idx = int(float(row_idx))
            except Exception:
                continue

            if row_idx < 0 or row_idx >= len(df) or column not in df.columns:
                continue

            current_dtype = df[column].dtype
            try:
                if pd.api.types.is_numeric_dtype(current_dtype):
                    if new_value == '' or new_value is None:
                        new_value = pd.NA if pd.api.types.is_integer_dtype(current_dtype) else float('nan')
                    else:
                        new_value = int(float(new_value)) if pd.api.types.is_integer_dtype(current_dtype) else float(new_value)
                else:
                    new_value = '' if new_value is None else str(new_value)
            except Exception:
                # Fallback to string
                new_value = '' if new_value is None else str(new_value)

            df.at[row_idx, column] = new_value
            applied += 1

        # Save corrected CSV in the same directory as the base CSV
        base_csv_dir = os.path.dirname(base_csv)
        corrected_csv = os.path.join(base_csv_dir, 'corrected.csv')
        df.to_csv(corrected_csv, index=False, encoding='utf-8')
        print(f"[CORRECTIONS] Saved corrected CSV: {corrected_csv} (applied={applied})")

        # Re-run validation using corrected CSV
        # Use stored validation parameters from original upload
        date_format = file_meta.get('date_format', 'DMY')
        flight_prefix = file_meta.get('flight_starts_with', '')
        fuel_method = file_meta.get('fuel_method', 'Block Off - Block On')

        # Parse stored dates from file_metadata
        start_date = None
        end_date = None
        try:
            if file_meta.get('start_date'):
                start_date = dt.fromisoformat(file_meta['start_date']).date()
            if file_meta.get('end_date'):
                end_date = dt.fromisoformat(file_meta['end_date']).date()
            print(f"[CORRECTIONS] Using stored dates: start={start_date}, end={end_date}")
        except Exception as e:
            print(f"[CORRECTIONS] Could not parse stored dates: {e}")

        # Fallback: infer date range from 'Date' column if stored dates are unavailable
        if not start_date or not end_date:
            try:
                if 'Date' in df.columns:
                    dates = pd.to_datetime(df['Date'], errors='coerce', utc=False)
                    if dates.notna().any():
                        start_date = dates.min().date()
                        end_date = dates.max().date()
                        print(f"[CORRECTIONS] Inferred dates from data: start={start_date}, end={end_date}")
            except Exception as e:
                print(f"[CORRECTIONS] Could not infer dates from data: {e}")

        # Load reference airports data
        airports_path = 'airports.csv'
        if not os.path.exists(airports_path):
            return jsonify({'error': 'Reference file airports.csv not found'}), 500

        ref_df = pd.read_csv(airports_path, encoding='utf-8', encoding_errors='replace')

        print(f"[CORRECTIONS] Re-validating corrected data with parameters: start={start_date}, end={end_date}, fmt={date_format}, prefix={flight_prefix}, fuel={fuel_method}")
        is_valid, processed_path, _, error_json = validate_and_process_file(
            corrected_csv, df, ref_df, date_format, flight_prefix, start_date, end_date, fuel_method
        )

        # Update project validation status (error count unknown -> infer from file existence/flag)
        error_count = 0 if is_valid else 1
        projects.update_validation_results(project_id, is_valid, error_count)

        return jsonify({
            'success': True,
            'corrections_saved': len(corrections),
            'applied': applied,
            'revalidated': True,
            'is_valid': is_valid
        }), 200

    except Exception as e:
        print("ERROR: Save corrections failed:", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/ignore-errors', methods=['POST'])
@require_auth
@limit_by_user("10 per hour")
def ignore_errors_route(project_id):
    """Mark project as validated despite errors"""
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    try:
        # Update project to mark as validated
        projects.update_validation_results(project_id, True, 0)

        return jsonify({'success': True}), 200

    except Exception as e:
        print("ERROR: Ignore errors failed:", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/revalidate', methods=['POST'])
@require_auth
@limit_by_user("20 per hour")
def revalidate_route(project_id):
    """Re-validate the project data"""
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    try:
        # Reset validation status
        projects.update_validation_results(project_id, False, 0)

        return jsonify({'success': True}), 200

    except Exception as e:
        print("ERROR: Revalidate failed:", str(e))
        return jsonify({'error': str(e)}), 500

# ============================================================================
# CHAT (requires AI chat enabled)
# ============================================================================

@app.route('/api/projects/<project_id>/chat/initialize', methods=['POST'])
@require_auth
@limit_expensive("20 per hour")
def chat_init(project_id):
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    if not project.get('ai_chat_enabled'):
        return jsonify({'error': 'AI chat not enabled for this project'}), 403

    if not project.get('file_metadata'):
        return jsonify({'error': 'No file uploaded'}), 400

    try:
        path = storage.get_project_path(project_id)
        clean_csv = os.path.join(path, 'clean_data.csv')
        error_csv = os.path.join(path, 'errors_data.csv')

        if not os.path.exists(clean_csv):
            return jsonify({'error': 'Data files not found'}), 400

        session_id, session_data = sessions.create_session_with_id(project_id, clean_csv, error_csv)
        db = DuckDBManager(session_id, session_data['db_path'])
        load_result = db.load_csv_data(clean_csv, error_csv)

        sessions.update_session(session_id, {'status': 'active', 'database_info': load_result})
        firestore.set_project_session(project_id, session_id)
        db.close()

        return jsonify({'success': True, 'session_id': session_id, 'database_info': load_result}), 200
    except Exception as e:
        print("ERROR: Chat init failed:", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/chat/query', methods=['POST'])
@require_auth
@limit_by_user("30 per hour")
@validate_json(ChatQuerySchema)
def chat_query_route(project_id):
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project or not project.get('ai_chat_enabled'):
        return jsonify({'error': 'Unauthorized or chat disabled'}), 403

    query = g.validated_data['query']
    session_id = g.validated_data.get('session_id') or project.get('session_id') or project_id

    session = sessions.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    try:
        db = DuckDBManager(session_id, session['db_path'])
        agent = create_sql_agent(db, session_id, 3, None, True)
        result = agent.process_query(query)

        sessions.update_session(session_id, {'message_count': session.get('message_count', 0) + 1})
        db.close()

        if result['success']:
            return jsonify({
                'status': 'success',
                'response': result['answer'],
                'sql_query': result['metadata'].get('sql_query'),
                'table_data': result.get('table_rows', [])
            }), 200
        else:
            return jsonify({'status': 'error', 'response': result['answer']}), 200
    except Exception as e:
        print("ERROR: Query failed:", str(e))
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ============================================================================
# REPORT & DOWNLOAD
# ============================================================================

@app.route('/api/projects/<project_id>/report', methods=['POST'])
@require_auth
@limit_expensive("5 per hour")
def report_route(project_id):
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project or not project.get('validation_status'):
        return jsonify({'error': 'Not found or not validated'}), 400

    try:
        path = storage.get_project_path(project_id)
        csv = os.path.join(path, 'clean_data.csv')
        prefix = request.json.get('flight_starts_with', '')

        output = os.path.join(path, 'template_filled.xlsx')
        build_report(csv, prefix)

        return send_file(output, as_attachment=True, download_name='report_{}.xlsx'.format(project_id))
    except Exception as e:
        print("ERROR: Report failed:", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/download/<csv_type>', methods=['GET'])
@require_auth
@limit_by_user("30 per hour")
def download_route(project_id, csv_type):
    if not validate_project_id(project_id) or csv_type not in ['clean', 'errors']:
        return jsonify({'error': 'Invalid request'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Not found'}), 404

    path = storage.get_project_path(project_id)
    csv_path = os.path.join(path, '{}_data.csv'.format(csv_type))

    if not os.path.exists(csv_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(csv_path, as_attachment=True, download_name='{}_data.csv'.format(csv_type))

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    print("[*] Starting app5.py on port", Config.PORT)
    app.run(host=Config.HOST, port=Config.PORT, debug=(Config.FLASK_ENV == 'development'))
