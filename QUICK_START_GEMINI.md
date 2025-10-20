# Quick Start Guide - Gemini SQL Agent

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
pip install google-generativeai
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Environment

Create/edit `.env` file in project root:

```bash
# Gemini API Key (get from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY_1=AIzaSy...your_actual_key_here

# PostgreSQL Configuration (if not already set)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=app_user
POSTGRES_PASSWORD=1234
```

**⚠️ Important**: No quotes around the API key!

### Step 3: Verify Configuration

```bash
python -c "from config import Config; print(f'API Key: {Config.GEMINI_API_KEY_1[:20]}...' if Config.GEMINI_API_KEY_1 else 'NOT SET')"
```

Should output: `API Key: AIzaSy...`

### Step 4: Run the CLI Chat

```bash
python test2.py
```

### Step 5: Try a Query

```
You: What tables are available in the database?
```

That's it! 🎉

---

## 📖 Common Commands

### In the Chat Interface

| Command | Description |
|---------|-------------|
| `Your question here` | Ask about flight data |
| `/help` | Show available commands |
| `/summary` | Get conversation summary |
| `/clear` | Clear conversation history |
| `/quit` or `/exit` | Exit the chat |

---

## 💡 Example Queries

### 1. Data Overview
```
What tables are in the database?
Tell me about the clean_flights table
Give me a summary of errors
```

### 2. Flight Analysis
```
What are the top 10 routes by flight count?
Show me fuel consumption statistics
Which aircraft has the most flights?
```

### 3. Specific Questions
```
What's the average fuel consumption per flight?
Which route is most fuel efficient?
Show me flights from KJFK to EGLL
```

### 4. Multi-Turn Conversation
```
1. What are the most common routes?
2. Show fuel consumption for those routes
3. Which one is most efficient?
4. /summary
```

---

## 🔧 Programmatic Usage

### Basic Example

```python
from modules.database import PostgreSQLManager
from modules.sql_generator_gemini import create_gemini_sql_agent

# Setup
session_id = "my_test_session"
db = PostgreSQLManager(session_id)
db.load_csv_data("clean_data.csv", "errors_data.csv")

# Create agent
agent = create_gemini_sql_agent(db, session_id)

# Ask questions
result = agent.process_query("What are the top 5 routes?")
print(result['answer'])

# Cleanup
agent.close()
db.close()
```

### With API Key Selection

```python
# Use a different API key
agent = create_gemini_sql_agent(
    db_manager=db,
    session_id=session_id,
    key="GEMINI_API_KEY_2"  # Use second key
)
```

---

## ❌ Troubleshooting

### Problem: "API key not found"
**Solution**: Add `GEMINI_API_KEY_1` to `.env` (no quotes!)

### Problem: "CSV files not found"
**Solution**: Update paths in `test2.py` lines 34-35

### Problem: "Cannot connect to PostgreSQL"
**Solution**: Check PostgreSQL is running:
```bash
# Ubuntu/Linux
sudo systemctl status postgresql

# Windows
# Check Services for "postgresql" service
```

### Problem: "Import error: google.generativeai"
**Solution**:
```bash
pip install google-generativeai --upgrade
```

---

## 📊 Expected Output

### Successful Initialization
```
🚀 GEMINI SQL AGENT - FLIGHT DATA CHAT INTERFACE
================================================================================
📅 2025-01-XX 14:30:00
🔑 API Key: AIzaSyBr...
🧠 Model: gemini-2.5-pro
================================================================================

📊 Initializing database for session: cli_chat_20250120_143000
✅ Database created: session_cli_chat_20250120_143000
📥 Loading CSV data...
✅ Clean flights loaded: 1234 rows
✅ Error flights loaded: 56 rows
🤖 Initializing Gemini SQL Agent...
✅ Gemini agent initialized with gemini-2.5-pro

💡 SAMPLE QUERIES YOU CAN TRY:
  1. What tables are available in the database?
  2. Give me a summary of the error flights
  3. What are the top 5 most common routes?
  4. Show me fuel consumption statistics
  5. Which aircraft has the most flights?

💬 Chat started. Type your questions or commands.

You:
```

### Example Response
```
You: What are the top 5 routes?

⏳ Processing message 1...
────────────────────────────────────────────────────────────────────────────────

🤖 Assistant:

Based on the flight data, here are the top 5 routes by flight count:

1. **KJFK → EGLL** (New York JFK to London Heathrow)
   - 145 flights
   - Average fuel consumption: 12,450 kg

2. **EGLL → KJFK** (London Heathrow to New York JFK)
   - 142 flights
   - Average fuel consumption: 11,890 kg

3. **EDDF → KJFK** (Frankfurt to New York JFK)
   - 98 flights
   - Average fuel consumption: 13,120 kg

... [detailed analysis continues]

📊 Function calls made: 1
────────────────────────────────────────────────────────────────────────────────
```

---

## 🎯 Next Steps

1. **Try the sample queries** above
2. **Experiment with multi-turn conversations**
3. **Use `/summary`** to see conversation recap
4. **Integrate into your app** (see `GEMINI_IMPLEMENTATION.md`)

---

## 🆘 Need Help?

- **Full Documentation**: See `GEMINI_IMPLEMENTATION.md`
- **Gemini API Docs**: https://ai.google.dev/gemini-api/docs
- **Function Calling**: https://ai.google.dev/gemini-api/docs/function-calling

---

**Ready to go!** Run `python test2.py` and start chatting with your flight data! 🛫
