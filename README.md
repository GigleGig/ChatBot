# RAG-Powered ChatBot System

A sophisticated chatbot built with **Retrieval-Augmented Generation (RAG)** capabilities, integrating LLM, LangChain, and GitHub search for intelligent document-based conversations.

## 🚀 Features

- **🤖 RAG Architecture**: Combines document retrieval with LLM generation
- **📚 Document Support**: PDF, DOCX, TXT, MD file processing
- **🔍 GitHub Integration**: Real-time code search and repository analysis
- **🔗 LangChain Integration**: Standardized LLM and document processing
- **💾 Vector Storage**: ChromaDB for document embeddings
- **🗣️ Conversation Management**: Interactive chat interface
- **🛠️ Tool Integration**: GitHub search tool for code queries

## 📋 Prerequisites

- Python 3.8+
- OpenAI API Key
- LangChain API Key
- GitHub Token (for code search)

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
   
   Edit the `.env` file with your API keys. You only need to set the 5 required variables.

## 🚀 Getting API Keys

**OpenAI API Key:**
1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create a new secret key
3. Add it to your `.env` file

**LangChain API Key:**
1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Create an API key
3. Add it to your `.env` file

**GitHub Token:**
1. Go to [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. Generate a new token with `public_repo` scope
3. Add it to your `.env` file

## 🔐 Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-proj-...` |
| `LANGCHAIN_API_KEY` | LangChain API key for tracing | `lsv2_pt_...` |
| `LANGCHAIN_TRACING_V2` | Enable LangChain tracing | `true` |
| `LANGCHAIN_ENDPOINT` | LangChain endpoint | `https://api.smith.langchain.com` |
| `GITHUB_TOKEN` | GitHub personal access token | `ghp_...` |

### Example .env file:
```env
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
LANGCHAIN_API_KEY=lsv2_pt_your-langchain-api-key-here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
GITHUB_TOKEN=ghp_your-github-token-here
```

## 🚀 Usage

**Start the application:**
```bash
python main_app.py
```

**Available commands:**
- `help` - Show available commands
- `chat "your question"` - Ask questions about documents or code
- `add-doc path/to/file` - Add documents to knowledge base
- `search "query"` - Search documents
- `clear` - Clear conversation history
- `exit` - Exit the application

**Example interactions:**
```bash
🤖 RAG Agent > chat "What is Python sorting?"
🤖 RAG Agent > chat "can you looking for the github about python sort"
🤖 RAG Agent > add-doc ./documents/my_document.pdf
```

## 📁 Project Structure

```
ChatBot/
├── main_app.py            # Main application and CLI interface
├── agent_core.py          # Core agent logic and tool management
├── config.py              # Configuration management
├── document_processor.py  # Document loading and processing
├── vector_store.py        # Vector database implementation
├── llm_integration.py     # LLM and RAG chain management
├── github_search_tool.py  # GitHub API integration
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
└── README.md             # This file
```

## 🔧 How It Works

1. **Document Processing**: Upload documents (PDF, DOCX, TXT, MD) to build a knowledge base
2. **Vector Storage**: Documents are chunked and stored as embeddings in ChromaDB
3. **RAG Pipeline**: User queries trigger document retrieval + LLM generation
4. **GitHub Integration**: Code-related queries search GitHub repositories in real-time
5. **Conversation**: Multi-turn conversations with context memory

## 🧪 Testing

The system includes GitHub search functionality that can find code examples:

```bash
# Test GitHub search
python main_app.py
🤖 RAG Agent > chat "find python sorting algorithms on github"
```

## 📞 Support

If you encounter any issues:
1. Check your API keys are correctly set in `.env`
2. Ensure all dependencies are installed
3. Create an issue on GitHub with error details

---

**Note**: Keep your `.env` file secure and never commit it to version control. 