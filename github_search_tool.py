"""
GitHub Search Tool for RAG System

This module provides GitHub search capabilities including:
- Code search across repositories
- Repository search
- Issues and pull requests search
- User and organization search
- Real-time code information retrieval

Key Features:
- GitHub REST API integration
- Multiple search types
- Rate limiting handling
- Result caching
- Authentication support
"""

import os
import json
import time
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from enum import Enum
from urllib.parse import quote
import base64

from pydantic import BaseModel, Field, field_validator

from agent_core import Tool, ToolType, ToolResult


class GitHubSearchType(str, Enum):
    """Types of GitHub searches available."""
    CODE = "code"
    REPOSITORIES = "repositories"
    ISSUES = "issues"
    USERS = "users"
    COMMITS = "commits"
    TOPICS = "topics"


class GitHubSearchResult(BaseModel):
    """Individual GitHub search result."""
    title: str = Field(..., description="Result title")
    url: str = Field(..., description="Result URL")
    description: Optional[str] = Field(None, description="Result description")
    score: float = Field(..., description="Search relevance score")
    repository: Optional[str] = Field(None, description="Repository name")
    language: Optional[str] = Field(None, description="Programming language")
    created_at: Optional[str] = Field(None, description="Creation date")
    updated_at: Optional[str] = Field(None, description="Last update date")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class GitHubContentFetcher:
    """Fetches actual content from GitHub files and repositories."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize content fetcher."""
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RAG-System-GitHub-Search/1.0"
        }
        
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
    
    async def fetch_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> Optional[str]:
        """Fetch content of a specific file from GitHub repository."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
                params = {"ref": ref}
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # GitHub returns base64 encoded content
                        if data.get("encoding") == "base64":
                            content = base64.b64decode(data["content"]).decode('utf-8')
                            return content
                        else:
                            return data.get("content", "")
                    else:
                        print(f"❌ Failed to fetch content: HTTP {response.status}")
                        return None
        except Exception as e:
            print(f"❌ Error fetching content: {str(e)}")
            return None
    
    def extract_repo_info_from_url(self, url: str) -> Optional[Dict[str, str]]:
        """Extract owner, repo, and path from GitHub URL."""
        try:
            # Handle different GitHub URL formats
            if "github.com" in url:
                # Remove protocol and www
                url = url.replace("https://", "").replace("http://", "").replace("www.", "")
                
                # Parse URL parts
                parts = url.split("/")
                if len(parts) >= 3 and parts[0] == "github.com":
                    owner = parts[1]
                    repo = parts[2]
                    
                    # Extract file path if present
                    if len(parts) > 4 and parts[3] == "blob":
                        ref = parts[4]  # branch/commit
                        path = "/".join(parts[5:]) if len(parts) > 5 else ""
                        return {"owner": owner, "repo": repo, "path": path, "ref": ref}
                    else:
                        return {"owner": owner, "repo": repo, "path": "", "ref": "main"}
            return None
        except Exception:
            return None


class GitHubSearchWithContentTool(Tool):
    """Enhanced GitHub search tool that can fetch actual code content."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize GitHub search tool with content fetching capability."""
        super().__init__(
            name="github_search_with_content",
            description="Search GitHub for code and optionally fetch the actual content",
            tool_type=ToolType.EXTERNAL
        )
        
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.rate_limit_remaining = 60
        self.rate_limit_reset = time.time()
        self.content_fetcher = GitHubContentFetcher(github_token)
        
        # Setup headers
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RAG-System-GitHub-Search/1.0"
        }
        
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
            self.rate_limit_remaining = 5000
    
    async def execute(self, query: str, 
                     search_type: str = "code",
                     language: Optional[str] = None,
                     fetch_content: bool = True,
                     max_content_files: int = 3,
                     **kwargs) -> ToolResult:
        """Execute GitHub search and optionally fetch content."""
        start_time = datetime.now()
        
        try:
            print(f"🔍 GitHub Search with Content - Query: '{query}'")
            print(f"🔍 Language: {language}, Fetch content: {fetch_content}")
            
            # First, perform the search using existing logic
            search_result = await self._perform_github_search(query, search_type, language, **kwargs)
            
            results_with_content = []
            
            if search_result.get("items") and fetch_content:
                print(f"📥 Fetching content for up to {max_content_files} files from {len(search_result['items'])} results...")
                
                for i, item in enumerate(search_result["items"][:max_content_files]):
                    result_data = {
                        "title": item.get("name", "Unknown"),
                        "url": item.get("html_url", ""),
                        "repository": item.get("repository", {}).get("full_name", ""),
                        "path": item.get("path", ""),
                        "score": item.get("score", 0.0),
                        "content": None
                    }
                    
                    # Try to fetch the actual content
                    if "repository" in item and "path" in item:
                        repo_info = item["repository"]
                        owner = repo_info.get("owner", {}).get("login", "")
                        repo_name = repo_info.get("name", "")
                        file_path = item.get("path", "")
                        
                        if owner and repo_name and file_path:
                            print(f"📦 Fetching content from {owner}/{repo_name}/{file_path}")
                            content = await self.content_fetcher.fetch_file_content(
                                owner, repo_name, file_path
                            )
                            
                            if content:
                                result_data["content"] = content
                                print(f"✅ Successfully fetched {len(content)} characters")
                            else:
                                print(f"❌ Failed to fetch content")
                    
                    results_with_content.append(result_data)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                result={
                    "query": query,
                    "search_type": search_type,
                    "total_count": search_result.get("total_count", 0),
                    "results": results_with_content,
                    "content_fetched": fetch_content,
                    "files_with_content": len([r for r in results_with_content if r.get("content")])
                },
                execution_time=execution_time,
                metadata={
                    "language": language,
                    "max_content_files": max_content_files
                }
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"GitHub search with content failed: {str(e)}",
                execution_time=execution_time
            )
    
    async def _perform_github_search(self, query: str, search_type: str, 
                                   language: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Perform GitHub search (reusing existing logic)."""
        # Build search query
        search_parts = [query]
        if language:
            search_parts.append(f"language:{language}")
        
        search_query = " ".join(search_parts)
        
        # Perform search
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/search/{search_type}"
            params = {
                "q": search_query,
                "sort": kwargs.get("sort", "best-match"),
                "order": kwargs.get("order", "desc"),
                "per_page": min(kwargs.get("per_page", 5), 10),  # Limit to avoid rate limits
                "page": kwargs.get("page", 1)
            }
            
            print(f"🌐 API Request URL: {url}")
            print(f"🌐 Parameters: {params}")
            print(f"🌐 Headers: {self.headers}")
            
            async with session.get(url, headers=self.headers, params=params) as response:
                print(f"📊 API Response Status: {response.status}")
                
                # Update rate limit info
                self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                print(f"📊 Rate Limit Remaining: {self.rate_limit_remaining}")
                
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"GitHub API error: {response.status} - {error_text}")
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for GitHub code/repositories"
                },
                "search_type": {
                    "type": "string",
                    "enum": ["code", "repositories"],
                    "description": "Type of search to perform",
                    "default": "code"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language filter"
                },
                "fetch_content": {
                    "type": "boolean",
                    "description": "Whether to fetch actual file content",
                    "default": True
                },
                "max_content_files": {
                    "type": "integer",
                    "description": "Maximum number of files to fetch content for",
                    "default": 3
                }
            },
            "required": ["query"]
        }


class GitHubSearchTool(Tool):
    """Tool for searching GitHub repositories, code, and issues."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize GitHub search tool."""
        super().__init__(
            name="github_search",
            description="Search GitHub for code, repositories, issues, and users",
            tool_type=ToolType.EXTERNAL
        )
        
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.rate_limit_remaining = 60  # Default for unauthenticated requests
        self.rate_limit_reset = time.time()
        
        # Setup headers
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RAG-System-GitHub-Search/1.0"
        }
        
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
            self.rate_limit_remaining = 5000  # Authenticated requests
    
    async def execute(self, query: str, search_type: str = "code", 
                     language: Optional[str] = None, 
                     repository: Optional[str] = None,
                     user: Optional[str] = None,
                     sort: str = "best-match",
                     order: str = "desc",
                     per_page: int = 10,
                     page: int = 1) -> ToolResult:
        """Execute GitHub search."""
        start_time = datetime.now()
        
        try:
            print(f"🔍 GitHub Search - Original query: '{query}'")
            print(f"🔍 Search type: {search_type}, Language: {language}")
            
            # Validate search type
            if search_type not in [t.value for t in GitHubSearchType]:
                raise ValueError(f"Invalid search type: {search_type}")
            
            # Check rate limits
            if not await self._check_rate_limit():
                print("❌ Rate limit exceeded")
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error="GitHub API rate limit exceeded. Please try again later.",
                    execution_time=0.0
                )
            
            # Build search query
            search_query = await self._build_search_query(
                query, search_type, language, repository, user
            )
            
            print(f"🔍 Final search query: '{search_query}'")
            
            # Perform search
            results = await self._perform_search(
                search_type, search_query, sort, order, per_page, page
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Format results
            formatted_results = await self._format_results(results.get("items", []), search_type)
            total_count = results.get("total_count", 0)
            
            print(f"📊 GitHub API returned {total_count} total results")
            print(f"📊 Formatted {len(formatted_results)} results for return")
            
            if total_count == 0:
                print("⚠️  No results found. This might indicate:")
                print("   - Invalid GitHub token")
                print("   - Query too specific")
                print("   - API rate limits")
                print("   - Network issues")
            
            return ToolResult(
                tool_name=self.name,
                success=True,
                result={
                    "query": query,
                    "search_type": search_type,
                    "total_count": total_count,
                    "results": formatted_results,
                    "rate_limit_remaining": self.rate_limit_remaining
                },
                execution_time=execution_time,
                metadata={
                    "search_query": search_query,
                    "sort": sort,
                    "order": order,
                    "per_page": per_page,
                    "page": page
                }
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=f"GitHub search failed: {str(e)}",
                execution_time=execution_time
            )
    
    async def _check_rate_limit(self) -> bool:
        """Check if we can make API requests."""
        current_time = time.time()
        
        # If rate limit has reset, restore full quota
        if current_time >= self.rate_limit_reset:
            self.rate_limit_remaining = 5000 if self.github_token else 60
            self.rate_limit_reset = current_time + 3600  # Reset in 1 hour
        
        return self.rate_limit_remaining > 0
    
    async def _build_search_query(self, query: str, search_type: str, 
                                 language: Optional[str] = None,
                                 repository: Optional[str] = None,
                                 user: Optional[str] = None) -> str:
        """Build GitHub search query with filters."""
        search_parts = [query]
        
        if language:
            search_parts.append(f"language:{language}")
        
        if repository:
            search_parts.append(f"repo:{repository}")
        
        if user:
            search_parts.append(f"user:{user}")
        
        # Add search type specific filters
        if search_type == "code":
            # For code search, we might want to add file type filters
            pass
        elif search_type == "repositories":
            # For repository search, we might want to add stars, forks filters
            pass
        elif search_type == "issues":
            # For issues search, we might want to add state filters
            search_parts.append("is:issue")
        
        return " ".join(search_parts)
    
    async def _perform_search(self, search_type: str, query: str, 
                             sort: str, order: str, per_page: int, page: int) -> Dict[str, Any]:
        """Perform the actual GitHub API search."""
        url = f"{self.base_url}/search/{search_type}"
        
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100),  # GitHub API limit
            "page": page
        }
        
        print(f"🌐 API Request URL: {url}")
        print(f"🌐 Parameters: {params}")
        print(f"🌐 Headers: {self.headers}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                self.rate_limit_reset = int(response.headers.get("X-RateLimit-Reset", time.time()))
                
                print(f"📊 API Response Status: {response.status}")
                print(f"📊 Rate Limit Remaining: {self.rate_limit_remaining}")
                
                if response.status == 200:
                    json_data = await response.json()
                    print(f"📊 API returned {json_data.get('total_count', 0)} total results")
                    print(f"📊 API returned {len(json_data.get('items', []))} items")
                    return json_data
                elif response.status == 403:
                    error_text = await response.text()
                    print(f"❌ 403 Error: {error_text}")
                    raise Exception(f"GitHub API rate limit exceeded: {error_text}")
                elif response.status == 422:
                    error_text = await response.text()
                    print(f"❌ 422 Error: {error_text}")
                    raise Exception(f"Invalid search query: {error_text}")
                else:
                    error_text = await response.text()
                    print(f"❌ {response.status} Error: {error_text}")
                    raise Exception(f"GitHub API error {response.status}: {error_text}")
    
    async def _format_results(self, items: List[Dict[str, Any]], search_type: str) -> List[GitHubSearchResult]:
        """Format GitHub API results into standardized format."""
        formatted_results = []
        
        for item in items:
            try:
                if search_type == "code":
                    result = GitHubSearchResult(
                        title=item.get("name", "Unknown file"),
                        url=item.get("html_url", ""),
                        description=f"Code from {item.get('repository', {}).get('full_name', 'Unknown repo')}",
                        score=item.get("score", 0.0),
                        repository=item.get("repository", {}).get("full_name"),
                        language=item.get("repository", {}).get("language"),
                        metadata={
                            "path": item.get("path", ""),
                            "sha": item.get("sha", ""),
                            "git_url": item.get("git_url", ""),
                            "repository_url": item.get("repository", {}).get("html_url", "")
                        }
                    )
                
                elif search_type == "repositories":
                    result = GitHubSearchResult(
                        title=item.get("full_name", "Unknown repository"),
                        url=item.get("html_url", ""),
                        description=item.get("description", "No description available"),
                        score=item.get("score", 0.0),
                        repository=item.get("full_name"),
                        language=item.get("language"),
                        created_at=item.get("created_at"),
                        updated_at=item.get("updated_at"),
                        metadata={
                            "stars": item.get("stargazers_count", 0),
                            "forks": item.get("forks_count", 0),
                            "watchers": item.get("watchers_count", 0),
                            "open_issues": item.get("open_issues_count", 0),
                            "default_branch": item.get("default_branch", "main"),
                            "topics": item.get("topics", [])
                        }
                    )
                
                elif search_type == "issues":
                    result = GitHubSearchResult(
                        title=item.get("title", "Unknown issue"),
                        url=item.get("html_url", ""),
                        description=item.get("body", "No description available")[:200] + "..." if item.get("body") else "No description",
                        score=item.get("score", 0.0),
                        repository=item.get("repository_url", "").split("/")[-2:] if item.get("repository_url") else None,
                        created_at=item.get("created_at"),
                        updated_at=item.get("updated_at"),
                        metadata={
                            "number": item.get("number"),
                            "state": item.get("state"),
                            "user": item.get("user", {}).get("login"),
                            "labels": [label.get("name") for label in item.get("labels", [])],
                            "comments": item.get("comments", 0)
                        }
                    )
                
                elif search_type == "users":
                    result = GitHubSearchResult(
                        title=item.get("login", "Unknown user"),
                        url=item.get("html_url", ""),
                        description=item.get("bio", "No bio available"),
                        score=item.get("score", 0.0),
                        metadata={
                            "type": item.get("type"),
                            "public_repos": item.get("public_repos", 0),
                            "followers": item.get("followers", 0),
                            "following": item.get("following", 0),
                            "avatar_url": item.get("avatar_url", "")
                        }
                    )
                
                else:
                    # Generic format for other search types
                    result = GitHubSearchResult(
                        title=item.get("name", item.get("title", "Unknown")),
                        url=item.get("html_url", ""),
                        description=item.get("description", item.get("body", "No description"))[:200],
                        score=item.get("score", 0.0),
                        metadata=item
                    )
                
                formatted_results.append(result)
                
            except Exception as e:
                # Skip malformed results
                continue
        
        return formatted_results
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameters schema for GitHub search."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (keywords, function names, etc.)"
                },
                "search_type": {
                    "type": "string",
                    "enum": ["code", "repositories", "issues", "users", "commits", "topics"],
                    "description": "Type of GitHub search to perform",
                    "default": "code"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language filter (e.g., 'python', 'javascript')"
                },
                "repository": {
                    "type": "string",
                    "description": "Specific repository to search in (format: 'owner/repo')"
                },
                "user": {
                    "type": "string",
                    "description": "Specific user or organization to search in"
                },
                "sort": {
                    "type": "string",
                    "enum": ["best-match", "stars", "forks", "updated"],
                    "description": "Sort order for results",
                    "default": "best-match"
                },
                "order": {
                    "type": "string",
                    "enum": ["desc", "asc"],
                    "description": "Sort direction",
                    "default": "desc"
                },
                "per_page": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Number of results per page",
                    "default": 10
                },
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Page number for pagination",
                    "default": 1
                }
            },
            "required": ["query"]
        }


class GitHubCodeSearchTool(GitHubSearchTool):
    """Specialized tool for searching code on GitHub."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize GitHub code search tool."""
        super().__init__(github_token)
        self.name = "github_code_search"
        self.description = "Search for code snippets, functions, and implementations on GitHub"
    
    async def execute(self, query: str, language: Optional[str] = None, 
                     repository: Optional[str] = None, **kwargs) -> ToolResult:
        """Execute GitHub code search with simplified and effective queries."""
        # Force search type to code
        kwargs["search_type"] = "code"
        
        # Simplify query by extracting key terms
        # Remove unnecessary words and focus on the actual search intent
        import re
        
        # Extract meaningful keywords from the query
        # Remove common question words and phrases
        stop_words = {
            'can', 'you', 'looking', 'for', 'the', 'github', 'about', 'and', 'tell', 'me', 
            'how', 'many', 'results', 'have', 'got', 'search', 'find', 'show', 'get',
            'please', 'help', 'what', 'where', 'when', 'why', 'who', 'which', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'to', 'of', 'in', 'on',
            'at', 'by', 'from', 'with', 'without', 'through', 'during', 'before', 'after',
            'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'a', 'an', 'as', 'so', 'than', 'too', 'very',
            'just', 'now', 'here', 'there', 'where', 'this', 'that', 'these', 'those'
        }
        
        # Clean and extract keywords
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # If we have meaningful keywords, use them; otherwise use the original query
        if keywords:
            # Take the most meaningful keywords (limit to avoid overly complex queries)
            query = ' '.join(keywords[:3])
        
        print(f"🔍 Simplified search query: '{query}' (from original: '{kwargs.get('original_query', query)}')")
        
        return await super().execute(query, language=language, repository=repository, **kwargs)


def create_github_search_tool(github_token: Optional[str] = None) -> GitHubSearchTool:
    """Create a GitHub search tool instance."""
    return GitHubSearchTool(github_token)


def create_github_code_search_tool(github_token: Optional[str] = None) -> GitHubCodeSearchTool:
    """Create a specialized GitHub code search tool instance."""
    return GitHubCodeSearchTool(github_token)


def create_github_search_with_content_tool(github_token: Optional[str] = None) -> GitHubSearchWithContentTool:
    """Create a GitHub search with content tool instance."""
    return GitHubSearchWithContentTool(github_token)


# Example usage and testing
async def test_github_search():
    """Test function for GitHub search tool."""
    tool = create_github_search_tool()
    
    # Test code search
    result = await tool.execute(
        query="async def",
        search_type="code",
        language="python",
        per_page=5
    )
    
    print("GitHub Search Test Results:")
    print(f"Success: {result.success}")
    if result.success:
        print(f"Total results: {result.result['total_count']}")
        for i, res in enumerate(result.result['results'][:3]):
            print(f"{i+1}. {res.title} - {res.repository}")
            print(f"   URL: {res.url}")
            print(f"   Score: {res.score}")
    else:
        print(f"Error: {result.error}")


if __name__ == "__main__":
    asyncio.run(test_github_search()) 