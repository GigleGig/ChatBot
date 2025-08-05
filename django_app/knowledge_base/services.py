"""
Knowledge Base Services - Django integration for RAG functionality.
"""
import os
import sys
import tempfile
from typing import Dict, List, Any, Optional
from django.conf import settings

# Add the parent directory to sys.path to import the original modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from config import get_config
    from llm_integration import create_llm_manager, create_rag_chain
    from vector_store import create_vector_store, create_retriever
    from agent_core import create_agent, AgentWorkflow
    LLM_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"LLM Integration not available: {e}")
    LLM_INTEGRATION_AVAILABLE = False

from .models import Document, DocumentChunk, VectorStoreIndex


class KnowledgeBaseService:
    """Service to manage knowledge base operations."""
    
    def __init__(self):
        # Temporarily simplified until dependencies are resolved
        pass
        # self.config = get_config()
        # self.document_processor = DocumentProcessor(self.config)
        # self.vector_store = create_vector_store(self.config)
        # self.retriever = create_retriever(self.vector_store, self.config)
        # self.llm_manager = create_llm_manager(self.config)
        # self.rag_chain = create_rag_chain(self.retriever, self.config)
        
    def add_document(self, title: str, content: str, source_type: str = 'user_input', 
                    user=None, metadata: Dict = None) -> Dict[str, Any]:
        """Add a document to the knowledge base."""
        try:
            # Create Django Document record
            document = Document.objects.create(
                title=title,
                content=content,
                source_type=source_type,
                uploaded_by=user,
                source_metadata=metadata or {},
                language=self._detect_language(content)
            )
            
            # Process content into chunks
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                result = self.document_processor.process_document(temp_path)
                chunks = result.get('chunks', [])
                
                if chunks:
                    # Update chunk metadata and add to vector store
                    for i, chunk in enumerate(chunks):
                        chunk.source_document = title
                        chunk.metadata.update({
                            'document_id': str(document.id),
                            'source_type': source_type,
                            'chunk_index': i
                        })
                        
                        # Create Django DocumentChunk record
                        DocumentChunk.objects.create(
                            document=document,
                            content=chunk.content,
                            chunk_index=i,
                            metadata=chunk.metadata,
                            start_char=chunk.metadata.get('start_char'),
                            end_char=chunk.metadata.get('end_char')
                        )
                    
                    # Add to vector store
                    success = self.vector_store.add_documents(chunks)
                    
                    if success:
                        return {
                            'success': True,
                            'document_id': str(document.id),
                            'chunks_added': len(chunks),
                            'title': title
                        }
                    else:
                        document.delete()  # Clean up if vector store failed
                        return {
                            'success': False,
                            'error': 'Failed to add to vector store'
                        }
                else:
                    document.delete()
                    return {
                        'success': False,
                        'error': 'No content could be extracted'
                    }
                    
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_documents(self, query: str, k: int = 5, user=None) -> Dict[str, Any]:
        """Search documents in the knowledge base."""
        try:
            results = self.retriever.retrieve_documents(query, k=k)
            
            search_results = []
            for result in results:
                # Try to find the corresponding Django document
                document = None
                chunk_metadata = result.chunk.metadata
                if 'document_id' in chunk_metadata:
                    try:
                        document = Document.objects.get(id=chunk_metadata['document_id'])
                    except Document.DoesNotExist:
                        pass
                
                search_results.append({
                    'content': result.chunk.content,
                    'score': result.score,
                    'source': result.chunk.source_document,
                    'chunk_index': result.chunk.chunk_index,
                    'document_id': chunk_metadata.get('document_id'),
                    'document_title': document.title if document else None,
                    'source_type': document.source_type if document else None
                })
            
            return {
                'success': True,
                'results': search_results,
                'total_results': len(search_results),
                'query': query
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def get_rag_response(self, query: str, conversation_id: str = None) -> Dict[str, Any]:
        """Get a RAG-powered response to a query."""
        try:
            result = self.rag_chain.process_query(
                query,
                conversation_id=conversation_id,
                template_name="rag_qa",
                retrieval_k=5
            )
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': ''
            }
    
    def _detect_language(self, content: str) -> str:
        """Detect programming language from content."""
        content_lower = content.lower()
        
        language_keywords = {
            'python': ['def ', 'import ', 'class ', 'python', 'pip install'],
            'javascript': ['function ', 'var ', 'let ', 'const ', 'node'],
            'java': ['public class', 'import java', 'public static'],
            'cpp': ['#include', 'namespace std', 'int main'],
            'go': ['package main', 'func ', 'import "'],
            'rust': ['fn ', 'use std', 'cargo'],
            'php': ['<?php', 'function ', '$'],
            'ruby': ['def ', 'class ', 'require '],
            'swift': ['func ', 'import swift', 'var '],
        }
        
        for language, keywords in language_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return language
        
        return 'text'


class AgentService:
    """Service to manage AI agent operations."""
    
    def __init__(self, knowledge_service: KnowledgeBaseService = None):
        self.knowledge_service = knowledge_service or KnowledgeBaseService()
        
        if LLM_INTEGRATION_AVAILABLE:
            try:
                # Initialize with actual LLM integration
                self.config = get_config()
                self.llm_manager = create_llm_manager(self.config)
                
                # Initialize vector store and retriever
                self.vector_store = create_vector_store(self.config)
                self.retriever = create_retriever(self.vector_store, self.config)
                
                # Create RAG chain
                self.rag_chain = create_rag_chain(self.retriever, self.config)
                
                # Create agent with tools
                self.agent = create_agent(self.rag_chain, self.config)
                self.workflow_manager = AgentWorkflow(self.agent)
                
                self.llm_available = True
                print("LLM integration initialized successfully")
            except Exception as e:
                print(f"Failed to initialize LLM integration: {e}")
                self.llm_available = False
                self._setup_fallback()
        else:
            self.llm_available = False
            self._setup_fallback()
    
    def _setup_fallback(self):
        """Setup fallback mode without LLM integration."""
        self.available_tools = [
            {'name': 'code_execution', 'description': 'Execute code safely'},
            {'name': 'github_search', 'description': 'Search GitHub for code examples'},
            {'name': 'document_search', 'description': 'Search knowledge base documents'}
        ]
        self.workflows = ['code_assistant', 'debug_helper', 'github_explorer']
    
    async def process_message(self, message: str, conversation_id: str = None, 
                            use_tools: bool = True, workflow: str = None) -> Dict[str, Any]:
        """Process a user message with the agent."""
        if self.llm_available:
            return await self._process_with_llm(message, conversation_id, use_tools, workflow)
        else:
            return await self._process_fallback(message, conversation_id, use_tools, workflow)
    
    async def _process_with_llm(self, message: str, conversation_id: str = None, 
                               use_tools: bool = True, workflow: str = None) -> Dict[str, Any]:
        """Process message using actual LLM integration."""
        try:
            import time
            start_time = time.time()
            
            # Try the full RAG system first
            if hasattr(self, 'rag_chain'):
                try:
                    result = self.rag_chain.process_query(
                        message,
                        conversation_id=conversation_id,
                        template_name="chat",
                        retrieval_k=3
                    )
                    
                    # Check if the response is too generic/unhelpful
                    response_text = result.get('response', '').lower()
                    if any(phrase in response_text for phrase in [
                        'without any relevant documents',
                        'do not have enough information',
                        'no relevant documents found',
                        'i am unable to',
                        'cannot provide'
                    ]):
                        # Fall back to direct LLM for general programming help
                        result = await self._direct_llm_response(message, conversation_id)
                    
                except Exception:
                    # If RAG fails, use direct LLM
                    result = await self._direct_llm_response(message, conversation_id)
            
            elif workflow and hasattr(self, 'workflow_manager'):
                result = await self.workflow_manager.execute_workflow(workflow, message)
            else:
                result = await self._direct_llm_response(message, conversation_id)
            
            execution_time = time.time() - start_time
            
            return {
                'success': True,
                'response': result.get('response', 'No response generated'),
                'tools_used': result.get('tools_used', []),
                'execution_time': execution_time,
                'metadata': {
                    'conversation_id': conversation_id,
                    'workflow': workflow,
                    'use_tools': use_tools,
                    'llm_mode': True
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': f'Sorry, I encountered an error while processing your request: {str(e)}'
            }
    
    async def _direct_llm_response(self, message: str, conversation_id: str = None) -> Dict[str, Any]:
        """Get direct response from LLM for general programming assistance."""
        try:
            messages = [
                {
                    "role": "system", 
                    "content": """You are a helpful programming assistant specializing in code development, debugging, and programming concepts. 
                    
You can help with:
- Writing code examples and implementations
- Explaining programming concepts and algorithms
- Debugging code issues
- Best practices and optimization
- Data structures and algorithms
- Multiple programming languages (Python, JavaScript, Java, etc.)

Provide clear, practical, and helpful responses. Include code examples when relevant."""
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
            
            llm_response = self.llm_manager.generate_response(messages)
            
            return {
                'response': llm_response.content,
                'tools_used': ['direct_llm'],
                'success': True
            }
            
        except Exception as e:
            return {
                'response': f'I encountered an error: {str(e)}',
                'tools_used': [],
                'success': False
            }
    
    async def _process_fallback(self, message: str, conversation_id: str = None, 
                               use_tools: bool = True, workflow: str = None) -> Dict[str, Any]:
        """Fallback processing when LLM is not available."""
        try:
            response = f"I received your message: '{message}'. "
            
            if workflow:
                response += f"Using workflow: {workflow}. "
            
            if use_tools:
                response += "Tools are available for code execution and GitHub search. "
            
            response += "This is a placeholder response while the full LLM integration is being set up."
            
            return {
                'success': True,
                'response': response,
                'tools_used': [],
                'execution_time': 0.1,
                'metadata': {
                    'conversation_id': conversation_id,
                    'workflow': workflow,
                    'use_tools': use_tools,
                    'llm_mode': False
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': f'Sorry, I encountered an error: {str(e)}'
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available agent tools."""
        return self.available_tools
    
    def get_available_workflows(self) -> List[str]:
        """Get list of available workflows."""
        return self.workflows
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            'status': 'online',
            'tools_count': len(self.available_tools),
            'workflows_count': len(self.workflows),
            'message': 'Agent is ready (simplified mode)'
        }