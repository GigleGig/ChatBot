"""
Configuration module for the Code Agent project.

This module handles all environment variables, API keys, and project settings.
It provides a centralized configuration management system using Pydantic for
data validation and type safety.

Key Components:
- Environment variable management
- API key configuration
- Model parameters and settings
- Vector store configuration
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class LLMConfig(BaseModel):
    """
    Configuration for Large Language Model settings.

    This class manages all LLM-related configuration including:
    - API keys and endpoints
    - Model parameters (temperature, max_tokens, etc.)
    - Provider-specific settings
    """

    model_config = {"protected_namespaces": ()}

    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    model_name: str = Field(default="gpt-3.5-turbo", description="OpenAI model name")
    temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Model temperature"
    )
    max_tokens: int = Field(
        default=1000, gt=0, description="Maximum tokens in response"
    )

    # LangChain Configuration
    langchain_tracing: bool = Field(
        default=True, description="Enable LangChain tracing"
    )
    langchain_endpoint: str = Field(
        default="https://api.smith.langchain.com", description="LangChain endpoint"
    )
    langchain_api_key: str = Field(..., description="LangChain API key")

    @field_validator("temperature")
    def validate_temperature(cls, v):
        """Validate temperature is within acceptable range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class VectorStoreConfig(BaseModel):
    """
    Configuration for vector store and embeddings.

    Manages settings for:
    - Vector database configuration
    - Embedding model settings
    - Document processing parameters
    """

    # Vector Store Settings
    vector_store_type: str = Field(
        default="chroma", description="Type of vector store (chroma, faiss)"
    )
    collection_name: str = Field(
        default="code_agent_docs", description="Collection name in vector store"
    )
    persist_directory: str = Field(
        default="./vector_store", description="Directory to persist vector store"
    )

    # Embedding Settings
    embedding_model: str = Field(
        default="text-embedding-ada-002", description="Embedding model name"
    )
    chunk_size: int = Field(
        default=1000, gt=0, description="Text chunk size for processing"
    )
    chunk_overlap: int = Field(
        default=200, ge=0, description="Overlap between text chunks"
    )

    # Search Settings
    search_k: int = Field(
        default=5, gt=0, description="Number of documents to retrieve"
    )
    search_type: str = Field(
        default="similarity", description="Type of search (similarity, mmr)"
    )


class AgentConfig(BaseModel):
    """
    Configuration for the agent behavior and capabilities.

    Controls:
    - Agent tools and capabilities
    - Memory management
    - Execution parameters
    """

    # Agent Settings
    agent_name: str = Field(default="CodeAgent", description="Name of the agent")
    max_iterations: int = Field(
        default=10, gt=0, description="Maximum agent iterations"
    )
    max_execution_time: int = Field(
        default=60, gt=0, description="Maximum execution time in seconds"
    )

    # Memory Settings
    memory_type: str = Field(
        default="buffer", description="Type of memory (buffer, summary)"
    )
    memory_max_tokens: int = Field(
        default=2000, gt=0, description="Maximum tokens in memory"
    )

    # Tool Settings
    enable_code_execution: bool = Field(
        default=False, description="Enable code execution tools"
    )
    enable_file_operations: bool = Field(
        default=True, description="Enable file operation tools"
    )
    enable_web_search: bool = Field(
        default=False, description="Enable web search tools"
    )


class ProjectConfig(BaseModel):
    """
    Main project configuration that combines all sub-configurations.

    This is the main configuration class that aggregates all other
    configuration components and provides a single point of access
    for all project settings.
    """

    # Sub-configurations
    llm: LLMConfig
    vector_store: VectorStoreConfig
    agent: AgentConfig

    # Project Settings
    project_name: str = Field(
        default="Code Agent RAG System", description="Project name"
    )
    version: str = Field(default="1.0.0", description="Project version")
    debug: bool = Field(default=False, description="Debug mode")

    # Logging Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")


def load_config() -> ProjectConfig:
    """
    Load configuration from environment variables.

    This function creates a ProjectConfig instance by reading values from
    environment variables. It handles missing required values and provides
    appropriate defaults for optional settings.

    Environment Variables Required:
    - OPENAI_API_KEY: OpenAI API key
    - LANGCHAIN_API_KEY: LangChain API key

    Environment Variables Optional:
    - LANGCHAIN_TRACING_V2: Enable LangChain tracing (default: true)
    - LANGCHAIN_ENDPOINT: LangChain endpoint URL
    - MODEL_NAME: OpenAI model name (default: gpt-3.5-turbo)
    - TEMPERATURE: Model temperature (default: 0.1)
    - DEBUG: Debug mode (default: false)

    Returns:
        ProjectConfig: Configured project settings

    Raises:
        ValueError: If required environment variables are missing
        ValidationError: If configuration values are invalid
    """

    # Required environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    if not langchain_api_key:
        raise ValueError("LANGCHAIN_API_KEY environment variable is required")

    # Set LangChain environment variables
    if os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true":
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if os.getenv("LANGCHAIN_ENDPOINT"):
        os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT")
    os.environ["LANGCHAIN_API_KEY"] = langchain_api_key

    # Create configuration
    llm_config = LLMConfig(
        openai_api_key=openai_api_key,
        langchain_api_key=langchain_api_key,
        model_name=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
        temperature=float(os.getenv("TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("MAX_TOKENS", "1000")),
        langchain_tracing=os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true",
        langchain_endpoint=os.getenv(
            "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
        ),
    )

    vector_store_config = VectorStoreConfig(
        vector_store_type=os.getenv("VECTOR_STORE_TYPE", "chroma"),
        collection_name=os.getenv("COLLECTION_NAME", "code_agent_docs"),
        persist_directory=os.getenv("PERSIST_DIRECTORY", "./vector_store"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
    )

    agent_config = AgentConfig(
        agent_name=os.getenv("AGENT_NAME", "CodeAgent"),
        max_iterations=int(os.getenv("MAX_ITERATIONS", "10")),
        max_execution_time=int(os.getenv("MAX_EXECUTION_TIME", "60")),
        enable_code_execution=os.getenv("ENABLE_CODE_EXECUTION", "false").lower()
        == "true",
        enable_file_operations=os.getenv("ENABLE_FILE_OPERATIONS", "true").lower()
        == "true",
        enable_web_search=os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true",
    )

    return ProjectConfig(
        llm=llm_config,
        vector_store=vector_store_config,
        agent=agent_config,
        project_name=os.getenv("PROJECT_NAME", "Code Agent RAG System"),
        version=os.getenv("VERSION", "1.0.0"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


# Global configuration instance - will be loaded when needed
config = None


def get_config() -> ProjectConfig:
    """
    Get the global configuration instance, loading it if not already loaded.

    Returns:
        ProjectConfig: The loaded configuration
    """
    global config
    if config is None:
        config = load_config()
    return config
