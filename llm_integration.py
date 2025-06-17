"""
LLM Integration Module for RAG System

This module provides LLM integration including:
- OpenAI GPT model integration
- Conversation management
- RAG-enhanced response generation
- Prompt templates
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# Optional imports with graceful fallbacks
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, AIMessage, SystemMessage
    HAS_LANGCHAIN_OPENAI = True
except ImportError:
    HAS_LANGCHAIN_OPENAI = False

from config import get_config
from vector_store import DocumentRetriever


class MessageRole(str, Enum):
    """Enum for message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ConversationMessage(BaseModel):
    """Individual message in a conversation."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()


class Conversation(BaseModel):
    """Conversation containing multiple messages."""
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_message(self, role: MessageRole, content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """Add a message to the conversation."""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)
        return message
    
    def get_messages_for_llm(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """Get messages formatted for LLM API calls."""
        messages = self.messages
        if max_messages:
            messages = messages[-max_messages:]
        
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]


class LLMResponse(BaseModel):
    """Response from LLM with metadata."""
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(..., description="Response content")
    model: str = Field(..., description="Model used for generation")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    usage: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMManager:
    """Manages LLM interactions and API calls."""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.client = None
        self.langchain_llm = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: No OPENAI_API_KEY found. LLM functionality will be limited.")
            return
        
        if HAS_OPENAI:
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
        
        if HAS_LANGCHAIN_OPENAI:
            try:
                self.langchain_llm = ChatOpenAI(
                    model=self.config.llm.model_name,
                    temperature=self.config.llm.temperature,
                    max_tokens=self.config.llm.max_tokens,
                    openai_api_key=api_key
                )
            except Exception as e:
                print(f"Warning: Could not initialize LangChain LLM: {e}")
    
    def generate_response(self, messages: List[Dict[str, str]], 
                         temperature: Optional[float] = None,
                         max_tokens: Optional[int] = None) -> LLMResponse:
        """Generate a response using OpenAI API."""
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check API key and dependencies.")
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.llm.model_name,
                messages=messages,
                temperature=temperature or self.config.llm.temperature,
                max_tokens=max_tokens or self.config.llm.max_tokens
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "response_id": response.id
                }
            )
            
        except Exception as e:
            raise ValueError(f"Failed to generate response: {e}")


class ConversationManager:
    """Manages conversations and chat history."""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.conversations: Dict[str, Conversation] = {}
    
    def create_conversation(self, conversation_id: Optional[str] = None) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            conversation_id=conversation_id or str(uuid.uuid4())
        )
        self.conversations[conversation.conversation_id] = conversation
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get an existing conversation."""
        return self.conversations.get(conversation_id)
    
    def add_message_to_conversation(self, conversation_id: str, role: MessageRole, 
                                  content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """Add a message to an existing conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        return conversation.add_message(role, content, metadata)


class PromptTemplate(BaseModel):
    """Template for generating structured prompts."""
    name: str = Field(..., description="Template name")
    system_prompt: str = Field(..., description="System prompt template")
    user_prompt_template: str = Field(..., description="User prompt template")
    
    def format_system_prompt(self) -> str:
        """Get the formatted system prompt."""
        return self.system_prompt
    
    def format_user_prompt(self, **kwargs) -> str:
        """Format the user prompt with provided variables."""
        try:
            return self.user_prompt_template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(f"Missing required template variable: {missing_var}")


class RAGChain:
    """Retrieval-Augmented Generation chain."""
    
    def __init__(self, retriever: DocumentRetriever, llm_manager: LLMManager, 
                 conversation_manager: ConversationManager, config=None):
        self.retriever = retriever
        self.llm_manager = llm_manager
        self.conversation_manager = conversation_manager
        self.config = config or get_config()
        self._setup_default_templates()
    
    def _setup_default_templates(self):
        """Setup default prompt templates."""
        self.templates = {
            "rag_qa": PromptTemplate(
                name="rag_qa",
                system_prompt="""You are a helpful AI assistant that answers questions based on provided context. 
Use the retrieved documents to provide accurate responses. If the context doesn't contain enough information, say so clearly.""",
                user_prompt_template="""Context from retrieved documents:
{context}

Question: {question}

Please provide a helpful answer based on the context above."""
            ),
            
            "chat": PromptTemplate(
                name="chat", 
                system_prompt="""You are a helpful AI assistant engaging in conversation. 
Use retrieved context when relevant.""",
                user_prompt_template="""Retrieved Context:
{context}

User Message: {user_message}

Please respond naturally."""
            )
        }
    
    def process_query(self, query: str, conversation_id: Optional[str] = None,
                     template_name: str = "rag_qa", 
                     retrieval_k: int = 5, min_score: float = 0.0) -> Dict[str, Any]:
        """Process a query using RAG pipeline."""
        
        # Step 1: Retrieve relevant documents
        search_results = self.retriever.retrieve_documents(
            query, k=retrieval_k, min_score=min_score
        )
        
        # Step 2: Format context from retrieved documents
        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"Document {i}:\n{result.chunk.content}")
        
        context = "\n\n".join(context_parts) if context_parts else "No relevant documents found."
        
        # Step 3: Get template
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Step 4: Prepare messages for LLM
        messages = [
            {"role": "system", "content": template.format_system_prompt()}
        ]
        
        # Add conversation history if provided
        if conversation_id:
            conversation = self.conversation_manager.get_conversation(conversation_id)
            if conversation:
                messages.extend(conversation.get_messages_for_llm(max_messages=10))
        
        # Add current query with context
        user_prompt = template.format_user_prompt(
            context=context,
            question=query,
            user_message=query
        )
        messages.append({"role": "user", "content": user_prompt})
        
        # Step 5: Generate response
        try:
            llm_response = self.llm_manager.generate_response(messages)
            
            # Step 6: Update conversation if provided
            if conversation_id:
                conversation = self.conversation_manager.get_conversation(conversation_id)
                if not conversation:
                    conversation = self.conversation_manager.create_conversation(conversation_id)
                
                conversation.add_message(MessageRole.USER, query)
                conversation.add_message(MessageRole.ASSISTANT, llm_response.content)
            
            return {
                "success": True,
                "response": llm_response.content,
                "retrieval_results": search_results,
                "context_used": context,
                "llm_response": llm_response,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "retrieval_results": search_results,
                "context_used": context
            }


# Factory functions
def create_llm_manager(config=None) -> LLMManager:
    """Factory function to create LLM manager."""
    return LLMManager(config)


def create_conversation_manager(config=None) -> ConversationManager:
    """Factory function to create conversation manager."""
    return ConversationManager(config)


def create_rag_chain(retriever: DocumentRetriever, config=None) -> RAGChain:
    """Factory function to create RAG chain."""
    llm_manager = create_llm_manager(config)
    conversation_manager = create_conversation_manager(config)
    return RAGChain(retriever, llm_manager, conversation_manager, config)


class ResponseProcessor:
    """Processes and formats LLM responses."""
    
    @staticmethod
    def format_response_for_display(rag_result: Dict[str, Any]) -> str:
        """Format RAG result for user-friendly display."""
        if not rag_result.get("success"):
            return f"❌ Error: {rag_result.get('error', 'Unknown error')}"
        
        response = rag_result["response"]
        retrieval_count = len(rag_result.get("retrieval_results", []))
        
        formatted = f"🤖 Assistant: {response}\n"
        
        if retrieval_count > 0:
            formatted += f"\n📚 Based on {retrieval_count} retrieved documents"
        
        return formatted 