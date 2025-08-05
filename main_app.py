"""
Main Application Module for RAG Agent System

This module provides the main application interface that integrates all components:
- Document management and processing
- Vector store management
- RAG-powered conversations
- Agent capabilities with tools
- User-friendly interfaces

Key Components:
- RAGApplication: Main application class
- DocumentManager: Document upload and management
- ConversationInterface: User conversation handling
- ApplicationConfig: Application-specific configuration
- CLI and Web interfaces
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from config import get_config
from document_processor import DocumentProcessor
from vector_store import create_vector_store, create_retriever
from llm_integration import (
    create_llm_manager,
    create_conversation_manager,
    create_rag_chain,
)
from agent_core import create_agent, AgentWorkflow


class DocumentManager:
    """Manages document upload, processing, and indexing."""

    def __init__(self, config):
        """Initialize document manager."""
        self.config = config
        self.processor = DocumentProcessor(config)
        self.vector_store = create_vector_store(config)
        self.processed_documents = []
        self.document_stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "last_updated": None,
        }

    def add_document_from_file(self, file_path: str) -> Dict[str, Any]:
        """Add a document from file path."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            # Process document
            chunks = self.processor.process_file(str(file_path))

            if not chunks:
                return {
                    "success": False,
                    "error": f"No content extracted from {file_path.name}",
                }

            # Add to vector store
            self.vector_store.add_documents(chunks)

            # Update tracking
            self.processed_documents.append(
                {
                    "filename": file_path.name,
                    "path": str(file_path),
                    "chunks": len(chunks),
                    "processed_at": datetime.now().isoformat(),
                }
            )

            self.document_stats["total_documents"] += 1
            self.document_stats["total_chunks"] += len(chunks)
            self.document_stats["last_updated"] = datetime.now().isoformat()

            return {
                "success": True,
                "filename": file_path.name,
                "chunks_added": len(chunks),
                "total_chunks": self.document_stats["total_chunks"],
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process {file_path}: {str(e)}",
            }

    def add_document_from_text(
        self, text: str, title: str = "User Text"
    ) -> Dict[str, Any]:
        """Add a document from raw text."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as f:
                f.write(text)
                temp_path = f.name

            # Process the temporary file
            result = self.add_document_from_file(temp_path)

            # Clean up
            os.unlink(temp_path)

            if result["success"]:
                result["filename"] = title
                # Update the tracking info
                if self.processed_documents:
                    self.processed_documents[-1]["filename"] = title

            return result

        except Exception as e:
            return {"success": False, "error": f"Failed to process text: {str(e)}"}

    def add_documents_from_directory(
        self, directory_path: str, file_extensions: List[str] = None
    ) -> Dict[str, Any]:
        """Add all documents from a directory."""
        if file_extensions is None:
            file_extensions = [".txt", ".md", ".pdf", ".docx"]

        directory_path = Path(directory_path)
        if not directory_path.exists():
            return {"success": False, "error": f"Directory not found: {directory_path}"}

        results = []
        success_count = 0
        error_count = 0

        for file_path in directory_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                result = self.add_document_from_file(str(file_path))
                results.append({"filename": file_path.name, "result": result})

                if result["success"]:
                    success_count += 1
                else:
                    error_count += 1

        return {
            "success": success_count > 0,
            "total_files": len(results),
            "successful": success_count,
            "failed": error_count,
            "results": results,
            "total_chunks_added": sum(
                r["result"].get("chunks_added", 0)
                for r in results
                if r["result"]["success"]
            ),
        }

    def get_document_stats(self) -> Dict[str, Any]:
        """Get document statistics."""
        return {**self.document_stats, "processed_documents": self.processed_documents}

    def search_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search documents using the vector store."""
        try:
            retriever = create_retriever(self.vector_store, self.config)
            results = retriever.retrieve_documents(query, k=k)

            return [
                {
                    "content": result.chunk.content,
                    "score": result.score,
                    "source": result.chunk.source_document,
                    "chunk_index": result.chunk.chunk_index,
                }
                for result in results
            ]
        except Exception as e:
            return []


class ConversationInterface:
    """Manages user conversations and interactions."""

    def __init__(self, agent, workflow_manager):
        """Initialize conversation interface."""
        self.agent = agent
        self.workflow_manager = workflow_manager
        self.conversation_history = []
        self.current_conversation_id = None

    async def start_new_conversation(self) -> str:
        """Start a new conversation."""
        self.current_conversation_id = self.agent.conversation_id
        self.conversation_history = []
        return self.current_conversation_id

    async def send_message(
        self, message: str, use_workflow: str = None
    ) -> Dict[str, Any]:
        """Send a message and get response."""
        try:
            # Record user message
            self.conversation_history.append(
                {
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Process message
            if use_workflow:
                result = await self.workflow_manager.execute_workflow(
                    use_workflow, message
                )
            else:
                result = await self.agent.process_request(message, use_tools=True)

            # Record agent response
            if result["success"]:
                self.conversation_history.append(
                    {
                        "role": "assistant",
                        "content": result.get("response", ""),
                        "timestamp": datetime.now().isoformat(),
                        "tools_used": result.get("tools_used", []),
                        "workflow": use_workflow,
                    }
                )

            return result

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

            self.conversation_history.append(
                {
                    "role": "error",
                    "content": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return error_result

    def get_conversation_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get conversation history."""
        if limit:
            return self.conversation_history[-limit:]
        return self.conversation_history

    def clear_conversation(self):
        """Clear current conversation."""
        self.conversation_history = []
        self.agent.clear_memory()

    def get_available_workflows(self) -> List[str]:
        """Get available workflows."""
        return self.workflow_manager.list_workflows()


class RAGApplication:
    """Main RAG application that integrates all components."""

    def __init__(self, config=None):
        """Initialize the RAG application."""
        self.config = config or get_config()
        self.document_manager = None
        self.conversation_interface = None
        self.agent = None
        self.workflow_manager = None
        self.is_initialized = False

    async def initialize(self) -> Dict[str, Any]:
        """Initialize all application components."""
        try:
            print("🚀 Initializing RAG Application...")

            # Initialize document manager
            print("📄 Setting up document processing...")
            self.document_manager = DocumentManager(self.config)

            # Initialize RAG components
            print("🤖 Setting up LLM and conversation management...")
            llm_manager = create_llm_manager(self.config)
            conversation_manager = create_conversation_manager(self.config)
            retriever = create_retriever(
                self.document_manager.vector_store, self.config
            )

            # Create RAG chain
            print("🔗 Creating RAG chain...")
            rag_chain = create_rag_chain(retriever, self.config)

            # Initialize agent
            print("🎯 Setting up intelligent agent...")
            self.agent = create_agent(rag_chain, self.config)

            # Connect agent to document manager for proper statistics tracking
            self.agent.document_manager = self.document_manager

            # Re-register tools now that we have the document manager
            self.agent._register_default_tools()

            # Initialize workflow manager
            print("🌊 Setting up workflow management...")
            self.workflow_manager = AgentWorkflow(self.agent)

            # Initialize conversation interface
            print("💬 Setting up conversation interface...")
            self.conversation_interface = ConversationInterface(
                self.agent, self.workflow_manager
            )

            self.is_initialized = True

            print("✅ RAG Application initialized successfully!")

            return {
                "success": True,
                "message": "Application initialized successfully",
                "components": {
                    "document_manager": True,
                    "agent": True,
                    "workflows": len(self.workflow_manager.list_workflows()),
                    "tools": len(self.agent.tool_manager.list_tools()),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to initialize application: {str(e)}",
            }

    def get_application_status(self) -> Dict[str, Any]:
        """Get current application status."""
        if not self.is_initialized:
            return {"initialized": False, "message": "Application not initialized"}

        return {
            "initialized": True,
            "document_stats": self.document_manager.get_document_stats(),
            "agent_status": self.agent.get_agent_status(),
            "available_workflows": self.conversation_interface.get_available_workflows(),
            "memory_summary": self.agent.get_memory_summary(),
        }

    async def add_document(
        self, source: str, source_type: str = "file"
    ) -> Dict[str, Any]:
        """Add a document to the system."""
        if not self.is_initialized:
            return {"success": False, "error": "Application not initialized"}

        if source_type == "file":
            return self.document_manager.add_document_from_file(source)
        elif source_type == "text":
            return self.document_manager.add_document_from_text(source)
        elif source_type == "directory":
            return self.document_manager.add_documents_from_directory(source)
        else:
            return {"success": False, "error": f"Unknown source type: {source_type}"}

    async def chat(self, message: str, workflow: str = None) -> Dict[str, Any]:
        """Send a chat message."""
        if not self.is_initialized:
            return {"success": False, "error": "Application not initialized"}

        return await self.conversation_interface.send_message(message, workflow)

    def search_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search documents."""
        if not self.is_initialized:
            return []

        return self.document_manager.search_documents(query, k)

    def get_conversation_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get conversation history."""
        if not self.is_initialized:
            return []

        return self.conversation_interface.get_conversation_history(limit)

    def clear_conversation(self):
        """Clear current conversation."""
        if self.is_initialized:
            self.conversation_interface.clear_conversation()

    async def shutdown(self):
        """Shutdown the application gracefully."""
        print("🔄 Shutting down RAG Application...")

        if self.is_initialized:
            # Save conversation history if needed
            # Clean up resources
            pass

        print("✅ Application shutdown complete")


# Application factory function
async def create_rag_application(config=None) -> RAGApplication:
    """Factory function to create and initialize a RAG application."""
    app = RAGApplication(config)
    await app.initialize()
    return app


# CLI Helper functions
def display_welcome():
    """Display welcome message."""
    print("=" * 60)
    print("🤖 Welcome to the RAG Agent System!")
    print("=" * 60)
    print("This intelligent agent can help you with:")
    print("• 📄 Document processing and indexing")
    print("• 🔍 Intelligent document search")
    print("• 💬 Context-aware conversations")
    print("• 🛠️  Tool-assisted problem solving")
    print("• 🌊 Specialized workflows")
    print("=" * 60)


def display_help():
    """Display help information."""
    print("\n📖 Available Commands:")
    print("─" * 40)
    print("📄 Document Management:")
    print("  add <file_path>           - Add document from file")
    print("  add-text <text>           - Add document from text")
    print("  add-dir <directory>       - Add all documents from directory")
    print("  search <query>            - Search documents")
    print("  docs-stats                - Show document statistics")
    print()
    print("💬 Conversation:")
    print("  chat <message>            - Regular chat")
    print("  qa <question>             - Question answering workflow")
    print("  analyze <topic>           - Document analysis workflow")
    print("  research <topic>          - Research workflow")
    print("  history [limit]           - Show conversation history")
    print("  clear                     - Clear conversation")
    print()
    print("🔧 System:")
    print("  status                    - Show application status")
    print("  workflows                 - List available workflows")
    print("  tools                     - List available tools")
    print("  help                      - Show this help")
    print("  quit/exit                 - Exit application")
    print("─" * 40)


async def main():
    """Main application entry point."""
    try:
        # Display welcome
        display_welcome()

        # Initialize application
        print("\n🔄 Starting application initialization...")
        app = await create_rag_application()

        if not app.is_initialized:
            print("❌ Failed to initialize application")
            return

        print("\n📖 Type 'help' for available commands")
        print("🚀 Ready to assist you!")

        # Main interaction loop
        while True:
            try:
                user_input = input("\n🤖 RAG Agent > ").strip()

                if not user_input:
                    continue

                # Parse command
                parts = user_input.split(" ", 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                # Handle commands
                if command in ["quit", "exit"]:
                    break

                elif command == "help":
                    display_help()

                elif command == "status":
                    status = app.get_application_status()
                    print(f"\n📊 Application Status:")
                    print(
                        f"  📄 Documents: {status['document_stats']['total_documents']}"
                    )
                    print(f"  📝 Chunks: {status['document_stats']['total_chunks']}")
                    print(
                        f"  🧠 Memory items: {status['memory_summary']['short_term_items']}"
                    )
                    print(
                        f"  🛠️  Available tools: {len(status['agent_status']['tools'])}"
                    )

                elif command == "workflows":
                    workflows = app.conversation_interface.get_available_workflows()
                    print(f"\n🌊 Available Workflows: {', '.join(workflows)}")

                elif command == "tools":
                    tools = app.agent.tool_manager.list_tools()
                    print(f"\n🛠️  Available Tools:")
                    for tool in tools:
                        print(f"  • {tool['name']}: {tool['description']}")

                elif command == "add" and args:
                    result = await app.add_document(args, "file")
                    if result["success"]:
                        print(
                            f"✅ Added {result['filename']}: {result['chunks_added']} chunks"
                        )
                    else:
                        print(f"❌ Error: {result['error']}")

                elif command == "add-text" and args:
                    result = await app.add_document(args, "text")
                    if result["success"]:
                        print(f"✅ Added text document: {result['chunks_added']} chunks")
                    else:
                        print(f"❌ Error: {result['error']}")

                elif command == "add-dir" and args:
                    result = await app.add_document(args, "directory")
                    if result["success"]:
                        print(
                            f"✅ Added {result['successful']}/{result['total_files']} documents"
                        )
                        print(f"   Total chunks added: {result['total_chunks_added']}")
                    else:
                        print(f"❌ Error: {result['error']}")

                elif command == "search" and args:
                    results = app.search_documents(args, k=3)
                    if results:
                        print(f"\n🔍 Search Results for '{args}':")
                        for i, result in enumerate(results, 1):
                            print(f"\n{i}. Score: {result['score']:.3f}")
                            print(f"   Source: {result['source']}")
                            print(f"   Content: {result['content'][:200]}...")
                    else:
                        print("No results found.")

                elif command == "docs-stats":
                    stats = app.document_manager.get_document_stats()
                    print(f"\n📊 Document Statistics:")
                    print(f"  📄 Total documents: {stats['total_documents']}")
                    print(f"  📝 Total chunks: {stats['total_chunks']}")
                    print(f"  🕒 Last updated: {stats['last_updated']}")

                elif command == "chat" and args:
                    print("\n🤖 Processing your message...")
                    result = await app.chat(args)
                    if result["success"]:
                        print(f"\n🤖 Assistant: {result['response']}")
                        if result.get("tools_used"):
                            print(f"🛠️  Tools used: {', '.join(result['tools_used'])}")
                    else:
                        print(f"❌ Error: {result['error']}")

                elif command == "qa" and args:
                    print("\n🤖 Processing your question...")
                    result = await app.chat(args, workflow="question_answering")
                    if result["success"]:
                        print(f"\n🤖 Assistant: {result['response']}")
                    else:
                        print(f"❌ Error: {result['error']}")

                elif command == "analyze" and args:
                    print("\n🤖 Analyzing documents...")
                    result = await app.chat(args, workflow="document_analysis")
                    if result["success"]:
                        print(f"\n🤖 Analysis: {result['response']}")
                    else:
                        print(f"❌ Error: {result['error']}")

                elif command == "research" and args:
                    print("\n🤖 Conducting research...")
                    result = await app.chat(args, workflow="research")
                    if result["success"]:
                        print(f"\n🤖 Research Results: {result['response']}")
                    else:
                        print(f"❌ Error: {result['error']}")

                elif command == "history":
                    limit = int(args) if args.isdigit() else None
                    history = app.get_conversation_history(limit)

                    if history:
                        print(f"\n📝 Conversation History:")
                        for entry in history[-10:]:  # Show last 10
                            role_icon = "👤" if entry["role"] == "user" else "🤖"
                            print(f"{role_icon} {entry['content'][:100]}...")
                    else:
                        print("No conversation history.")

                elif command == "clear":
                    app.clear_conversation()
                    print("✅ Conversation cleared")

                else:
                    print(
                        f"❌ Unknown command: '{command}'. Type 'help' for available commands."
                    )

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

    except Exception as e:
        print(f"❌ Application error: {str(e)}")

    finally:
        if "app" in locals():
            await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
