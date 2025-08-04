# config.py - Updated for Ubuntu server with Dual LLM Architecture
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # ========================================================================
    # EXISTING CONFIGURATION (BACKWARD COMPATIBLE)
    # ========================================================================
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    
    # OpenAI settings (existing)
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
    
    # ========================================================================
    # NEW: DUAL LLM ARCHITECTURE CONFIGURATION
    # ========================================================================
    
    # GPT-4.1 (Analysis Model) - for query analysis and improvement
    OPENAI_ANALYSIS_MODEL = os.getenv('OPENAI_ANALYSIS_MODEL', 'gpt-4-turbo')
    OPENAI_ANALYSIS_TEMPERATURE = float(os.getenv('OPENAI_ANALYSIS_TEMPERATURE', '0.1'))
    OPENAI_ANALYSIS_MAX_TOKENS = int(os.getenv('OPENAI_ANALYSIS_MAX_TOKENS', '1000'))
    
    # GPT-4o-mini (Execution Model) - for SQL generation and answer generation
    OPENAI_EXECUTION_MODEL = os.getenv('OPENAI_EXECUTION_MODEL', OPENAI_MODEL)  # Default to existing model
    OPENAI_EXECUTION_TEMPERATURE = float(os.getenv('OPENAI_EXECUTION_TEMPERATURE', '0.1'))
    OPENAI_EXECUTION_MAX_TOKENS = int(os.getenv('OPENAI_EXECUTION_MAX_TOKENS', str(OPENAI_MAX_TOKENS)))
    
    # Answer generation temperature (for more natural responses)
    OPENAI_ANSWER_TEMPERATURE = float(os.getenv('OPENAI_ANSWER_TEMPERATURE', '0.3'))
    
    # ========================================================================
    # DUAL LLM WORKFLOW CONFIGURATION
    # ========================================================================
    
    # Enable/disable dual LLM workflow
    ENABLE_DUAL_LLM = os.getenv('ENABLE_DUAL_LLM', 'true').lower() == 'true'
    ENABLE_QUERY_ANALYSIS = os.getenv('ENABLE_QUERY_ANALYSIS', 'true').lower() == 'true'
    ENABLE_QUERY_IMPROVEMENT = os.getenv('ENABLE_QUERY_IMPROVEMENT', 'true').lower() == 'true'
    
    # Fallback settings
    ANALYSIS_FALLBACK_ENABLED = os.getenv('ANALYSIS_FALLBACK_ENABLED', 'true').lower() == 'true'
    
    # Caching settings
    CACHE_QUERY_ANALYSIS = os.getenv('CACHE_QUERY_ANALYSIS', 'true').lower() == 'true'
    ANALYSIS_CACHE_TTL = int(os.getenv('ANALYSIS_CACHE_TTL', '1800'))  # 30 minutes
    
    # ========================================================================
    # SQL AGENT CONFIGURATION
    # ========================================================================
    
    # SQL Agent settings
    MAX_SQL_ATTEMPTS = int(os.getenv('MAX_SQL_ATTEMPTS', '3'))
    DEFAULT_QUERY_LIMIT = int(os.getenv('DEFAULT_QUERY_LIMIT', '1000'))
    MAX_QUERY_ROWS = int(os.getenv('MAX_QUERY_ROWS', '10000'))
    MAX_SAMPLE_ROWS = int(os.getenv('MAX_SAMPLE_ROWS', '50'))
    
    # PostgreSQL Configuration (if using PostgreSQL)
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', 'flight_data')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # API Settings
    OPENAI_TIMEOUT = int(os.getenv('OPENAI_TIMEOUT', '60'))
    OPENAI_MAX_RETRIES = int(os.getenv('OPENAI_MAX_RETRIES', '3'))
    
    # ========================================================================
    # DIRECTORY CREATION (EXISTING)
    # ========================================================================
    
    # Create necessary directories
    os.makedirs(DATABASE_DIR, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # ========================================================================
    # VALIDATION AND UTILITY METHODS
    # ========================================================================
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate the configuration"""
        errors = []
        
        # Check required settings
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        # Validate API key format (should start with sk-)
        if cls.OPENAI_API_KEY and not cls.OPENAI_API_KEY.startswith('sk-'):
            errors.append("OPENAI_API_KEY should start with 'sk-'")
        
        # Validate temperature ranges
        if not 0.0 <= cls.OPENAI_ANALYSIS_TEMPERATURE <= 1.0:
            errors.append("OPENAI_ANALYSIS_TEMPERATURE must be between 0.0 and 1.0")
        
        if not 0.0 <= cls.OPENAI_EXECUTION_TEMPERATURE <= 1.0:
            errors.append("OPENAI_EXECUTION_TEMPERATURE must be between 0.0 and 1.0")
        
        # Check directory permissions
        try:
            if not os.access(cls.UPLOAD_FOLDER, os.W_OK):
                errors.append(f"No write permission for UPLOAD_FOLDER: {cls.UPLOAD_FOLDER}")
        except:
            errors.append(f"Cannot access UPLOAD_FOLDER: {cls.UPLOAD_FOLDER}")
        
        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")
        
        return True
    
    @classmethod
    def get_model_info(cls) -> dict:
        """Get information about the configured models"""
        return {
            "analysis_model": {
                "name": cls.OPENAI_ANALYSIS_MODEL,
                "temperature": cls.OPENAI_ANALYSIS_TEMPERATURE,
                "max_tokens": cls.OPENAI_ANALYSIS_MAX_TOKENS,
                "purpose": "Query analysis and improvement"
            },
            "execution_model": {
                "name": cls.OPENAI_EXECUTION_MODEL,
                "temperature": cls.OPENAI_EXECUTION_TEMPERATURE,
                "max_tokens": cls.OPENAI_EXECUTION_MAX_TOKENS,
                "purpose": "SQL generation and answer generation"
            },
            "legacy_model": {
                "name": cls.OPENAI_MODEL,
                "max_tokens": cls.OPENAI_MAX_TOKENS,
                "purpose": "Backward compatibility"
            },
            "dual_llm_enabled": cls.ENABLE_DUAL_LLM,
            "query_analysis_enabled": cls.ENABLE_QUERY_ANALYSIS
        }
    
    @classmethod
    def print_config_summary(cls):
        """Print a summary of the current configuration"""
        print("=" * 60)
        print("🔧 CONFIGURATION SUMMARY")
        print("=" * 60)
        
        # API Key status
        if cls.OPENAI_API_KEY:
            masked_key = f"{cls.OPENAI_API_KEY[:10]}...{cls.OPENAI_API_KEY[-5:]}"
            print(f"✅ OpenAI API Key: {masked_key}")
        else:
            print("❌ OpenAI API Key: NOT SET")
        
        # Model configuration
        print(f"\n🤖 MODEL CONFIGURATION:")
        print(f"   Analysis Model: {cls.OPENAI_ANALYSIS_MODEL}")
        print(f"   Execution Model: {cls.OPENAI_EXECUTION_MODEL}")
        print(f"   Legacy Model: {cls.OPENAI_MODEL}")
        print(f"   Dual LLM Enabled: {cls.ENABLE_DUAL_LLM}")
        
        # Paths
        print(f"\n📁 PATHS:")
        print(f"   Database Dir: {cls.DATABASE_DIR}")
        print(f"   Upload Folder: {cls.UPLOAD_FOLDER}")
        print(f"   Log File: {cls.LOG_FILE}")
        
        # Server settings
        print(f"\n🌐 SERVER:")
        print(f"   Host: {cls.HOST}")
        print(f"   Port: {cls.PORT}")
        print(f"   Environment: {cls.FLASK_ENV}")
        
        print("=" * 60)


# ========================================================================
# STARTUP VALIDATION
# ========================================================================

if __name__ == "__main__":
    try:
        # Print configuration summary
        Config.print_config_summary()
        
        # Validate configuration
        Config.validate_config()
        print("✅ Configuration validated successfully")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)# config.py - Updated for Dual LLM Architecture

"""
Configuration class for Flight Data SQL Agent with Dual LLM support.
Add these settings to your existing Config class.
"""

import os
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("    Or set environment variables manually.")

class Config:
    """Configuration class with dual LLM support"""
    
    # ========================================================================
    # EXISTING CONFIGURATION (keep your current settings)
    # ========================================================================
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'flight_data')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    
    # Basic OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # ========================================================================
    # NEW: DUAL LLM ARCHITECTURE CONFIGURATION
    # ========================================================================
    
    # GPT-4.1 (Analysis Model) - for query analysis and improvement
    OPENAI_ANALYSIS_MODEL = os.getenv('OPENAI_ANALYSIS_MODEL', 'gpt-4-turbo')
    OPENAI_ANALYSIS_TEMPERATURE = float(os.getenv('OPENAI_ANALYSIS_TEMPERATURE', '0.1'))
    OPENAI_ANALYSIS_MAX_TOKENS = int(os.getenv('OPENAI_ANALYSIS_MAX_TOKENS', '1000'))
    
    # GPT-4o-mini (Execution Model) - for SQL generation and answer generation
    OPENAI_EXECUTION_MODEL = os.getenv('OPENAI_EXECUTION_MODEL', 'gpt-4o-mini')
    OPENAI_EXECUTION_TEMPERATURE = float(os.getenv('OPENAI_EXECUTION_TEMPERATURE', '0.1'))
    OPENAI_EXECUTION_MAX_TOKENS = int(os.getenv('OPENAI_EXECUTION_MAX_TOKENS', '4096'))
    
    # Answer generation (uses execution model with higher temperature)
    OPENAI_ANSWER_TEMPERATURE = float(os.getenv('OPENAI_ANSWER_TEMPERATURE', '0.3'))
    
    # ========================================================================
    # WORKFLOW CONFIGURATION
    # ========================================================================
    
    # Enable/disable dual LLM workflow
    ENABLE_DUAL_LLM = os.getenv('ENABLE_DUAL_LLM', 'true').lower() == 'true'
    ENABLE_QUERY_ANALYSIS = os.getenv('ENABLE_QUERY_ANALYSIS', 'true').lower() == 'true'
    ENABLE_QUERY_IMPROVEMENT = os.getenv('ENABLE_QUERY_IMPROVEMENT', 'true').lower() == 'true'
    
    # Fallback settings
    ANALYSIS_FALLBACK_ENABLED = os.getenv('ANALYSIS_FALLBACK_ENABLED', 'true').lower() == 'true'
    
    # Caching settings
    CACHE_QUERY_ANALYSIS = os.getenv('CACHE_QUERY_ANALYSIS', 'true').lower() == 'true'
    ANALYSIS_CACHE_TTL = int(os.getenv('ANALYSIS_CACHE_TTL', '1800'))  # 30 minutes
    
    # ========================================================================
    # LEGACY COMPATIBILITY (for backward compatibility)
    # ========================================================================
    
    # These maintain compatibility with existing code
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', OPENAI_EXECUTION_MODEL)
    OPENAI_TEMPERATURE = OPENAI_EXECUTION_TEMPERATURE
    OPENAI_MAX_TOKENS = OPENAI_EXECUTION_MAX_TOKENS
    
    # ========================================================================
    # API AND PERFORMANCE SETTINGS
    # ========================================================================
    
    # Request timeouts
    OPENAI_TIMEOUT = int(os.getenv('OPENAI_TIMEOUT', '60'))
    OPENAI_MAX_RETRIES = int(os.getenv('OPENAI_MAX_RETRIES', '3'))
    
    # Query limits
    MAX_SQL_ATTEMPTS = int(os.getenv('MAX_SQL_ATTEMPTS', '3'))
    DEFAULT_QUERY_LIMIT = int(os.getenv('DEFAULT_QUERY_LIMIT', '1000'))
    MAX_QUERY_ROWS = int(os.getenv('MAX_QUERY_ROWS', '10000'))
    MAX_SAMPLE_ROWS = int(os.getenv('MAX_SAMPLE_ROWS', '50'))
    
    # ========================================================================
    # LOGGING CONFIGURATION
    # ========================================================================
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_SQL_QUERIES = os.getenv('LOG_SQL_QUERIES', 'true').lower() == 'true'
    LOG_PERFORMANCE = os.getenv('LOG_PERFORMANCE', 'true').lower() == 'true'
    
    # ========================================================================
    # VALIDATION METHOD
    # ========================================================================
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate the configuration"""
        errors = []
        
        # Check required settings
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        if not cls.DB_PASSWORD:
            errors.append("DB_PASSWORD is required")
        
        # Validate model names
        valid_analysis_models = ['gpt-4-turbo', 'gpt-4', 'gpt-4-0613']
        if cls.OPENAI_ANALYSIS_MODEL not in valid_analysis_models:
            errors.append(f"OPENAI_ANALYSIS_MODEL must be one of: {valid_analysis_models}")
        
        valid_execution_models = ['gpt-4o-mini', 'gpt-3.5-turbo', 'gpt-4o']
        if cls.OPENAI_EXECUTION_MODEL not in valid_execution_models:
            errors.append(f"OPENAI_EXECUTION_MODEL must be one of: {valid_execution_models}")
        
        # Validate temperature ranges
        if not 0.0 <= cls.OPENAI_ANALYSIS_TEMPERATURE <= 1.0:
            errors.append("OPENAI_ANALYSIS_TEMPERATURE must be between 0.0 and 1.0")
        
        if not 0.0 <= cls.OPENAI_EXECUTION_TEMPERATURE <= 1.0:
            errors.append("OPENAI_EXECUTION_TEMPERATURE must be between 0.0 and 1.0")
        
        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")
        
        return True
    
    @classmethod
    def get_model_info(cls) -> dict:
        """Get information about the configured models"""
        return {
            "analysis_model": {
                "name": cls.OPENAI_ANALYSIS_MODEL,
                "temperature": cls.OPENAI_ANALYSIS_TEMPERATURE,
                "max_tokens": cls.OPENAI_ANALYSIS_MAX_TOKENS,
                "purpose": "Query analysis and improvement"
            },
            "execution_model": {
                "name": cls.OPENAI_EXECUTION_MODEL,
                "temperature": cls.OPENAI_EXECUTION_TEMPERATURE,
                "max_tokens": cls.OPENAI_EXECUTION_MAX_TOKENS,
                "purpose": "SQL generation and answer generation"
            },
            "dual_llm_enabled": cls.ENABLE_DUAL_LLM,
            "query_analysis_enabled": cls.ENABLE_QUERY_ANALYSIS
        }


# ========================================================================
# USAGE EXAMPLE
# ========================================================================

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Validate configuration
    try:
        Config.validate_config()
        print("✅ Configuration validated successfully")
        
        # Print model information
        model_info = Config.get_model_info()
        print(f"\n🤖 Model Configuration:")
        print(f"   Analysis Model: {model_info['analysis_model']['name']}")
        print(f"   Execution Model: {model_info['execution_model']['name']}")
        print(f"   Dual LLM Enabled: {model_info['dual_llm_enabled']}")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        exit(1)