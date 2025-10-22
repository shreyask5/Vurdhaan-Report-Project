# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# test2.py - CLI Chat Interface for Gemini SQL Agent

"""
CLI Chat Interface for Testing Gemini SQL Agent

This script provides an interactive command-line interface for testing
the Gemini-powered SQL agent with real flight data.

Features:
- Multi-turn conversation support
- Conversation history tracking
- Summary generation
- Interactive commands

Usage:
    python test2.py
"""

import os
import sys
import logging
from datetime import datetime

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.database import PostgreSQLManager
from modules.sql_generator_open_router import create_open_router_sql_agent
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# File paths (adjust for your local environment if needed)
CLEAN_CSV_PATH = "/home/ubuntu/project/uploads/1b21b190-4f59-4d4b-8fe8-fc0932eea0d5/clean_data.csv"
ERROR_CSV_PATH = "/home/ubuntu/project/uploads/1b21b190-4f59-4d4b-8fe8-fc0932eea0d5/errors_data.csv"

# For Windows testing, use these paths instead:
CLEAN_CSV_PATH_WINDOWS = r"C:\chrome-win64\vurdhaan report project\github\Vurdhaan-Report-Project\uploads\1b21b190-4f59-4d4b-8fe8-fc0932eea0d5\clean_data.csv"
ERROR_CSV_PATH_WINDOWS = r"C:\chrome-win64\vurdhaan report project\github\Vurdhaan-Report-Project\uploads\1b21b190-4f59-4d4b-8fe8-fc0932eea0d5\errors_data.csv"

# Detect platform and use appropriate paths
if os.name == 'nt':  # Windows
    if os.path.exists(CLEAN_CSV_PATH_WINDOWS):
        CLEAN_CSV_PATH = CLEAN_CSV_PATH_WINDOWS
        ERROR_CSV_PATH = ERROR_CSV_PATH_WINDOWS


# ============================================================================
# CLI CHAT INTERFACE
# ============================================================================

class GeminiChatCLI:
    """Interactive CLI for Gemini SQL Agent"""

    def __init__(self):
        self.db_manager = None
        self.agent = None
        self.session_id = None
        self.message_count = 0

    def print_banner(self):
        """Print welcome banner"""
        print("\n" + "=" * 80)
        print("GEMINI SQL AGENT - FLIGHT DATA CHAT INTERFACE")
        print("=" * 80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API Key: {Config.GEMINI_API_KEY_1[:20] if Config.GEMINI_API_KEY_1 else 'NOT SET'}...")
        print(f"Model: {Config.GEMINI_MODEL}")
        print("=" * 80)
        print()

    def print_help(self):
        """Print help message"""
        print("\nAVAILABLE COMMANDS:")
        print("  * Type your question about flight data")
        print("  * /summary  - Get a summary of the conversation")
        print("  * /clear    - Clear conversation history")
        print("  * /help     - Show this help message")
        print("  * /quit     - Exit the chat")
        print("  * /exit     - Exit the chat")
        print()

    def initialize_database(self):
        """Initialize database and load CSV data"""
        try:
            # Create unique session ID
            self.session_id = f"cli_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            print(f"[*] Initializing database for session: {self.session_id}")
            print(f"[*] Clean CSV: {CLEAN_CSV_PATH}")
            print(f"[*] Error CSV: {ERROR_CSV_PATH}")

            # Check if files exist
            if not os.path.exists(CLEAN_CSV_PATH):
                raise FileNotFoundError(f"Clean CSV not found: {CLEAN_CSV_PATH}")
            if not os.path.exists(ERROR_CSV_PATH):
                raise FileNotFoundError(f"Error CSV not found: {ERROR_CSV_PATH}")

            # Create database manager
            self.db_manager = PostgreSQLManager(self.session_id)
            print(f"[+] Database created: {self.db_manager.db_name}")

            # Load CSV data
            print("[*] Loading CSV data...")
            load_result = self.db_manager.load_csv_data(CLEAN_CSV_PATH, ERROR_CSV_PATH)

            print(f"[+] Clean flights loaded: {load_result['clean_flights']['row_count']} rows")
            print(f"[+] Error flights loaded: {load_result['error_flights']['row_count']} rows")

            return True

        except Exception as e:
            print(f"[-] Database initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def initialize_agent(self):
        """Initialize Gemini SQL Agent"""
        try:
            print(f"[*] Initializing Gemini SQL Agent...")

            # Create agent with GEMINI_API_KEY_1
            self.agent = create_open_router_sql_agent(
                db_manager=self.db_manager,
                session_id=self.session_id,
                max_attempts=3,
                key="GEMINI_API_KEY_1"
            )

            print(f"[+] Gemini agent initialized with {Config.GEMINI_MODEL}")
            return True

        except Exception as e:
            print(f"[-] Agent initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def process_message(self, message: str):
        """Process user message"""
        try:
            self.message_count += 1

            print(f"\n[*] Processing message {self.message_count}...")
            print("-" * 80)

            # Process query
            result = self.agent.process_query(message)

            if result['success']:
                print(f"\nAssistant:\n")
                print(result['answer'])
                print()

                # Show metadata
                metadata = result.get('metadata', {})
                if metadata.get('function_calls', 0) > 0:
                    print(f"\n[*] Function calls made: {metadata['function_calls']}")
            else:
                print(f"\n[-] Error: {result.get('error', 'Unknown error')}")

            print("-" * 80)

        except Exception as e:
            print(f"\n[-] Error processing message: {e}")
            import traceback
            traceback.print_exc()

    def get_conversation_summary(self):
        """Get conversation summary"""
        try:
            print(f"\n[*] Generating conversation summary...")
            print("-" * 80)

            summary = self.agent.get_conversation_summary()

            print(f"\nCONVERSATION SUMMARY:\n")
            print(summary)
            print()
            print("-" * 80)

        except Exception as e:
            print(f"\n[-] Error generating summary: {e}")

    def clear_history(self):
        """Clear conversation history"""
        try:
            self.agent.clear_history()
            self.message_count = 0
            print("\n[+] Conversation history cleared")
        except Exception as e:
            print(f"\n[-] Error clearing history: {e}")

    def run(self):
        """Run the chat interface"""
        self.print_banner()

        # Initialize database
        if not self.initialize_database():
            print("\n[-] Failed to initialize database. Exiting.")
            return

        # Initialize agent
        if not self.initialize_agent():
            print("\n[-] Failed to initialize agent. Exiting.")
            return

        # Print help
        self.print_help()

        # Main chat loop
        print("[*] Chat started. Type your questions or commands.\n")

        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                # Process commands
                if user_input.lower() in ['/quit', '/exit']:
                    print("\n[*] Goodbye!")
                    break

                elif user_input.lower() == '/help':
                    self.print_help()

                elif user_input.lower() == '/summary':
                    self.get_conversation_summary()

                elif user_input.lower() == '/clear':
                    self.clear_history()

                else:
                    # Process regular message
                    self.process_message(user_input)

            except KeyboardInterrupt:
                print("\n\n[*] Interrupted. Goodbye!")
                break

            except EOFError:
                print("\n\n[*] EOF. Goodbye!")
                break

            except Exception as e:
                print(f"\n[-] Unexpected error: {e}")
                import traceback
                traceback.print_exc()

        # Cleanup
        try:
            if self.agent:
                self.agent.close()
            if self.db_manager:
                self.db_manager.close()
            print("\n[+] Cleanup completed")
        except Exception as e:
            print(f"\n[!] Cleanup error: {e}")


# ============================================================================
# SAMPLE QUERIES FOR TESTING
# ============================================================================

SAMPLE_QUERIES = [
    "What tables are available in the database?",
    "Give me a summary of the error flights",
    "What are the top 5 most common routes?",
    "Show me fuel consumption statistics",
    "Which aircraft has the most flights?",
    "What are the most common types of errors?",
    "Compare fuel efficiency across different routes",
    "Show me flights from the last week",
    "What's the average fuel consumption per flight?",
    "Tell me about data quality issues"
]


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""

    # Check if API key is set
    if not Config.GEMINI_API_KEY_1:
        print("\n[-] ERROR: GEMINI_API_KEY_1 not found in environment")
        print("Please set GEMINI_API_KEY_1 in your .env file")
        print("\nExample:")
        print("GEMINI_API_KEY_1=your_api_key_here")
        sys.exit(1)

    # Check if model is configured
    print(f"\n[+] Using Gemini model: {Config.GEMINI_MODEL}")

    # Show sample queries
    print("\nSAMPLE QUERIES YOU CAN TRY:")
    for i, query in enumerate(SAMPLE_QUERIES[:5], 1):
        print(f"  {i}. {query}")
    print()

    # Create and run CLI
    cli = GeminiChatCLI()
    cli.run()


if __name__ == "__main__":
    main()
