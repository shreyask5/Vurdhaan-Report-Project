from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Import configurations
from config import Config

# Import modules
from modules.session_manager import SessionManager
from modules.database import DuckDBManager
from modules.rag_engine import FlightOpsRAG
from modules.utils import setup_logging, validate_csv_file, format_query_results

# Import existing helpers
from helpers.clean import validate_and_process_file
from helpers.corsia import build_report

# Setup logging
setup_logging(Config.LOG_FILE, Config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize session manager
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

# Routes
@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('chat.html')

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    stats = session_manager.get_session_stats()
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'session_stats': stats
    }), 200

@app.route('/chat/initialize', methods=['POST'])
def initialize_chat_session():
    """Initialize new chat session with DuckDB and CSV data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['session_id', 'clean_data_csv', 'error_data_csv']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate CSV files exist
        clean_csv = data['clean_data_csv']
        error_csv = data['error_data_csv']
        
        # Validate clean CSV
        is_valid, message = validate_csv_file(clean_csv)
        if not is_valid:
            return jsonify({'error': f'Clean CSV validation failed: {message}'}), 400
        
        # Validate error CSV
        is_valid, message = validate_csv_file(error_csv)
        if not is_valid:
            return jsonify({'error': f'Error CSV validation failed: {message}'}), 400
        
        # Create session
        session_id, session_data = session_manager.create_session(clean_csv, error_csv)
        
        # Initialize DuckDB
        try:
            db_manager = DuckDBManager(session_id, session_data['db_path'])
            
            # Load CSV data
            load_result = db_manager.load_csv_data(clean_csv, error_csv)
            
            # Update session status
            session_manager.update_session(session_id, {
                'status': 'active',
                'database_info': load_result
            })
            
            # Close DB connection (will be reopened for each query)
            db_manager.close()
            
            return jsonify({
                'session_id': session_id,
                'status': 'initialized',
                'database_info': load_result,
                'expires_at': session_data['expires_at']
            }), 200
            
        except Exception as e:
            # Clean up on failure
            session_manager.delete_session(session_id)
            logger.error(f"Failed to initialize database: {e}")
            return jsonify({'error': f'Database initialization failed: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Failed to initialize chat session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat/<session_id>/query', methods=['POST'])
def process_chat_query(session_id):
    """Process natural language query via SQL-first RAG"""
    try:
        # Validate session
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Invalid or expired session'}), 404
        
        # Get query from request
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Log query
        logger.info(f"Processing query for session {session_id}: {query}")
        
        # Initialize database connection
        db_manager = DuckDBManager(session_id, session['db_path'])
        
        # Initialize RAG engine
        rag_engine = FlightOpsRAG(session_id, db_manager)
        
        # Process query
        result = rag_engine.process_query(query)
        
        # Update session
        session_manager.update_session(session_id, {
            'message_count': session.get('message_count', 0) + 1,
            'last_query': query
        })
        
        # Format results
        if result['status'] == 'success' and 'results' in result:
            result['results'] = format_query_results(
                result['results'], 
                max_rows=100
            )
        
        # Close database connection
        db_manager.close()
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Failed to process query: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'response': 'I encountered an error processing your query. Please try again.'
        }), 500

@app.route('/chat/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    """Get session status and database info"""
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session_id': session_id,
            'status': session.get('status', 'unknown'),
            'created_at': session.get('created_at'),
            'expires_at': session.get('expires_at'),
            'message_count': session.get('message_count', 0),
            'database_info': session.get('database_info', {})
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat/<session_id>/export', methods=['GET'])
def export_session(session_id):
    """Export session conversation history"""
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get conversation history from database
        db_manager = DuckDBManager(session_id, session['db_path'])
        
        # Create export data
        export_data = {
            'session_id': session_id,
            'created_at': session.get('created_at'),
            'exported_at': datetime.now().isoformat(),
            'database_info': session.get('database_info', {}),
            'message_count': session.get('message_count', 0)
        }
        
        db_manager.close()
        
        return jsonify(export_data), 200
        
    except Exception as e:
        logger.error(f"Failed to export session: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Flight Operations RAG Chat Server")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.FLASK_ENV == 'development'
    )