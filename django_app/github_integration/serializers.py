"""
Serializers for GitHub Integration app
"""
from rest_framework import serializers
from .models import GitHubRepository, GitHubFile, GitHubSearchResult, GitHubCodeExample, UserGitHubProfile


class GitHubRepositorySerializer(serializers.ModelSerializer):
    """Serializer for GitHubRepository model."""
    file_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GitHubRepository
        fields = [
            'id', 'github_id', 'name', 'full_name', 'description',
            'html_url', 'clone_url', 'language', 'stars_count',
            'forks_count', 'owner', 'is_private', 'created_at',
            'updated_at', 'last_indexed', 'file_count'
        ]
        read_only_fields = ['id', 'last_indexed', 'file_count']
    
    def get_file_count(self, obj):
        """Get the number of files tracked for this repository."""
        return obj.files.count()


class GitHubFileSerializer(serializers.ModelSerializer):
    """Serializer for GitHubFile model."""
    repository_name = serializers.CharField(source='repository.full_name', read_only=True)
    
    class Meta:
        model = GitHubFile
        fields = [
            'id', 'path', 'filename', 'content', 'sha', 'size',
            'download_url', 'file_type', 'language', 'last_fetched',
            'repository_name'
        ]
        read_only_fields = ['id', 'last_fetched', 'repository_name']


class GitHubSearchResultSerializer(serializers.ModelSerializer):
    """Serializer for GitHubSearchResult model."""
    
    class Meta:
        model = GitHubSearchResult
        fields = [
            'id', 'query', 'search_type', 'language', 'results_data',
            'total_count', 'search_time', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at']


class GitHubCodeExampleSerializer(serializers.ModelSerializer):
    """Serializer for GitHubCodeExample model."""
    repository_name = serializers.SerializerMethodField()
    added_by_username = serializers.CharField(source='added_by.username', read_only=True)
    vote_score = serializers.ReadOnlyField()
    
    class Meta:
        model = GitHubCodeExample
        fields = [
            'id', 'title', 'description', 'file_path', 'code_content',
            'language', 'concepts', 'difficulty_level', 'upvotes',
            'downvotes', 'vote_score', 'created_at', 'updated_at',
            'repository_name', 'added_by_username'
        ]
        read_only_fields = [
            'id', 'upvotes', 'downvotes', 'vote_score', 'created_at',
            'updated_at', 'repository_name', 'added_by_username'
        ]
    
    def get_repository_name(self, obj):
        """Get repository name if it exists."""
        return obj.repository.full_name if obj.repository else None


class UserGitHubProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserGitHubProfile model."""
    username = serializers.CharField(source='user.username', read_only=True)
    favorite_repos_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserGitHubProfile
        fields = [
            'username', 'github_username', 'preferred_languages',
            'search_history', 'created_at', 'updated_at',
            'favorite_repos_count'
        ]
        read_only_fields = ['username', 'created_at', 'updated_at', 'favorite_repos_count']
    
    def get_favorite_repos_count(self, obj):
        """Get the number of favorite repositories."""
        return obj.favorite_repos.count()