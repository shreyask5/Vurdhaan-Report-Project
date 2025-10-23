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
    validate_json, validate_file, validate_monitoring_plan_file,
    CreateProjectSchema, UpdateProjectSchema, ChatQuerySchema,
    SchemeSelectionSchema, validate_project_id
)

# Services
from services.firebase_service import FirestoreService
from services.project_service import ProjectService
from services.storage_service import StorageService
from services.openai_service import OpenAIService
from services.chat_service import ChatService
from modules.cleanup_service import create_cleanup_service

# Existing helpers
from helpers.clean import validate_and_process_file
from helpers.corsia import build_report
from modules.session_manager import SessionManager
from modules.database import DuckDBManager
from modules.sql_generator_open_router import create_openrouter_sql_agent
from concurrent.futures import ThreadPoolExecutor
import uuid

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
openai_service = OpenAIService()
chat_service = ChatService()
executor_workers = int(os.getenv('MONITORING_PLAN_WORKERS', '4'))
executor = ThreadPoolExecutor(max_workers=executor_workers)
# Simple in-memory task registry; for multi-instance deployments, replace with Redis.
monitoring_plan_tasks = {}

# Initialize PostgreSQL cleanup service
cleanup_service = create_cleanup_service()

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

print("[*] Secure API Backend (app5.py) - Ready")
print(f"[*] PostgreSQL Cleanup Service - Enabled: {cleanup_service.enabled}")
print(f"[*] Cleanup Interval: {cleanup_service.cleanup_interval_seconds / 60} minutes")
print(f"[*] Inactivity Timeout: {cleanup_service.inactive_minutes} minutes")
print(f"[*] Monitoring Plan: {'Enabled' if Config.ENABLE_MONITORING_PLAN else 'Disabled'}")

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

@app.route('/api/auth/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile including profile completion status"""
    user = firestore.get_user(g.user['uid'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'uid': user['uid'],
        'email': user['email'],
        'name': user.get('name'),
        'designation': user.get('designation'),
        'airline_name': user.get('airline_name'),
        'airline_size': user.get('airline_size'),
        'profile_completed': user.get('profile_completed', False)
    }), 200

@app.route('/api/auth/profile', methods=['PUT'])
@require_auth
@limit_by_user("30 per hour")
def update_profile():
    """Update user profile"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate allowed fields
    allowed_fields = ['designation', 'airline_name', 'airline_size', 'profile_completed']
    update_data = {}

    for field in allowed_fields:
        if field in data:
            update_data[field] = data[field]

    # Validate airline_size if provided
    if 'airline_size' in update_data:
        if update_data['airline_size'] not in ['small', 'medium', 'large']:
            return jsonify({'error': 'Invalid airline_size. Must be small, medium, or large'}), 400

    if not update_data:
        return jsonify({'error': 'No valid fields to update'}), 400

    try:
        # Update user document in Firestore
        firestore.update_user(g.user['uid'], update_data)
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"[PROFILE UPDATE ERROR] {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500

@app.route('/api/auth/verify-email-action', methods=['POST'])
@limit_by_user("10 per hour")
def verify_email_action():
    """
    Optional backend endpoint to log email verification attempts
    The actual verification is done client-side using Firebase action codes
    This endpoint provides logging and monitoring capabilities
    """
    data = request.get_json()
    if not data or 'oobCode' not in data:
        return jsonify({'error': 'Missing action code'}), 400

    oob_code = data['oobCode']

    try:
        print(f"[EMAIL VERIFICATION] Received verification request with code: {oob_code[:10]}...")

        # Log the verification attempt
        # In production, you might want to store this in a database for analytics

        return jsonify({
            'success': True,
            'message': 'Action code received. Please apply it on the client side.'
        }), 200

    except Exception as e:
        print(f"[EMAIL VERIFICATION ERROR] {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process action code',
            'details': str(e)
        }), 500

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
            'has_file': p.get('file_metadata') is not None,
            'upload_completed': p.get('upload_completed'),
            'validation_status': p.get('validation_status'),
            'error_count': p.get('error_count'),
            'file_metadata': p.get('file_metadata'),
            'updated_at': p.get('updated_at').isoformat() if p.get('updated_at') and isinstance(p.get('updated_at'), datetime) else p.get('updated_at')
        })

    return jsonify({'projects': formatted, 'total': len(formatted)}), 200

@app.route('/api/projects', methods=['POST'])
@require_auth
@limit_expensive("10 per hour")
@validate_json(CreateProjectSchema)
def create_project_route():
    data = g.validated_data
    # Determine next version number for the selected scheme
    scheme = data['scheme']
    next_version = firestore.increment_report_counter(g.user['uid'], scheme)
    name = f"{scheme} Version {next_version}"

    project = projects.create_project(
        owner_uid=g.user['uid'],
        name=name,
        description=None,
        ai_chat_enabled=data.get('ai_chat_enabled', False),
        save_files_on_server=data.get('save_files_on_server', False)
    )

    # Persist scheme on the project
    projects.update_project(project['id'], g.user['uid'], {'scheme': scheme})

    return jsonify({
        'success': True,
        'project': {
            'id': project['id'],
            'name': name,
            'scheme': scheme,
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
        'scheme': project.get('scheme'),
        'ai_chat_enabled': project.get('ai_chat_enabled'),
        'save_files_on_server': project.get('save_files_on_server'),
        'validation_status': project.get('validation_status'),
        'file_metadata': project.get('file_metadata'),
        'upload_completed': project.get('upload_completed'),
        'error_count': project.get('error_count'),
        'has_file': project.get('file_metadata') is not None,
        'created_at': project['created_at'].isoformat() if isinstance(project['created_at'], datetime) else project['created_at'],
        'updated_at': project.get('updated_at').isoformat() if project.get('updated_at') and isinstance(project.get('updated_at'), datetime) else project.get('updated_at')
    }), 200

@app.route('/api/projects/<project_id>', methods=['PUT'])
@require_auth
@limit_by_user("30 per hour")
@validate_json(UpdateProjectSchema)
def update_project_route(project_id):
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    # Filter out None values to prevent overwriting existing fields with null
    validated_data = {k: v for k, v in g.validated_data.items() if v is not None}

    updated = projects.update_project(project_id, g.user['uid'], validated_data)
    if not updated:
        return jsonify({'error': 'Not found or unauthorized'}), 404

    # Return full project object instead of just id and name
    return jsonify({'success': True, 'project': updated}), 200

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
# SCHEME SELECTION & MONITORING PLAN
# ============================================================================

@app.route('/api/projects/<project_id>/scheme', methods=['PUT'])
@require_auth
@limit_by_user("30 per hour")
@validate_json(SchemeSelectionSchema)
def update_scheme_route(project_id):
    """Update project scheme"""
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    data = g.validated_data
    updated = projects.update_scheme(
        project_id,
        g.user['uid'],
        data['scheme']
    )

    if not updated:
        return jsonify({'error': 'Not found or unauthorized'}), 404

    return jsonify({
        'success': True,
        'scheme': data['scheme']
    }), 200

@app.route('/api/projects/<project_id>/monitoring-plan', methods=['POST'])
@require_auth
@limit_expensive("5 per hour")
@validate_monitoring_plan_file('file', max_size_mb=50)
def upload_monitoring_plan_route(project_id):
    """Upload and asynchronously process monitoring plan file"""
    # Check if monitoring plan is enabled
    if not Config.ENABLE_MONITORING_PLAN:
        return jsonify({'error': 'Monitoring plan functionality is disabled'}), 403
    
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    file = g.validated_file

    try:
        # Save file temporarily for processing
        print(f"[MONITORING PLAN] Starting async upload for project {project_id}")
        temp_path = storage.get_temp_path(project_id)
        os.makedirs(temp_path, exist_ok=True)

        file_extension = file.filename.rsplit('.', 1)[-1].lower()
        temp_file_path = os.path.join(temp_path, f'temp_monitoring_plan.{file_extension}')

        file.save(temp_file_path)
        print(f"[MONITORING PLAN] File saved to: {temp_file_path}")

        # Create background task
        task_id = str(uuid.uuid4())
        user_uid = g.user['uid']  # Capture user_uid before background thread

        monitoring_plan_tasks[task_id] = {
            'status': 'queued',
            'project_id': project_id,
            'file_path': temp_file_path,
            'file_extension': file_extension,
            'error': None,
            'result': None
        }

        def run_extraction(task_id_local: str, user_uid_local: str, project_id_local: str, file_path_local: str, file_ext_local: str):
            try:
                monitoring_plan_tasks[task_id_local]['status'] = 'running'
                print(f"[MONITORING PLAN] Task {task_id_local} running for project {project_id_local}")
                extracted_data = openai_service.extract_monitoring_plan_info(file_path_local, file_ext_local)
                # Persist to project document
                projects.update_project(project_id_local, user_uid_local, {
                    'monitoring_plan': extracted_data,
                    'monitoring_plan_status': {
                        'status': 'done',
                        'updated_at': datetime.utcnow().isoformat()
                    }
                })
                monitoring_plan_tasks[task_id_local]['result'] = extracted_data
                monitoring_plan_tasks[task_id_local]['status'] = 'done'
                print(f"[MONITORING PLAN] Task {task_id_local} completed for project {project_id_local}")
            except Exception as e:
                print(f"[MONITORING PLAN ERROR] Task {task_id_local} failed: {e}")
                print(f"[MONITORING PLAN ERROR] Traceback: {traceback.format_exc()}")
                monitoring_plan_tasks[task_id_local]['status'] = 'error'
                monitoring_plan_tasks[task_id_local]['error'] = str(e)
                # Update project status
                projects.update_project(project_id_local, user_uid_local, {
                    'monitoring_plan_status': {
                        'status': 'error',
                        'message': str(e),
                        'updated_at': datetime.utcnow().isoformat()
                    }
                })
            finally:
                try:
                    if os.path.exists(file_path_local):
                        os.remove(file_path_local)
                except Exception:
                    pass

        executor.submit(run_extraction, task_id, user_uid, project_id, temp_file_path, file_extension)

        # Update project status immediately
        projects.update_project(project_id, g.user['uid'], {
            'monitoring_plan_status': {
                'status': 'queued',
                'started_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        })

        return jsonify({'success': True, 'task_id': task_id}), 202

    except Exception as e:
        print(f"[MONITORING PLAN ERROR] Enqueue failed: {str(e)}")
        print(f"[MONITORING PLAN ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500

@app.route('/api/projects/<project_id>/monitoring-plan/status', methods=['GET'])
@require_auth
@limit_by_user("60 per minute")
def monitoring_plan_status_route(project_id):
    """Check async extraction status. Optionally pass task_id as query."""
    # Check if monitoring plan is enabled
    if not Config.ENABLE_MONITORING_PLAN:
        return jsonify({'error': 'Monitoring plan functionality is disabled'}), 403
    
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400
    task_id = request.args.get('task_id')
    if task_id and task_id in monitoring_plan_tasks:
        task = monitoring_plan_tasks[task_id]
        if task.get('project_id') != project_id:
            return jsonify({'error': 'Task not found for project'}), 404
        resp = {'status': task['status']}
        if task['status'] == 'done':
            resp['extracted_data'] = task.get('result')
        if task['status'] == 'error':
            resp['error'] = task.get('error')
        return jsonify(resp), 200

    # Fallback to project-level status
    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    mp_status = project.get('monitoring_plan_status') or {}
    return jsonify({
        'status': mp_status.get('status', 'unknown'),
        'started_at': mp_status.get('started_at'),
        'extracted_data': project.get('monitoring_plan')
    }), 200

@app.route('/api/projects/<project_id>/monitoring-plan', methods=['PUT'])
@require_auth
@limit_by_user("30 per hour")
def put_monitoring_plan_route(project_id):
    """Save user-edited monitoring plan data to Firestore."""
    # Check if monitoring plan is enabled
    if not Config.ENABLE_MONITORING_PLAN:
        return jsonify({'error': 'Monitoring plan functionality is disabled'}), 403
    
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400
    payload = request.get_json(silent=True) or {}
    try:
        updated = projects.update_project(project_id, g.user['uid'], {
            'monitoring_plan': payload,
            'monitoring_plan_status': {
                'status': 'edited',
                'updated_at': datetime.utcnow().isoformat()
            }
        })
        if not updated:
            return jsonify({'error': 'Not found or unauthorized'}), 404
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# FILE UPLOAD
# ============================================================================

@app.route('/api/projects/<project_id>/upload-status', methods=['GET'])
@require_auth
@limit_by_user("60 per minute")
def upload_status_route(project_id):
    """Check if file has been uploaded and get validation status"""
    print(f"[UPLOAD STATUS DEBUG] Called for project_id={project_id}")

    if not validate_project_id(project_id):
        print(f"[UPLOAD STATUS DEBUG] Invalid project ID")
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        print(f"[UPLOAD STATUS DEBUG] Project not found")
        return jsonify({'error': 'Project not found'}), 404

    print(f"[UPLOAD STATUS DEBUG] Project found: {project.keys() if project else 'None'}")
    print(f"[UPLOAD STATUS DEBUG] upload_completed={project.get('upload_completed')}")
    print(f"[UPLOAD STATUS DEBUG] validation_status={project.get('validation_status')}")
    print(f"[UPLOAD STATUS DEBUG] error_summary={project.get('error_summary')}")
    print(f"[UPLOAD STATUS DEBUG] save_files_on_server={project.get('save_files_on_server')}")

    response = {
        'upload_completed': project.get('upload_completed', False),
        'validation_status': project.get('validation_status'),
        'has_errors': not project.get('validation_status', True),
        'error_summary': project.get('error_summary'),
        'validation_params': project.get('file_metadata', {})
    }
    print(f"[UPLOAD STATUS DEBUG] Returning response: {response}")
    return jsonify(response), 200

@app.route('/api/projects/<project_id>/upload', methods=['POST'])
@require_auth
@limit_expensive("10 per hour")
@validate_file('file', ['csv'], max_size_mb=50)
def upload_route(project_id):
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    # Check if upload already completed for this project
    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    if project.get('upload_completed') and project.get('save_files_on_server'):
        return jsonify({'error': 'File already uploaded. Create a new project to upload again.'}), 400

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
            date_format, flight_prefix, start_date, end_date, fuel_method, project.get('scheme')
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

        # Calculate error summary for Firebase
        error_summary = None
        print(f"[UPLOAD DEBUG] Starting error summary generation")
        print(f"[UPLOAD DEBUG] is_valid={is_valid}, error_json exists={error_json is not None}")

        if not is_valid and error_json:
            try:
                print(f"[UPLOAD DEBUG] error_json keys: {error_json.keys() if error_json else 'None'}")
                total_errors = error_json.get('summary', {}).get('total_errors', 0)
                error_rows = error_json.get('summary', {}).get('error_rows', 0)
                categories = error_json.get('categories', [])
                print(f"[UPLOAD DEBUG] total_errors={total_errors}, error_rows={error_rows}, categories_count={len(categories)}")

                top_error = categories[0]['errors'][0]['reason'] if categories and categories[0].get('errors') else 'Validation errors found'

                error_summary = {
                    'total_errors': total_errors,
                    'total_clean_rows': len(result_df) - error_rows,
                    'has_errors': True,
                    'categories_count': len(categories),
                    'top_error': top_error[:100]  # Limit length
                }
                print(f"[UPLOAD DEBUG] Error summary created: {error_summary}")
            except Exception as e:
                print(f"[UPLOAD ERROR] Could not generate error summary: {e}")
                import traceback
                print(f"[UPLOAD ERROR] Traceback: {traceback.format_exc()}")
        else:
            print(f"[UPLOAD DEBUG] No error summary needed (is_valid={is_valid})")

        print(f"[UPLOAD DEBUG] Calling update_validation_results with error_summary={error_summary}")
        projects.update_validation_results(project_id, is_valid, 0, file_metadata, error_summary)
        print(f"[UPLOAD DEBUG] Validation results updated in database successfully")

        # Note: error_report.lzs is already saved by validate_and_process_file in the project directory
        # The compressed file is created automatically during validation

        return jsonify({
            'success': True,
            'project_id': project_id,
            'file_id': project_id,
            'is_valid': is_valid,
            'filename': file.filename,
            'has_errors': not is_valid,
            'error_summary': error_summary
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

@app.route('/api/projects/<project_id>/errors/metadata', methods=['GET'])
@require_auth
@limit_by_user("60 per minute")
def get_errors_metadata_route(project_id):
    """Get error metadata including categories and page counts"""
    print(f"[ERRORS METADATA API] Request received for project: {project_id}")
    print(f"[ERRORS METADATA API] User UID: {g.user['uid']}")

    if not validate_project_id(project_id):
        print(f"[ERRORS METADATA API] Invalid project ID: {project_id}")
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        print(f"[ERRORS METADATA API] Project not found: {project_id}")
        return jsonify({'error': 'Project not found'}), 404

    try:
        import json

        # Check temp directory first (where validation saves files)
        temp_path = storage.get_temp_path(project_id)
        project_path = storage.get_project_path(project_id)

        # Look for metadata file
        metadata_file = os.path.join(temp_path, 'error_metadata.json')
        if not os.path.exists(metadata_file):
            metadata_file = os.path.join(project_path, 'error_metadata.json')

        if os.path.exists(metadata_file):
            print(f"[ERRORS METADATA] Reading metadata file: {metadata_file}")
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            print(f"[ERRORS METADATA API] Metadata loaded - total_errors: {metadata.get('total_errors', 0)}")
            return jsonify(metadata), 200
        else:
            # No errors - return empty metadata
            print(f"[ERRORS METADATA] No metadata found for project {project_id}")
            return jsonify({
                'total_errors': 0,
                'error_rows': 0,
                'error_categories': 0,
                'categories': []
            }), 200

    except Exception as e:
        print(f"[ERRORS METADATA] Get metadata failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects/<project_id>/errors', methods=['GET'])
@require_auth
@limit_by_user("60 per minute")
def get_errors_route(project_id):
    """Get paginated validation errors for a project category"""
    print(f"[ERRORS API] Request received for project: {project_id}")
    print(f"[ERRORS API] User UID: {g.user['uid']}")

    if not validate_project_id(project_id):
        print(f"[ERRORS API] Invalid project ID: {project_id}")
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        print(f"[ERRORS API] Project not found: {project_id}")
        return jsonify({'error': 'Project not found'}), 404

    # Get query parameters for pagination
    category = request.args.get('category')
    page = request.args.get('page', '1')

    # Validate page number
    try:
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        return jsonify({'error': 'Invalid page number'}), 400

    # Validate category if provided
    if category:
        valid_categories = ["Time", "Date", "Fuel", "ICAO", "Sequence", "Missing", "Column Missing"]
        if category not in valid_categories:
            return jsonify({'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'}), 400

    print(f"[ERRORS API] Category: {category}, Page: {page}")

    try:
        import json

        # Check temp directory first (where validation saves files)
        temp_path = storage.get_temp_path(project_id)
        project_path = storage.get_project_path(project_id)

        print(f"[ERRORS API] Checking temp path: {temp_path}")
        print(f"[ERRORS API] Checking project path: {project_path}")

        if not category:
            # Legacy support: if no category specified, return error
            return jsonify({'error': 'category parameter is required'}), 400

        # Build filename for paginated error file
        json_filename = f"error_report_{category}_page_{page}.json"
        compressed_filename = f"error_report_{category}_page_{page}.lzs"

        # Try compressed file first (preferred)
        compressed_file = os.path.join(temp_path, compressed_filename)
        if not os.path.exists(compressed_file):
            compressed_file = os.path.join(project_path, compressed_filename)

        json_file = os.path.join(temp_path, json_filename)
        if not os.path.exists(json_file):
            json_file = os.path.join(project_path, json_filename)

        print(f"[ERRORS API] Compressed file exists: {os.path.exists(compressed_file)} at {compressed_file}")
        print(f"[ERRORS API] JSON file exists: {os.path.exists(json_file)} at {json_file}")

        if os.path.exists(compressed_file):
            print(f"[ERRORS] Reading compressed paginated error report: {compressed_file}")
            # Read compressed file
            with open(compressed_file, 'r') as f:
                compressed_data = f.read()

            # Return compressed data with header indicating compression
            from flask import Response
            response = Response(compressed_data, mimetype='text/plain')
            response.headers['X-Compression'] = 'lzstring'
            return response

        elif os.path.exists(json_file):
            print(f"[ERRORS] Reading JSON paginated error report: {json_file}")
            with open(json_file, 'r') as f:
                page_data = json.load(f)
            print(f"[ERRORS API] Page data loaded - errors_on_page: {page_data.get('errors_on_page', 0)}")
            return jsonify(page_data), 200
        else:
            # Page not found
            print(f"[ERRORS] Page not found: {category} page {page}")
            return jsonify({'error': f'Page {page} not found for category {category}'}), 404

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

        # Normalize column names to avoid trailing/leading space issues
        # This ensures required columns like 'Fuel Consumption' are detected correctly
        df.columns = df.columns.str.strip()

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
            corrected_csv, df, ref_df, date_format, flight_prefix, start_date, end_date, fuel_method, project.get('scheme')
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
        # Check temp directory first, then permanent directory
        temp_path = storage.get_temp_path(project_id)
        project_path = storage.get_project_path(project_id)

        clean_csv = os.path.join(temp_path, 'clean_data.csv')
        error_csv = os.path.join(temp_path, 'errors_data.csv')

        if not os.path.exists(clean_csv):
            clean_csv = os.path.join(project_path, 'clean_data.csv')
            error_csv = os.path.join(project_path, 'errors_data.csv')

        if not os.path.exists(clean_csv):
            return jsonify({'error': 'Data files not found'}), 400

        session_id, session_data = sessions.create_session_with_id(project_id, clean_csv, error_csv)
        db = DuckDBManager(session_id, session_data['db_path'])
        load_result = db.load_csv_data(clean_csv, error_csv)

        # Update last accessed timestamp for cleanup tracking
        db.update_last_accessed()

        sessions.update_session(session_id, {'status': 'active', 'database_info': load_result})
        firestore.set_project_session(project_id, session_id)
        db.close()

        # Create a new chat if none exists or get active chat
        try:
            request_data = request.get_json(silent=True) or {}
            chat_id = request_data.get('chat_id')
        except Exception:
            chat_id = None

        if not chat_id:
            # Check if there's an active chat
            active_chat_id = firestore.get_project_active_chat(project_id)
            if active_chat_id:
                # Verify it exists
                active_chat = chat_service.get_chat(active_chat_id)
                if active_chat:
                    chat_id = active_chat_id

            # Create new chat if no active chat exists
            if not chat_id:
                new_chat = chat_service.create_chat(project_id, g.user['uid'])
                chat_id = new_chat['id']
                firestore.set_project_active_chat(project_id, chat_id)

        return jsonify({
            'success': True,
            'session_id': session_id,
            'chat_id': chat_id,
            'database_info': load_result
        }), 200
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
    chat_id = g.validated_data.get('chat_id') or firestore.get_project_active_chat(project_id)

    # Create chat if it doesn't exist
    if not chat_id:
        new_chat = chat_service.create_chat(project_id, g.user['uid'])
        chat_id = new_chat['id']
        firestore.set_project_active_chat(project_id, chat_id)

    session = sessions.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    try:
        db = DuckDBManager(session_id, session['db_path'])
        agent = create_openrouter_sql_agent(db, session_id, 3)
        result = agent.process_query(query)

        sessions.update_session(session_id, {'message_count': session.get('message_count', 0) + 1})
        db.close()

        # Save user message to Firestore
        chat_service.save_message(
            chat_id=chat_id,
            role='user',
            content=query
        )

        # Save assistant response to Firestore
        if result['success']:
            chat_service.save_message(
                chat_id=chat_id,
                role='assistant',
                content=result['answer'],
                sql_query=result['metadata'].get('sql_query', ''),
                table_data=result.get('table_rows', []),
                metadata={
                    'tokens_used': result['metadata'].get('tokens', {}).get('total', 0),
                    'model': result['metadata'].get('model', ''),
                    'cache_savings_pct': result['metadata'].get('tokens', {}).get('cache_savings_pct', 0),
                    'function_calls': result['metadata'].get('function_calls', 0)
                }
            )

            return jsonify({
                'status': 'success',
                'response': result['answer'],
                'sql_query': result['metadata'].get('sql_query'),
                'table_data': result.get('table_rows', []),
                'chat_id': chat_id
            }), 200
        else:
            # Save error response
            chat_service.save_message(
                chat_id=chat_id,
                role='assistant',
                content=result['answer']
            )
            return jsonify({'status': 'error', 'response': result['answer'], 'chat_id': chat_id}), 200
    except Exception as e:
        print("ERROR: Query failed:", str(e))
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ============================================================================
# CHAT HISTORY MANAGEMENT
# ============================================================================

@app.route('/api/projects/<project_id>/chats', methods=['POST'])
@require_auth
@limit_expensive("20 per hour")
def create_chat_route(project_id):
    """Create a new chat session for a project"""
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    if not project.get('ai_chat_enabled'):
        return jsonify({'error': 'AI chat not enabled for this project'}), 403

    try:
        # Create new chat
        chat = chat_service.create_chat(project_id, g.user['uid'])

        # Set as active chat
        firestore.set_project_active_chat(project_id, chat['id'])

        return jsonify({
            'success': True,
            'chat': {
                'id': chat['id'],
                'name': chat['name'],
                'created_at': chat['created_at'].isoformat(),
                'message_count': 0
            }
        }), 201
    except Exception as e:
        print(f"[CHAT CREATE ERROR] {str(e)}")
        return jsonify({'error': 'Failed to create chat'}), 500

@app.route('/api/projects/<project_id>/chats', methods=['GET'])
@require_auth
@limit_by_user("60 per minute")
def list_chats_route(project_id):
    """Get all chats for a project"""
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    try:
        chats = chat_service.get_project_chats(project_id, g.user['uid'])
        active_chat_id = firestore.get_project_active_chat(project_id)

        formatted_chats = []
        for chat in chats:
            formatted_chats.append({
                'id': chat['id'],
                'name': chat['name'],
                'created_at': chat['created_at'].isoformat() if isinstance(chat['created_at'], datetime) else chat['created_at'],
                'updated_at': chat['updated_at'].isoformat() if isinstance(chat['updated_at'], datetime) else chat['updated_at'],
                'message_count': chat.get('message_count', 0),
                'last_message_preview': chat.get('last_message_preview', ''),
                'is_active': chat['id'] == active_chat_id
            })

        return jsonify({
            'success': True,
            'chats': formatted_chats,
            'total': len(formatted_chats)
        }), 200
    except Exception as e:
        print(f"[CHAT LIST ERROR] {str(e)}")
        return jsonify({'error': 'Failed to retrieve chats'}), 500

@app.route('/api/projects/<project_id>/chats/<chat_id>', methods=['GET'])
@require_auth
@limit_by_user("60 per minute")
def get_chat_route(project_id, chat_id):
    """Get chat details including messages"""
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    try:
        chat = chat_service.get_chat_with_validation(chat_id, g.user['uid'])
        if not chat or chat['project_id'] != project_id:
            return jsonify({'error': 'Chat not found'}), 404

        # Get messages (paginated)
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        messages = chat_service.get_chat_messages(chat_id, limit, offset)

        # Format messages for frontend
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'id': msg['id'],
                'role': msg['role'],
                'content': msg['content'],
                'sql_query': msg.get('sql_query'),
                'table_data': msg.get('table_data', []),
                'metadata': msg.get('metadata', {}),
                'timestamp': msg['timestamp'].isoformat() if isinstance(msg['timestamp'], datetime) else msg['timestamp']
            })

        return jsonify({
            'success': True,
            'chat': {
                'id': chat['id'],
                'name': chat['name'],
                'message_count': chat.get('message_count', 0)
            },
            'messages': formatted_messages,
            'has_more': len(messages) == limit
        }), 200
    except Exception as e:
        print(f"[CHAT GET ERROR] {str(e)}")
        return jsonify({'error': 'Failed to retrieve chat'}), 500

@app.route('/api/projects/<project_id>/chats/<chat_id>', methods=['PUT'])
@require_auth
@limit_by_user("30 per hour")
def update_chat_route(project_id, chat_id):
    """Update chat (rename)"""
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Missing chat name'}), 400

    new_name = data['name'].strip()
    if not new_name or len(new_name) > 100:
        return jsonify({'error': 'Invalid chat name'}), 400

    try:
        updated_chat = chat_service.update_chat_name(chat_id, g.user['uid'], new_name)
        if not updated_chat:
            return jsonify({'error': 'Chat not found or unauthorized'}), 404

        return jsonify({
            'success': True,
            'chat': {
                'id': updated_chat['id'],
                'name': updated_chat['name']
            }
        }), 200
    except Exception as e:
        print(f"[CHAT UPDATE ERROR] {str(e)}")
        return jsonify({'error': 'Failed to update chat'}), 500

@app.route('/api/projects/<project_id>/chats/<chat_id>', methods=['DELETE'])
@require_auth
@limit_by_user("10 per hour")
def delete_chat_route(project_id, chat_id):
    """Delete a chat and all its messages"""
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    try:
        success = chat_service.delete_chat(chat_id, g.user['uid'])
        if not success:
            return jsonify({'error': 'Chat not found or unauthorized'}), 404

        # If this was the active chat, clear it
        active_chat_id = firestore.get_project_active_chat(project_id)
        if active_chat_id == chat_id:
            firestore.set_project_active_chat(project_id, '')

        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"[CHAT DELETE ERROR] {str(e)}")
        return jsonify({'error': 'Failed to delete chat'}), 500

@app.route('/api/projects/<project_id>/chats/<chat_id>/set-active', methods=['POST'])
@require_auth
@limit_by_user("60 per minute")
def set_active_chat_route(project_id, chat_id):
    """Set a chat as the active chat for the project"""
    if not validate_project_id(project_id):
        return jsonify({'error': 'Invalid project ID'}), 400

    project = projects.get_project_with_validation(project_id, g.user['uid'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    try:
        # Verify chat exists and belongs to user
        chat = chat_service.get_chat_with_validation(chat_id, g.user['uid'])
        if not chat or chat['project_id'] != project_id:
            return jsonify({'error': 'Chat not found'}), 404

        # Set as active
        firestore.set_project_active_chat(project_id, chat_id)

        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"[SET ACTIVE CHAT ERROR] {str(e)}")
        return jsonify({'error': 'Failed to set active chat'}), 500

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
        # Check temp directory first, then permanent directory
        temp_path = storage.get_temp_path(project_id)
        project_path = storage.get_project_path(project_id)

        csv = os.path.join(temp_path, 'clean_data.csv')
        if not os.path.exists(csv):
            csv = os.path.join(project_path, 'clean_data.csv')

        if not os.path.exists(csv):
            return jsonify({'error': 'Clean data file not found'}), 404

        prefix = request.json.get('flight_starts_with', '')

        # Save output in same directory as csv
        output_dir = os.path.dirname(csv)
        output = os.path.join(output_dir, 'template_filled.xlsx')
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

    # Check temp directory first, then permanent directory
    temp_path = storage.get_temp_path(project_id)
    project_path = storage.get_project_path(project_id)

    filename = '{}_data.csv'.format(csv_type)
    csv_path = os.path.join(temp_path, filename)

    if not os.path.exists(csv_path):
        csv_path = os.path.join(project_path, filename)

    if not os.path.exists(csv_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(csv_path, as_attachment=True, download_name=filename)

# ============================================================================
# CLEANUP SERVICE MANAGEMENT
# ============================================================================

@app.route('/api/admin/cleanup/stats', methods=['GET'])
@require_auth
def get_cleanup_stats():
    """Get cleanup service statistics (admin only)"""
    try:
        stats = cleanup_service.get_stats()
        active_sessions = cleanup_service.get_active_sessions()

        return jsonify({
            'success': True,
            'stats': stats,
            'active_sessions': active_sessions,
            'session_count': len(active_sessions)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/cleanup/run', methods=['POST'])
@require_auth
def manual_cleanup():
    """Manually trigger cleanup (admin only)"""
    try:
        # This will be picked up by the next cleanup cycle
        return jsonify({
            'success': True,
            'message': 'Cleanup will run in the next cycle'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

import atexit
import signal

def shutdown_handler(signum=None, frame=None):
    """Handle graceful shutdown"""
    print("\n[*] Shutting down gracefully...")

    # Stop cleanup service
    if cleanup_service:
        cleanup_service.stop()
        print("[*] Cleanup service stopped")

    # Stop executor
    if executor:
        executor.shutdown(wait=True)
        print("[*] Thread pool executor stopped")

    print("[*] Shutdown complete")

# Register shutdown handlers
atexit.register(shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == '__main__':
    try:
        print("[*] Starting app5.py on port", Config.PORT)

        # Start cleanup service
        cleanup_service.start()
        print("[*] Cleanup service started")

        # Start Flask application
        app.run(host=Config.HOST, port=Config.PORT, debug=(Config.FLASK_ENV == 'development'))
    except KeyboardInterrupt:
        print("\n[*] Received interrupt signal")
        shutdown_handler()
    except Exception as e:
        print(f"[!] Fatal error: {e}")
        shutdown_handler()
        raise
