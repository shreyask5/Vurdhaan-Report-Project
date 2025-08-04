# config.py - Updated for Dual LLM Architecture

"""
Configuration class for Flight Data SQL Agent with Dual LLM support.
Add these settings to your existing Config class.
"""

import os
from typing import Optional

class Config:
    """Configuration class with dual LLM support"""
    
    # ========================================================================
    # EXISTING CONFIGURATION (keep your current settings)
    # ========================================================================
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_USER = os.getenv('DB_USER', 'app_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '1234')
    
    # Basic OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # ========================================================================
    # NEW: DUAL LLM ARCHITECTURE CONFIGURATION
    # ========================================================================
    
    # GPT-4.1 (Analysis Model) - for query analysis and improvement
    OPENAI_ANALYSIS_MODEL = os.getenv('OPENAI_ANALYSIS_MODEL', 'gpt-4.1')
    OPENAI_ANALYSIS_TEMPERATURE = float(os.getenv('OPENAI_ANALYSIS_TEMPERATURE', '0.1'))
    OPENAI_ANALYSIS_MAX_TOKENS = int(os.getenv('OPENAI_ANALYSIS_MAX_TOKENS', '1000'))
    
    # o4-mini (Execution Model) - for SQL generation and answer generation
    OPENAI_EXECUTION_MODEL = os.getenv('OPENAI_EXECUTION_MODEL', 'o4-mini')
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
        valid_analysis_models = ['gpt-4.1', 'gpt-4', 'gpt-4-0613']
        if cls.OPENAI_ANALYSIS_MODEL not in valid_analysis_models:
            errors.append(f"OPENAI_ANALYSIS_MODEL must be one of: {valid_analysis_models}")
        
        valid_execution_models = ['o4-mini', 'gpt-3.5-turbo', 'gpt-4o']
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