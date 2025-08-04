#!/usr/bin/env python3
"""
Debug script to help identify .env loading issues
Run this before your main application to verify environment variables are loaded correctly.
"""

import os
import sys
from pathlib import Path

def debug_env_loading():
    """Debug environment variable loading"""
    
    print("🔍 ENVIRONMENT VARIABLE DEBUGGING")
    print("=" * 60)
    
    # Check current working directory
    print(f"📁 Current working directory: {os.getcwd()}")
    
    # Check if .env file exists
    env_file = Path('.env')
    if env_file.exists():
        print(f"✅ .env file found: {env_file.absolute()}")
        print(f"📏 .env file size: {env_file.stat().st_size} bytes")
        
        # Read and display .env content (safely)
        try:
            with open('.env', 'r') as f:
                lines = f.readlines()
            
            print(f"\n📋 .env file content ({len(lines)} lines):")
            for i, line in enumerate(lines[:20], 1):  # Show first 20 lines
                line = line.strip()
                if line and not line.startswith('#'):
                    # Mask sensitive values
                    if 'API_KEY' in line or 'PASSWORD' in line:
                        key, _, value = line.partition('=')
                        if len(value) > 10:
                            masked_value = f"{value[:5]}...{value[-3:]}"
                        else:
                            masked_value = "***"
                        print(f"   {i:2d}: {key}={masked_value}")
                    else:
                        print(f"   {i:2d}: {line}")
                elif line.startswith('#'):
                    print(f"   {i:2d}: {line[:50]}...")
            
            if len(lines) > 20:
                print(f"   ... and {len(lines) - 20} more lines")
                
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print(f"❌ .env file not found in current directory")
        
        # Look for .env in parent directories
        current_path = Path.cwd()
        for parent in current_path.parents:
            env_in_parent = parent / '.env'
            if env_in_parent.exists():
                print(f"🔍 Found .env in parent directory: {env_in_parent}")
                break
    
    print(f"\n" + "=" * 60)
    
    # Try loading dotenv
    print("📦 Testing python-dotenv loading...")
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
        
        # Try loading .env
        result = load_dotenv()
        print(f"📄 load_dotenv() result: {result}")
        
        # Try loading with verbose output
        result_verbose = load_dotenv(verbose=True)
        print(f"📄 load_dotenv(verbose=True) result: {result_verbose}")
        
    except ImportError:
        print("❌ python-dotenv not installed")
        print("   Install with: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"❌ Error loading .env: {e}")
        return False
    
    print(f"\n" + "=" * 60)
    
    # Check specific environment variables
    print("🔑 Checking key environment variables...")
    
    key_vars = [
        'OPENAI_API_KEY',
        'OPENAI_MODEL', 
        'OPENAI_MAX_TOKENS',
        'OPENAI_ANALYSIS_MODEL',
        'OPENAI_EXECUTION_MODEL',
    ]
    
    for var in key_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'API_KEY' in var or 'SECRET' in var:
                if len(value) > 10:
                    masked_value = f"{value[:5]}...{value[-3:]}"
                else:
                    masked_value = "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    print(f"\n" + "=" * 60)
    
    # Test import of config
    print("⚙️  Testing config.py import...")
    try:
        # Add current directory to path if needed
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
            
        from config import Config
        print("✅ config.py imported successfully")
        
        # Test validation
        try:
            Config.validate_config()
            print("✅ Configuration validation passed")
            
            # Print model info
            model_info = Config.get_model_info()
            print(f"\n🤖 Configured models:")
            print(f"   Analysis: {model_info['analysis_model']['name']}")
            print(f"   Execution: {model_info['execution_model']['name']}")
            
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import config.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing config: {e}")
        return False
    
    print(f"\n✅ All checks passed! Your environment is ready.")
    return True


if __name__ == "__main__":
    success = debug_env_loading()
    if not success:
        print(f"\n❌ Environment setup has issues. Please fix them before running your application.")
        sys.exit(1)
    else:
        print(f"\n🚀 Environment setup is working correctly!")
        sys.exit(0)