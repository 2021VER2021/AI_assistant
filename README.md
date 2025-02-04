# AI Agent with PDF RAG and Web Search

An AI-powered Telegram bot that answers questions using information from uploaded PDF documents and web searches. Uses Ollama's deepseek-r1:7b model for reasoning and response generation.

## Features

- PDF document processing and storage
- Semantic search in uploaded documents
- Domain-specific web search (arxiv.org and wikipedia.org)
- Chat history tracking with deletion capability
- User authentication
- RAG (Retrieval Augmented Generation) implementation

## Prerequisites

- Python 3.10+
- Ollama service running with deepseek-r1:7b model
- Telegram Bot Token (from @BotFather)

## Installation

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install python-telegram-bot sqlalchemy aiohttp langchain sentence-transformers pypdf2 duckduckgo-search
```

3. Set up environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
```

## Project Structure

```
src/
├── ai_agent/
│   └── agent.py          # AI agent core implementation
├── bot/
│   └── telegram_bot.py   # Telegram bot handler
├── database/
│   ├── db.py            # Database connection management
│   └── models.py        # SQLAlchemy models
├── utils/
│   ├── pdf_processor.py # PDF processing utilities
│   └── web_search.py    # Web search implementation
└── main.py              # Application entry point
```

## Usage

1. Start the Ollama service with the deepseek-r1:7b model:
```bash
ollama run deepseek-r1:7b
```

2. Run the bot:
```bash
python src/main.py
```

3. In Telegram:
   - Start a chat with your bot
   - Authenticate with: `/start 12345`
   - Send PDF documents (max 10MB)
   - Ask questions about the documents or any topic
   - Use `/delete` to clear your chat history

## Features in Detail

### PDF Processing
- Extracts text from PDF documents
- Splits text into semantic chunks
- Generates and stores embeddings for semantic search

### Question Answering
- Retrieves relevant chunks from uploaded PDFs
- Performs focused web searches on arxiv.org and wikipedia.org
- Combines information using the Ollama model
- Provides sourced responses with domain-specific references

### Chat Management
- Complete chat history tracking
- `/delete` command for clearing personal chat history
- All messages stored with timestamps

### Security
- Basic authentication with static password
- Per-user document and chat history isolation
- Secure chat history deletion

### Data Storage
- SQLite database for storing:
  - User information
  - Chat history
  - Document content and embeddings
  - Web search cache (24-hour expiration)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
