# 🤖 Intelligent RAG Agent System

A **next-generation chatbot** built with **Retrieval-Augmented Generation (RAG)** capabilities, featuring advanced GitHub integration, intelligent document processing, and automated knowledge base building.

## ✨ Key Highlights

- **🧠 Intelligent Response Generation**: Never gives empty responses - always provides valuable information
- **📥 Automatic Knowledge Building**: GitHub search results automatically added to RAG knowledge base
- **🔍 Smart Code Discovery**: Fetches actual code content, not just links
- **🎯 Context-Aware Conversations**: Combines retrieved knowledge with real-time search

## 🚀 Features

### Core RAG Capabilities
- **🤖 Advanced RAG Architecture**: Combines document retrieval with LLM generation
- **📚 Multi-Format Document Support**: PDF, DOCX, TXT, MD file processing
- **💾 Persistent Vector Storage**: ChromaDB for document embeddings
- **🗣️ Conversation Management**: Interactive chat interface with memory

### GitHub Integration
- **🔍 Intelligent GitHub Search**: Real-time code search and repository analysis
- **📥 Content Fetching**: Automatically retrieves actual code content from GitHub
- **🎯 Smart Knowledge Building**: Found code automatically added to RAG knowledge base
- **🔄 Enhanced Search**: Multiple search strategies (general, code-specific, content-rich)

### Agent & Tools
- **🛠️ Multi-Tool Architecture**: GitHub search, document search, text analysis
- **🎯 Smart Tool Selection**: Automatically chooses the best tools for each query
- **📊 Knowledge Base Management**: Add content directly to RAG system
- **🔗 LangChain Integration**: Standardized LLM and document processing

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
- `qa "question"` - Question answering workflow
- `add <file_path>` - Add documents to knowledge base
- `search "query"` - Search documents
- `docs-stats` - Show document statistics
- `clear` - Clear conversation history
- `exit` - Exit the application

**Example interactions:**
```bash
🤖 RAG Agent > chat "What is Python sorting?"
🤖 RAG Agent > chat "can you show me a python quicksort algorithm"
🤖 RAG Agent > qa "How does bubble sort work?"
🤖 RAG Agent > add ./documents/my_document.pdf
🤖 RAG Agent > docs-stats
```

### 🎯 What Makes This Special

**Before (Traditional Chatbot):**
- Empty responses when no documents found
- Only returns links to GitHub repositories
- No learning from searches
- Limited to pre-uploaded documents

**After (Intelligent RAG Agent):**
- Always provides valuable responses
- Fetches and analyzes actual code content
- Automatically builds knowledge base from searches
- Continuously learns and improves responses

**Example conversation flow:**
```bash
🤖 RAG Agent > chat "show me a fast sorting algorithm in python"

# System automatically:
# 1. Searches GitHub for relevant code
# 2. Fetches actual algorithm implementations
# 3. Adds found code to knowledge base
# 4. Provides detailed explanation with real examples
# 5. Future queries can reference this newly acquired knowledge
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

### Traditional RAG Flow
1. **Document Processing**: Upload documents (PDF, DOCX, TXT, MD) to build a knowledge base
2. **Vector Storage**: Documents are chunked and stored as embeddings in ChromaDB
3. **RAG Pipeline**: User queries trigger document retrieval + LLM generation

### Enhanced Intelligent Flow
4. **Smart Tool Selection**: Agent automatically selects appropriate tools based on query intent
5. **GitHub Content Fetching**: For code queries, fetches actual implementations from GitHub
6. **Automatic Knowledge Expansion**: Found content automatically added to RAG knowledge base
7. **Context-Rich Responses**: Combines retrieved knowledge with real-time search results
8. **Continuous Learning**: Every search improves the system's knowledge base

### Key Improvements
- **No Empty Responses**: System always provides valuable information, even without existing documents
- **Real Content**: Actual code implementations instead of just repository links
- **Self-Improving**: Knowledge base grows automatically through intelligent searches
- **Context Awareness**: Remembers and builds upon previous interactions

## 🧪 Testing

### Test the Enhanced GitHub Integration

The system now includes advanced GitHub search with automatic content fetching:

```bash
# Start the application
python main_app.py

# Test intelligent code search (automatically fetches and stores content)
🤖 RAG Agent > chat "show me a python quicksort implementation"
🤖 RAG Agent > chat "find bubble sort algorithms"
🤖 RAG Agent > qa "how does merge sort work in python?"

# Check that content was automatically added to knowledge base
🤖 RAG Agent > docs-stats
# Should show documents and chunks have been added

# Test that the system now knows about the fetched code
🤖 RAG Agent > chat "what sorting algorithms do you know about?"
# Should reference the previously fetched GitHub content
```

### Verify Automatic Knowledge Building

1. Start with empty knowledge base
2. Ask code-related questions
3. System automatically searches GitHub and fetches content
4. Check `docs-stats` to see knowledge base growth
5. Ask follow-up questions that reference the newly acquired knowledge

## 🔄 Recent Updates

### Version 2.0 - Intelligent GitHub Integration
- ✅ **Automatic Content Fetching**: GitHub search now fetches actual code content
- ✅ **Smart Knowledge Building**: Found content automatically added to RAG knowledge base
- ✅ **Enhanced Response Generation**: No more empty responses - always provides valuable information
- ✅ **Multiple Search Strategies**: General search, code-specific search, and content-rich search
- ✅ **Improved Error Handling**: Better debugging and error recovery
- ✅ **Statistics Tracking**: Real-time knowledge base growth monitoring

### Key Files Modified
- `agent_core.py` - Enhanced agent logic with auto-knowledge building
- `github_search_tool.py` - Added content fetching capabilities
- `main_app.py` - Improved integration and statistics tracking

## 📞 Support

If you encounter any issues:
1. Check your API keys are correctly set in `.env`
2. Ensure all dependencies are installed
3. Try the test commands in the Testing section
4. Check `docs-stats` to verify knowledge base is growing
5. Create an issue on GitHub with error details

### Common Solutions
- **Empty responses**: Check GitHub token and OpenAI API key
- **No content fetched**: Verify internet connection and GitHub rate limits
- **Processing errors**: Check file permissions and temp directory access

---

**Note**: Keep your `.env` file secure and never commit it to version control. 