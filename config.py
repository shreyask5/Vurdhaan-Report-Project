# config.py - Updated for Ubuntu server
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '128000'))
    
    # Database settings - Updated for local DuckDB
    DATABASE_DIR = os.getenv('DATABASE_DIR', '/var/lib/duckdb/sessions')
    SESSION_TIMEOUT_HOURS = int(os.getenv('SESSION_TIMEOUT_HOURS', '24'))
    
    # Upload settings - Updated for server
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/home/ubuntu/project/uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '50485760'))  # 50MB for server
    
    # Redis settings (optional)
    REDIS_URL = os.getenv('REDIS_URL')
    
    # Server settings
    HOST = os.getenv('HOST', '0.0.0.0')  # Listen on all interfaces
    PORT = int(os.getenv('PORT', '5000'))
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/var/log/flight-analyzer/app.log')
    
    # Create necessary directories
    os.makedirs(DATABASE_DIR, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)