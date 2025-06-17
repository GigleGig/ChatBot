# RAG-Powered ChatBot System

A sophisticated chatbot built with **Retrieval-Augmented Generation (RAG)** capabilities, integrating LLM, LangChain, and vector databases for intelligent document-based conversations.

## 🚀 Features

- **🤖 Advanced RAG Architecture**: Combines document retrieval with LLM generation
- **📚 Multi-format Document Support**: PDF, DOCX, TXT, MD, HTML, JSON, CSV
- **🔍 GitHub Integration**: Real-time code search and repository analysis
- **⚡ Async Processing**: High-performance concurrent request handling
- **🔗 LangChain Integration**: Standardized LLM and document processing tools
- **💾 Vector Storage**: ChromaDB for persistent storage, FAISS for high-performance search
- **🗣️ Conversation Management**: Multi-turn conversation with memory
- **🛠️ Tool Integration**: Extensible tool system for external API calls

## 🏗️ Architecture

```
User Query → RAG System → Document Retrieval → LLM Processing → Response
                ↓              ↓                    ↓
         Conversation    Vector Database      OpenAI API
         Management      (ChromaDB/FAISS)    (GPT-3.5/GPT-4)
```

## 📋 Prerequisites

- Python 3.8+
- OpenAI API Key
- (Optional) GitHub Token for code search
- (Optional) Redis for production caching

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/GigleGig/ChatBot.git
   cd ChatBot
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
   cp env.example .env
   ```
   
   Edit the `.env` file with your configuration. **Quick Start**: You only need to set the 5 required variables - all others have sensible defaults! See [Environment Variables](#environment-variables) section for details.

## 🚀 Getting API Keys

**OpenAI API Key (Required):**
1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in to your OpenAI account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-`)
5. Add it to your `.env` file

**LangChain API Key (Required):**
1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Sign up for a LangSmith account
3. Go to Settings → API Keys
4. Create a new API key
5. Copy the key (starts with `lsv2_pt_`)
6. Add it to your `.env` file

**GitHub Token (Optional):**
1. Go to [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `public_repo`, `read:org`
4. Copy the token (starts with `ghp_`)
5. Add it to your `.env` file

## 🔐 Environment Variables

The system requires several environment variables for proper operation. Create a `.env` file in the root directory:

> **💡 Quick Start**: You only need to set the 5 **Required** variables to get started. All **Optional** variables have sensible defaults and can be customized later as needed.

### Required Variables (Must be set)

| Variable | Description | Example | Get From |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key for LLM access | `sk-proj-...` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `LANGCHAIN_API_KEY` | LangChain API key for tracing | `lsv2_pt_...` | [LangSmith](https://smith.langchain.com/) |
| `LANGCHAIN_TRACING_V2` | Enable LangChain tracing | `true` | Set to `true` |
| `LANGCHAIN_ENDPOINT` | LangChain tracing endpoint | `https://api.smith.langchain.com` | Default endpoint |
| `GITHUB_TOKEN` | GitHub personal access token | `ghp_...` | [GitHub Settings](https://github.com/settings/tokens) |

### Optional Variables (Have defaults)

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `MODEL_NAME` | OpenAI LLM model | `gpt-3.5-turbo` | Main language model |
| `TEMPERATURE` | LLM creativity setting | `0.1` | Range: 0.0-2.0 |
| `MAX_TOKENS` | Maximum response tokens | `1000` | Response length limit |
| `VECTOR_STORE_TYPE` | Vector database type | `chroma` | `chroma` or `faiss` |
| `COLLECTION_NAME` | Vector store collection | `code_agent_docs` | Database collection name |
| `PERSIST_DIRECTORY` | Vector store storage path | `./vector_store` | Database location |
| `CHUNK_SIZE` | Document chunk size | `1000` | Text splitting size |
| `CHUNK_OVERLAP` | Chunk overlap size | `200` | Context preservation |
| `AGENT_NAME` | Agent name | `CodeAgent` | Agent identifier |
| `MAX_ITERATIONS` | Maximum agent iterations | `10` | Agent execution limit |
| `MAX_EXECUTION_TIME` | Max execution time (seconds) | `60` | Timeout setting |
| `ENABLE_CODE_EXECUTION` | Enable code execution | `false` | Security setting |
| `ENABLE_FILE_OPERATIONS` | Enable file operations | `true` | File access permission |
| `ENABLE_WEB_SEARCH` | Enable web search | `false` | External search capability |
| `PROJECT_NAME` | Project name | `Code Agent RAG System` | Project identifier |
| `VERSION` | Project version | `1.0.0` | Version tracking |
| `DEBUG` | Debug mode | `false` | Development setting |
| `LOG_LEVEL` | Logging level | `INFO` | DEBUG, INFO, WARNING, ERROR |

### Environment Setup Examples

**Minimal Setup (.env file) - Just the essentials:**
```env
# Required - Only these 5 variables are needed to get started
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
LANGCHAIN_API_KEY=lsv2_pt_your-langchain-api-key-here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
GITHUB_TOKEN=ghp_your-github-token-here
```

**Development Setup (.env file) - With debugging:**
```env
# Required
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
LANGCHAIN_API_KEY=lsv2_pt_your-langchain-api-key-here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
GITHUB_TOKEN=ghp_your-github-token-here

# Optional - Development Configuration
MODEL_NAME=gpt-3.5-turbo
TEMPERATURE=0.1
MAX_TOKENS=1000
DEBUG=true
LOG_LEVEL=DEBUG
```

**Production Setup (.env file) - Optimized for performance:**
```env
# Required
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
LANGCHAIN_API_KEY=lsv2_pt_your-langchain-api-key-here
LANGCHAIN_TRACING_V2=false
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
GITHUB_TOKEN=ghp_your-github-token-here

# Optional - Production Configuration
MODEL_NAME=gpt-4
TEMPERATURE=0.5
MAX_TOKENS=2000
DEBUG=false
LOG_LEVEL=WARNING
ENABLE_WEB_SEARCH=true
```

## 🚀 Quick Start

1. **Basic Usage**
```bash
   python main_app.py
```

2. **Add documents to knowledge base**
```bash
   # Add a single document
   python main_app.py add-doc path/to/document.pdf

   # Add all documents from a directory
   python main_app.py add-dir path/to/documents/

   # Add text directly
   python main_app.py add-text "Your custom text content"
   ```

3. **Start interactive chat**
```bash
   python main_app.py chat
   ```

## 📁 Project Structure

```
ChatBot/
├── agent_core.py           # Core agent logic and tool management
├── vector_store.py         # Vector database implementations
├── document_processor.py   # Document loading and processing
├── llm_integration.py      # LLM and RAG chain management
├── github_search_tool.py   # GitHub API integration
├── main_app.py            # Main application and CLI
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
├── README.md             # This file
└── documents/            # Default document storage
    └── sample_document.txt
```

## 🔧 Configuration

The system uses a hierarchical configuration system:

1. **Environment Variables** (highest priority)
2. **Configuration Files** (`config.py`)
3. **Default Values** (lowest priority)

### Key Configuration Options

```python
# Vector Store Configuration
VECTOR_STORE_TYPE = "chroma"  # or "faiss"
COLLECTION_NAME = "code_agent_docs"
PERSIST_DIRECTORY = "./vector_store"

# LLM Configuration
MODEL_NAME = "gpt-3.5-turbo"  # or "gpt-4"
TEMPERATURE = 0.1
MAX_TOKENS = 1000

# Document Processing
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Agent Configuration
ENABLE_CODE_EXECUTION = False
ENABLE_FILE_OPERATIONS = True
ENABLE_WEB_SEARCH = False
```

## 🔌 API Usage

The system provides both CLI and programmatic interfaces:

### Python API
```python
from main_app import create_rag_application
import asyncio

async def main():
    # Initialize the application
    app = await create_rag_application()
    
    # Add documents
    await app.add_document("path/to/document.pdf", "file")
    
    # Chat with the system
    response = await app.chat("What is this document about?")
    print(response["response"])

asyncio.run(main())
```

### REST API (Optional)
```bash
# Start the web server
uvicorn main_app:app --host 0.0.0.0 --port 8000

# API endpoints will be available at:
# POST /chat - Send chat messages
# POST /documents - Upload documents
# GET /documents - List documents
# GET /health - Health check
```

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_agent_core.py
```

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production
- Set `DEBUG=false`
- Use `MODEL_NAME=gpt-4` for better quality
- Set appropriate `LOG_LEVEL=WARNING`
- Disable tracing: `LANGCHAIN_TRACING_V2=false`

## 📊 Performance Optimization

For high-traffic scenarios:

1. **Use Production LLM Settings**
   ```env
   MODEL_NAME=gpt-4
   TEMPERATURE=0.5
   MAX_TOKENS=2000
   ```

2. **Optimize Vector Store**
   ```env
   VECTOR_STORE_TYPE=faiss  # For better search performance
   PERSIST_DIRECTORY=/opt/vector_store  # Use faster disk
   ```

3. **Disable Development Features**
   ```env
   DEBUG=false
   LANGCHAIN_TRACING_V2=false
   LOG_LEVEL=WARNING
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/) for GPT models and embeddings
- [LangChain](https://github.com/langchain-ai/langchain) for the framework
- [ChromaDB](https://github.com/chroma-core/chroma) for vector storage
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/GigleGig/ChatBot/issues) page
2. Create a new issue with detailed information
3. Join our community discussions

---

**Note**: Make sure to keep your `.env` file secure and never commit it to version control. Always use the `env.example` file as a template. 