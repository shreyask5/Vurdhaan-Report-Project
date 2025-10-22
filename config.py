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

    # Google Gemini API Keys (multiple keys support)
    GEMINI_API_KEY_1 = os.getenv('GEMINI_API_KEY_1')
    GEMINI_API_KEY_2 = os.getenv('GEMINI_API_KEY_2')
    GEMINI_API_KEY_3 = os.getenv('GEMINI_API_KEY_3')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.1'))
    GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '8192'))

    # OpenRouter API Configuration
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'google/gemini-2.5-pro')
    OPENROUTER_TEMPERATURE = float(os.getenv('OPENROUTER_TEMPERATURE', '0.1'))
    OPENROUTER_MAX_TOKENS = int(os.getenv('OPENROUTER_MAX_TOKENS', '8192'))

    # OpenRouter metadata (optional, for tracking and rankings)
    OPENROUTER_SITE_URL = os.getenv('OPENROUTER_SITE_URL', 'http://localhost:5002')
    OPENROUTER_APP_NAME = os.getenv('OPENROUTER_APP_NAME', 'Vurdhaan Flight Analyzer')

    # OpenRouter caching configuration
    OPENROUTER_ENABLE_CACHING = os.getenv('OPENROUTER_ENABLE_CACHING', 'true').lower() == 'true'
    
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
    PORT = int(os.getenv('PORT', '5002'))
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/var/log/flight-analyzer/app.log')
    
    # ------------------------------------------------------------------------
    # Rate Limiting (toggleable for testing)
    # ------------------------------------------------------------------------
    # Set to False during testing to disable all rate limits
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'false').lower() == 'true'
    # Global default limits when enabled; can be overridden per-route
    # Example env format: "120 per minute|2000 per hour"
    _rl_defaults_env = os.getenv('RATELIMIT_DEFAULT_LIMITS')
    if _rl_defaults_env:
        RATELIMIT_DEFAULT_LIMITS = [part.strip() for part in _rl_defaults_env.split('|') if part.strip()]
    else:
        RATELIMIT_DEFAULT_LIMITS = ["120 per minute"]
    # Storage backend for Flask-Limiter (use Redis in production)
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')
    
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

        # Check required settings (at least one API key)
        if not cls.OPENAI_API_KEY and not cls.GEMINI_API_KEY_1:
            errors.append("Either OPENAI_API_KEY or GEMINI_API_KEY_1 is required")

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
        print(f"\n⏱️ RATE LIMITING:")
        print(f"   Enabled: {cls.RATELIMIT_ENABLED}")
        print(f"   Default Limits: {cls.RATELIMIT_DEFAULT_LIMITS}")
        print(f"   Storage URI: {cls.RATELIMIT_STORAGE_URI}")
        
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
