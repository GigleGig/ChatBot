"""
Agent Core Module for RAG System

This module provides the core agent functionality including:
- Tool management and execution
- Agent orchestration and decision making
- Memory systems for agent state
- Integration with RAG system
- Agent workflow management

Key Components:
- Tool: Abstract base class for agent tools
- ToolManager: Manages available tools and execution
- AgentMemory: Manages agent state and memory
- Agent: Main agent class with decision making
- AgentWorkflow: Orchestrates agent operations
"""

import os
import json
import uuid
import asyncio
import tempfile
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Callable
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from config import get_config
from llm_integration import RAGChain, MessageRole
from vector_store import DocumentRetriever
from document_processor import DocumentProcessor


class ToolType(str, Enum):
    """Types of tools available to the agent."""
    SEARCH = "search"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    UTILITY = "utility"
    EXTERNAL = "external"
    KNOWLEDGE = "knowledge"


class ToolResult(BaseModel):
    """Result from tool execution."""
    tool_name: str = Field(..., description="Name of the executed tool")
    success: bool = Field(..., description="Whether tool execution was successful")
    result: Any = Field(default=None, description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time: float = Field(..., description="Execution time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Tool(ABC):
    """Abstract base class for agent tools."""
    
    def __init__(self, name: str, description: str, tool_type: ToolType):
        """Initialize the tool."""
        self.name = name
        self.description = description
        self.tool_type = tool_type
        self.enabled = True
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's parameter schema."""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": self._get_parameters_schema()
        }
    
    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema for this tool."""
        pass


class DocumentSearchTool(Tool):
    """Tool for searching documents using the RAG system."""
    
    def __init__(self, retriever: DocumentRetriever):
        super().__init__(
            name="document_search",
            description="Search through stored documents to find relevant information",
            tool_type=ToolType.SEARCH
        )
        self.retriever = retriever
    
    async def execute(self, query: str, k: int = 5, min_score: float = 0.0) -> ToolResult:
        """Execute document search."""
        start_time = datetime.now()
        
        try:
            results = self.retriever.retrieve_documents(query, k=k, min_score=min_score)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                result={
                    "query": query,
                    "results": [
                        {
                            "content": result.chunk.content,
                            "score": result.score,
                            "source": result.chunk.source_document,
                            "chunk_index": result.chunk.chunk_index
                        }
                        for result in results
                    ],
                    "total_results": len(results)
                },
                execution_time=execution_time,
                metadata={"retrieval_k": k, "min_score": min_score}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for document search."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for finding relevant documents"
                },
                "k": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                },
                "min_score": {
                    "type": "number",
                    "description": "Minimum similarity score threshold",
                    "default": 0.0
                }
            },
            "required": ["query"]
        }


class AddToKnowledgeBaseTool(Tool):
    """Tool for adding content to the RAG knowledge base."""
    
    def __init__(self, vector_store, config=None, document_manager=None):
        super().__init__(
            name="add_to_knowledge_base",
            description="Add content to the RAG knowledge base for future reference",
            tool_type=ToolType.KNOWLEDGE
        )
        self.vector_store = vector_store
        self.config = config or get_config()
        self.processor = DocumentProcessor(self.config)
        self.document_manager = document_manager
    
    async def execute(self, content: str, title: str, source: str = "user_input", 
                     metadata: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Add content to the knowledge base."""
        start_time = datetime.now()
        
        print(f"🔧 AddToKnowledgeBaseTool: Processing '{title}' ({len(content)} chars)")
        
        try:
            # Create a temporary file with the content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            print(f"🔧 Created temp file: {temp_path}")
            
            try:
                # Process the content into chunks
                print(f"🔧 Processing temp file: {temp_path}")
                
                try:
                    result = self.processor.process_document(temp_path)
                    chunks = result.get('chunks', [])
                    print(f"🔧 DocumentProcessor result: success={result is not None}")
                    print(f"🔧 Chunks found: {len(chunks)}")
                    
                    if chunks:
                        print(f"🔧 First chunk preview: {chunks[0].content[:100]}...")
                    else:
                        print(f"🔧 No chunks - checking original content...")
                        original_content = result.get('original_content', '')
                        print(f"🔧 Original content length: {len(original_content)}")
                        if original_content:
                            print(f"🔧 Original content preview: {original_content[:200]}...")
                        
                        # Check if file exists and has content
                        if os.path.exists(temp_path):
                            with open(temp_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            print(f"🔧 File content length: {len(file_content)}")
                            print(f"🔧 File content preview: {file_content[:200]}...")
                            
                except Exception as process_error:
                    print(f"🔧 DocumentProcessor error: {str(process_error)}")
                    print(f"🔧 Checking if temp file exists: {os.path.exists(temp_path)}")
                    if os.path.exists(temp_path):
                        print(f"🔧 File size: {os.path.getsize(temp_path)} bytes")
                        try:
                            with open(temp_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            print(f"🔧 File content: {file_content[:500]}...")
                        except Exception as read_error:
                            print(f"🔧 Could not read file: {read_error}")
                    
                    # Return error result
                    return ToolResult(
                        tool_name=self.name,
                        success=False,
                        error=f"DocumentProcessor failed: {str(process_error)}",
                        execution_time=(datetime.now() - start_time).total_seconds()
                    )
                
                if chunks:
                    # Update chunk metadata
                    for chunk in chunks:
                        chunk.source_document = title
                        chunk.metadata.update({
                            "source_type": source,
                            "added_at": datetime.now().isoformat(),
                            **(metadata or {})
                        })
                    
                    # Add chunks to vector store
                    success = self.vector_store.add_documents(chunks)
                    
                    if success and self.document_manager:
                        # Update document manager statistics
                        self.document_manager.processed_documents.append({
                            "filename": title,
                            "path": f"tool:{source}",
                            "chunks": len(chunks),
                            "processed_at": datetime.now().isoformat()
                        })
                        
                        self.document_manager.document_stats["total_documents"] += 1
                        self.document_manager.document_stats["total_chunks"] += len(chunks)
                        self.document_manager.document_stats["last_updated"] = datetime.now().isoformat()
                        
                        print(f"✅ Updated DocumentManager stats: {len(chunks)} chunks added")
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    return ToolResult(
                        tool_name=self.name,
                        success=success,
                        result={
                            "title": title,
                            "chunks_added": len(chunks),
                            "total_characters": len(content),
                            "source": source,
                            "stats_updated": self.document_manager is not None
                        },
                        execution_time=execution_time,
                        metadata={"source_type": source}
                    )
                else:
                    return ToolResult(
                        tool_name=self.name,
                        success=False,
                        error="No content could be extracted",
                        execution_time=0.0
                    )
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for adding to knowledge base."""
        return {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content to add to the knowledge base"
                },
                "title": {
                    "type": "string",
                    "description": "Title or identifier for the content"
                },
                "source": {
                    "type": "string",
                    "description": "Source of the content (e.g., 'github', 'user_input')",
                    "default": "user_input"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata to store with the content"
                }
            },
            "required": ["content", "title"]
        }


class TextAnalysisTool(Tool):
    """Tool for analyzing text content."""
    
    def __init__(self):
        super().__init__(
            name="text_analysis",
            description="Analyze text content for length, structure, and basic statistics",
            tool_type=ToolType.ANALYSIS
        )
    
    async def execute(self, text: str, analysis_type: str = "basic") -> ToolResult:
        """Execute text analysis."""
        start_time = datetime.now()
        
        try:
            if analysis_type == "basic":
                result = self._basic_analysis(text)
            elif analysis_type == "detailed":
                result = self._detailed_analysis(text)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"analysis_type": analysis_type}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _basic_analysis(self, text: str) -> Dict[str, Any]:
        """Perform basic text analysis."""
        lines = text.split('\n')
        words = text.split()
        
        return {
            "character_count": len(text),
            "word_count": len(words),
            "line_count": len(lines),
            "paragraph_count": len([line for line in lines if line.strip()]),
            "average_word_length": sum(len(word) for word in words) / len(words) if words else 0
        }
    
    def _detailed_analysis(self, text: str) -> Dict[str, Any]:
        """Perform detailed text analysis."""
        basic = self._basic_analysis(text)
        
        # Additional analysis
        sentences = text.split('.')
        unique_words = set(word.lower().strip('.,!?;:"()[]{}') for word in text.split())
        
        basic.update({
            "sentence_count": len([s for s in sentences if s.strip()]),
            "unique_words": len(unique_words),
            "vocabulary_richness": len(unique_words) / len(text.split()) if text.split() else 0,
            "average_sentence_length": len(text.split()) / len(sentences) if sentences else 0
        })
        
        return basic
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for text analysis."""
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text content to analyze"
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["basic", "detailed"],
                    "description": "Type of analysis to perform",
                    "default": "basic"
                }
            },
            "required": ["text"]
        }


class AgentMemory(BaseModel):
    """Memory system for the agent."""
    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    short_term_memory: List[Dict[str, Any]] = Field(default_factory=list)
    long_term_memory: Dict[str, Any] = Field(default_factory=dict)
    working_memory: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_to_short_term(self, memory_item: Dict[str, Any]) -> None:
        """Add item to short-term memory."""
        memory_item["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.short_term_memory.append(memory_item)
        self.updated_at = datetime.now(timezone.utc)
        
        # Keep short-term memory limited
        if len(self.short_term_memory) > 50:
            self.short_term_memory = self.short_term_memory[-50:]
    
    def store_in_long_term(self, key: str, value: Any) -> None:
        """Store information in long-term memory."""
        self.long_term_memory[key] = {
            "value": value,
            "stored_at": datetime.now(timezone.utc).isoformat()
        }
        self.updated_at = datetime.now(timezone.utc)
    
    def get_from_long_term(self, key: str) -> Optional[Any]:
        """Retrieve information from long-term memory."""
        memory_item = self.long_term_memory.get(key)
        return memory_item["value"] if memory_item else None
    
    def update_working_memory(self, key: str, value: Any) -> None:
        """Update working memory."""
        self.working_memory[key] = value
        self.updated_at = datetime.now(timezone.utc)
    
    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activities from short-term memory."""
        return self.short_term_memory[-limit:] if self.short_term_memory else []


class ToolManager:
    """Manages available tools and their execution."""
    
    def __init__(self):
        """Initialize the tool manager."""
        self.tools: Dict[str, Tool] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool with the manager."""
        self.tools[tool.name] = tool
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        if tool_name in self.tools:
            del self.tools[tool_name]
            return True
        return False
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        return [tool.get_schema() for tool in self.tools.values() if tool.enabled]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool with given parameters."""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' not found",
                execution_time=0.0
            )
        
        if not tool.enabled:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' is disabled",
                execution_time=0.0
            )
        
        try:
            result = await tool.execute(**kwargs)
            
            # Record execution
            self.execution_history.append({
                "tool_name": tool_name,
                "parameters": kwargs,
                "result": result.model_dump(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return result
            
        except Exception as e:
            error_result = ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool execution failed: {str(e)}",
                execution_time=0.0
            )
            
            self.execution_history.append({
                "tool_name": tool_name,
                "parameters": kwargs,
                "result": error_result.model_dump(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return error_result
    
    def get_execution_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent tool execution history."""
        return self.execution_history[-limit:] if self.execution_history else []


class Agent:
    """Main agent class that orchestrates all components."""
    
    def __init__(self, rag_chain: RAGChain, config=None):
        """Initialize the agent."""
        self.config = config or get_config()
        self.rag_chain = rag_chain
        self.memory = AgentMemory()
        self.tool_manager = ToolManager()
        self.conversation_id = str(uuid.uuid4())
        
        # Register default tools
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools."""
        # Document search tool
        document_search = DocumentSearchTool(self.rag_chain.retriever)
        self.tool_manager.register_tool(document_search)
        
        # Knowledge base tool (for adding content to RAG)
        # We need to pass the document manager to properly update statistics
        if hasattr(self.rag_chain.retriever, 'vector_store'):
            knowledge_tool = AddToKnowledgeBaseTool(
                self.rag_chain.retriever.vector_store, 
                self.config,
                document_manager=getattr(self, 'document_manager', None)
            )
            self.tool_manager.register_tool(knowledge_tool)
        
        # Text analysis tool
        text_analysis = TextAnalysisTool()
        self.tool_manager.register_tool(text_analysis)
        
        # GitHub search tools
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            try:
                # Dynamic import to avoid circular imports
                from github_search_tool import create_github_search_tool, create_github_code_search_tool, GitHubSearchWithContentTool
                
                # General GitHub search tool
                github_search_tool = create_github_search_tool(github_token)
                self.tool_manager.register_tool(github_search_tool)
                
                # Specialized code search tool
                github_code_search_tool = create_github_code_search_tool(github_token)
                self.tool_manager.register_tool(github_code_search_tool)
                
                # New GitHub search with content tool
                github_content_tool = GitHubSearchWithContentTool(github_token)
                self.tool_manager.register_tool(github_content_tool)
                
            except ImportError as e:
                print(f"Warning: Could not import GitHub search tools: {e}")
        else:
            print("Warning: No GITHUB_TOKEN found. GitHub search functionality will be disabled.")
    
    async def process_request(self, user_input: str, use_tools: bool = True) -> Dict[str, Any]:
        """Process a user request and generate a response."""
        start_time = datetime.now()
        
        # Add to memory
        self.memory.add_to_short_term({
            "type": "user_input",
            "content": user_input,
            "conversation_id": self.conversation_id
        })
        
        try:
            # Decide if tools are needed
            if use_tools:
                tool_decision = await self._decide_tool_usage(user_input)
                
                if tool_decision.get("use_tools", False):
                    # Execute tools first
                    tool_results = await self._execute_recommended_tools(
                        user_input, 
                        tool_decision.get("recommended_tools", [])
                    )
                    
                    # Add tool results to working memory
                    self.memory.update_working_memory("recent_tool_results", tool_results)
                    
                    # Generate response with tool context
                    response_result = await self._generate_response_with_tools(
                        user_input, tool_results
                    )
                else:
                    # Generate response without tools
                    response_result = await self._generate_simple_response(user_input)
            else:
                # Generate response without tools
                response_result = await self._generate_simple_response(user_input)
            
            # Add response to memory
            self.memory.add_to_short_term({
                "type": "agent_response",
                "content": response_result.get("response", ""),
                "conversation_id": self.conversation_id,
                "tools_used": response_result.get("tools_used", [])
            })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "response": response_result.get("response", ""),
                "tools_used": response_result.get("tools_used", []),
                "conversation_id": self.conversation_id,
                "execution_time": execution_time,
                "memory_items": len(self.memory.short_term_memory)
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.memory.add_to_short_term({
                "type": "error",
                "content": str(e),
                "conversation_id": self.conversation_id
            })
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "conversation_id": self.conversation_id
            }
    
    async def _decide_tool_usage(self, user_input: str) -> Dict[str, Any]:
        """Decide whether to use tools and which ones."""
        # Simple heuristic-based decision making
        # In a more advanced system, this could use an LLM to decide
        
        keywords_for_search = ["search", "find", "lookup", "document", "information", "what", "who", "when", "where", "how"]
        keywords_for_analysis = ["analyze", "analysis", "statistics", "count", "length", "structure"]
        keywords_for_github = ["github", "code", "repository", "repo", "function", "class", "implementation", "example", "library", "package"]
        keywords_for_code_search = ["def", "function", "class", "import", "async", "await", "python", "javascript", "java", "c++"]
        
        user_lower = user_input.lower()
        
        recommended_tools = []
        
        # Check for GitHub/code search keywords
        if any(keyword in user_lower for keyword in keywords_for_github) or any(keyword in user_lower for keyword in keywords_for_code_search):
            # Use the new GitHub search with content tool for better results
            recommended_tools.append({
                "tool_name": "github_search_with_content",
                "parameters": {
                    "query": user_input,
                    "search_type": "code",
                    "language": self._detect_programming_language(user_input),
                    "fetch_content": True,
                    "max_content_files": 3
                }
            })
        
        # Check for document search keywords (but not if GitHub search is already selected)
        elif any(keyword in user_lower for keyword in keywords_for_search):
            recommended_tools.append({
                "tool_name": "document_search",
                "parameters": {"query": user_input, "k": 5}
            })
        
        # Check for analysis keywords
        if any(keyword in user_lower for keyword in keywords_for_analysis):
            recommended_tools.append({
                "tool_name": "text_analysis",
                "parameters": {"text": user_input, "analysis_type": "basic"}
            })
        
        return {
            "use_tools": len(recommended_tools) > 0,
            "recommended_tools": recommended_tools,
            "reasoning": f"Found {len(recommended_tools)} relevant tools for this request"
        }
    
    def _detect_programming_language(self, query: str) -> Optional[str]:
        """Detect programming language from query."""
        query_lower = query.lower()
        
        language_keywords = {
            "python": ["python", "def", "import", "class", "pip", "django", "flask", "pandas"],
            "javascript": ["javascript", "js", "function", "var", "let", "const", "node", "react", "vue"],
            "java": ["java", "public", "private", "class", "import", "spring", "maven"],
            "typescript": ["typescript", "ts", "interface", "type"],
            "c++": ["c++", "cpp", "include", "namespace", "std"],
            "go": ["golang", "go", "func", "package"],
            "rust": ["rust", "fn", "cargo", "crate"],
            "php": ["php", "function", "class", "composer"],
            "ruby": ["ruby", "def", "class", "gem"],
            "swift": ["swift", "func", "class", "var", "let"]
        }
        
        for language, keywords in language_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return language
        
        return None
    
    async def _execute_recommended_tools(self, user_input: str, recommended_tools: List[Dict[str, Any]]) -> List[ToolResult]:
        """Execute recommended tools."""
        results = []
        
        for tool_config in recommended_tools:
            tool_name = tool_config["tool_name"]
            parameters = tool_config["parameters"]
            
            result = await self.tool_manager.execute_tool(tool_name, **parameters)
            results.append(result)
        
        return results
    
    async def _generate_response_with_tools(self, user_input: str, tool_results: List[ToolResult]) -> Dict[str, Any]:
        """Generate response using tool results."""
        # Prepare context from tool results
        tool_context_parts = []
        tools_used = []
        
        for result in tool_results:
            if result.success:
                tools_used.append(result.tool_name)
                if result.tool_name == "document_search" and result.result:
                    search_results = result.result.get("results", [])
                    for i, search_result in enumerate(search_results[:3], 1):  # Top 3 results
                        tool_context_parts.append(
                            f"Search Result {i}: {search_result['content'][:200]}..."
                        )
                elif result.tool_name == "text_analysis" and result.result:
                    analysis = result.result
                    tool_context_parts.append(
                        f"Text Analysis: {analysis.get('word_count', 0)} words, "
                        f"{analysis.get('character_count', 0)} characters"
                    )
                elif result.tool_name in ["github_search", "github_code_search"] and result.result:
                    github_results = result.result.get("results", [])
                    total_count = result.result.get("total_count", 0)
                    search_type = result.result.get("search_type", "code")
                    
                    tool_context_parts.append(f"GitHub Search Results ({search_type}): Found {total_count} total results")
                    
                    for i, github_result in enumerate(github_results[:3], 1):  # Top 3 results
                        title = github_result.title
                        url = github_result.url
                        description = github_result.description or "No description"
                        repository = github_result.repository or "Unknown repo"
                        language = github_result.language or "Unknown language"
                        
                        tool_context_parts.append(
                            f"GitHub Result {i}: {title}\n"
                            f"Repository: {repository} ({language})\n"
                            f"Description: {description[:150]}...\n"
                            f"URL: {url}"
                        )
                
                elif result.tool_name == "github_search_with_content" and result.result:
                    github_results = result.result.get("results", [])
                    total_count = result.result.get("total_count", 0)
                    files_with_content = result.result.get("files_with_content", 0)
                    
                    tool_context_parts.append(f"GitHub Search with Content: Found {total_count} total results, fetched content from {files_with_content} files")
                    
                    # Process results and add content to knowledge base
                    for i, github_result in enumerate(github_results[:3], 1):
                        title = github_result.get("title", "Unknown")
                        repository = github_result.get("repository", "Unknown repo")
                        url = github_result.get("url", "")
                        content = github_result.get("content")
                        
                        if content:
                            # Add content to knowledge base
                            print(f"📝 Found content ({len(content)} chars) from {repository}/{title}, adding to knowledge base...")
                            try:
                                add_result = await self.tool_manager.execute_tool(
                                    "add_to_knowledge_base",
                                    content=content,
                                    title=f"GitHub: {repository}/{title}",
                                    source="github",
                                    metadata={
                                        "repository": repository,
                                        "url": url,
                                        "language": self._detect_programming_language(content),
                                        "search_query": user_input
                                    }
                                )
                                
                                if add_result.success:
                                    chunks_added = add_result.result.get('chunks_added', 0)
                                    print(f"✅ Added GitHub content to knowledge base: {repository}/{title} ({chunks_added} chunks)")
                                else:
                                    print(f"❌ Failed to add to knowledge base: {add_result.error}")
                                    
                            except Exception as e:
                                print(f"❌ Error adding to knowledge base: {str(e)}")
                        else:
                            print(f"⚠️  No content found for {repository}/{title}")
                        
                        # Add to tool context for immediate use
                        content_preview = content[:500] + "..." if content and len(content) > 500 else content or "No content available"
                        tool_context_parts.append(
                            f"GitHub Result {i}: {title}\n"
                            f"Repository: {repository}\n"
                            f"URL: {url}\n"
                            f"Content: {content_preview}"
                        )
        
        tool_context = "\n\n".join(tool_context_parts) if tool_context_parts else "No tool results available."
        
        # Always try RAG retrieval first to get relevant documents from knowledge base
        rag_result = self.rag_chain.process_query(
            user_input,
            conversation_id=self.conversation_id,
            template_name="rag_qa",
            retrieval_k=5
        )
        
        # Combine RAG context with tool results for comprehensive response
        rag_context = ""
        if rag_result["success"] and rag_result.get("retrieval_results"):
            rag_context_parts = []
            for i, result in enumerate(rag_result["retrieval_results"][:3], 1):
                rag_context_parts.append(f"Knowledge Base Document {i}: {result.chunk.content[:300]}...")
            rag_context = "\n\n".join(rag_context_parts)
        
        # Create enhanced prompt with both RAG context and tool results
        if tool_context_parts or rag_context:
            messages = [
                {
                    "role": "system", 
                    "content": "You are a helpful AI assistant. Use both the knowledge base documents and tool results to provide comprehensive and accurate responses. Prioritize recent information from tools while leveraging foundational knowledge from documents."
                },
                {
                    "role": "user",
                    "content": f"""User Request: {user_input}

Knowledge Base Context:
{rag_context if rag_context else "No relevant documents found in knowledge base."}

Tool Results:
{tool_context}

Please provide a comprehensive response that combines insights from both the knowledge base and tool results."""
                }
            ]
            
            try:
                llm_response = self.rag_chain.llm_manager.generate_response(messages)
                return {
                    "response": llm_response.content,
                    "tools_used": tools_used,
                    "rag_results": rag_result.get("retrieval_results", []),
                    "combined_context": True
                }
            except Exception as e:
                return {
                    "response": f"I encountered an issue generating a response: {str(e)}",
                    "tools_used": tools_used,
                    "error": str(e)
                }
        else:
            # No tool results and no RAG context, use simple RAG response
            if rag_result["success"]:
                return {
                    "response": rag_result["response"],
                    "tools_used": tools_used,
                    "rag_results": rag_result.get("retrieval_results", [])
                }
            else:
                return {
                    "response": f"I encountered an issue generating a response: {rag_result.get('error', 'Unknown error')}",
                    "tools_used": tools_used,
                    "error": rag_result.get("error")
                }
    
    async def _generate_simple_response(self, user_input: str) -> Dict[str, Any]:
        """Generate simple response without tools but still use RAG."""
        # Always try RAG first to get relevant documents from knowledge base
        rag_result = self.rag_chain.process_query(
            user_input,
            conversation_id=self.conversation_id,
            template_name="rag_qa",
            retrieval_k=5
        )
        
        if rag_result["success"]:
            return {
                "response": rag_result["response"],
                "tools_used": [],
                "rag_results": rag_result.get("retrieval_results", [])
            }
        else:
            # If RAG fails, generate a response using LLM without context
            # This ensures we always provide a helpful response
            try:
                messages = [
                    {
                        "role": "system",
                        "content": """You are a helpful AI assistant. The user has asked a question but no relevant documents were found in the knowledge base. Please provide a helpful response based on your general knowledge. If the question is about programming, provide code examples. If you don't know something specific, be honest about limitations but still try to be helpful with general guidance."""
                    },
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
                
                llm_response = self.rag_chain.llm_manager.generate_response(messages)
                
                return {
                    "response": llm_response.content,
                    "tools_used": [],
                    "rag_results": [],
                    "fallback_response": True
                }
                
            except Exception as e:
                return {
                    "response": f"I apologize, but I encountered an issue generating a response. Please try rephrasing your question or adding more context. Error: {str(e)}",
                    "tools_used": [],
                    "error": str(e),
                    "fallback_response": True
                }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and statistics."""
        return {
            "conversation_id": self.conversation_id,
            "memory_items": len(self.memory.short_term_memory),
            "available_tools": len(self.tool_manager.tools),
            "tool_executions": len(self.tool_manager.execution_history),
            "uptime": (datetime.now(timezone.utc) - self.memory.created_at).total_seconds(),
            "tools": [tool.name for tool in self.tool_manager.tools.values() if tool.enabled]
        }
    
    def clear_memory(self) -> None:
        """Clear agent memory."""
        self.memory = AgentMemory()
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of agent memory."""
        return {
            "short_term_items": len(self.memory.short_term_memory),
            "long_term_items": len(self.memory.long_term_memory),
            "working_memory_items": len(self.memory.working_memory),
            "recent_activities": self.memory.get_recent_activities(5)
        }


# Factory functions
def create_agent(rag_chain: RAGChain, config=None) -> Agent:
    """Factory function to create an agent."""
    return Agent(rag_chain, config)


class AgentWorkflow:
    """Orchestrates agent workflows and operations."""
    
    def __init__(self, agent: Agent):
        """Initialize workflow manager."""
        self.agent = agent
        self.workflows: Dict[str, Callable] = {}
        self._register_default_workflows()
    
    def _register_default_workflows(self):
        """Register default workflows."""
        self.workflows["question_answering"] = self._qa_workflow
        self.workflows["document_analysis"] = self._document_analysis_workflow
        self.workflows["research"] = self._research_workflow
    
    async def _qa_workflow(self, query: str) -> Dict[str, Any]:
        """Question answering workflow."""
        return await self.agent.process_request(query, use_tools=True)
    
    async def _document_analysis_workflow(self, query: str) -> Dict[str, Any]:
        """Document analysis workflow."""
        # First search for relevant documents
        search_result = await self.agent.tool_manager.execute_tool(
            "document_search", 
            query=query, 
            k=5
        )
        
        if search_result.success:
            # Then analyze the found content
            combined_text = ""
            for result in search_result.result.get("results", []):
                combined_text += result["content"] + "\n"
            
            if combined_text:
                analysis_result = await self.agent.tool_manager.execute_tool(
                    "text_analysis",
                    text=combined_text,
                    analysis_type="detailed"
                )
                
                # Generate comprehensive response
                response_result = await self.agent._generate_response_with_tools(
                    f"Analyze these documents: {query}",
                    [search_result, analysis_result]
                )
                
                return {
                    "success": True,
                    "workflow": "document_analysis",
                    "response": response_result.get("response"),
                    "tools_used": ["document_search", "text_analysis"],
                    "search_results": search_result.result,
                    "analysis_results": analysis_result.result if analysis_result.success else None
                }
        
        # Fallback to regular processing
        return await self.agent.process_request(query)
    
    async def _research_workflow(self, query: str) -> Dict[str, Any]:
        """Research workflow with multiple search strategies."""
        # Multiple search approaches
        search_queries = [
            query,
            f"background information on {query}",
            f"details about {query}",
            f"examples of {query}"
        ]
        
        all_results = []
        for search_query in search_queries:
            result = await self.agent.tool_manager.execute_tool(
                "document_search",
                query=search_query,
                k=3
            )
            if result.success:
                all_results.extend(result.result.get("results", []))
        
        # Remove duplicates and combine
        unique_results = []
        seen_content = set()
        for result in all_results:
            content_hash = hash(result["content"][:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        # Generate research summary
        if unique_results:
            combined_context = "\n".join([r["content"] for r in unique_results[:10]])
            
            research_query = f"""Based on the following research materials, provide a comprehensive answer to: {query}

Research Materials:
{combined_context}

Please synthesize the information and provide a well-structured response."""
            
            rag_result = self.agent.rag_chain.process_query(
                research_query,
                conversation_id=self.agent.conversation_id,
                template_name="rag_qa",
                retrieval_k=2
            )
            
            return {
                "success": True,
                "workflow": "research",
                "response": rag_result.get("response", ""),
                "research_sources": len(unique_results),
                "tools_used": ["document_search"],
                "sources": unique_results[:5]  # Top 5 sources
            }
        
        # Fallback
        return await self.agent.process_request(query)
    
    async def execute_workflow(self, workflow_name: str, query: str) -> Dict[str, Any]:
        """Execute a specific workflow."""
        if workflow_name not in self.workflows:
            return {
                "success": False,
                "error": f"Unknown workflow: {workflow_name}",
                "available_workflows": list(self.workflows.keys())
            }
        
        try:
            return await self.workflows[workflow_name](query)
        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}",
                "workflow": workflow_name
            }
    
    def list_workflows(self) -> List[str]:
        """List available workflows."""
        return list(self.workflows.keys()) 