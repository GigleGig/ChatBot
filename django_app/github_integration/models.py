from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class GitHubRepository(models.Model):
    """Track GitHub repositories and their metadata."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    github_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    html_url = models.URLField()
    clone_url = models.URLField()
    language = models.CharField(max_length=50, blank=True)
    stars_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    owner = models.CharField(max_length=255)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    last_indexed = models.DateTimeField(null=True, blank=True)
    indexed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='indexed_repos')
    
    class Meta:
        ordering = ['-stars_count', '-updated_at']
    
    def __str__(self):
        return self.full_name


class GitHubFile(models.Model):
    """Files from GitHub repositories."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey(GitHubRepository, on_delete=models.CASCADE, related_name='files')
    path = models.TextField()
    filename = models.CharField(max_length=255)
    content = models.TextField()
    sha = models.CharField(max_length=40)
    size = models.IntegerField()
    download_url = models.URLField()
    file_type = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=50, blank=True)
    last_fetched = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['repository', 'path']
        ordering = ['repository', 'path']
    
    def __str__(self):
        return f"{self.repository.full_name}/{self.path}"


class GitHubSearchResult(models.Model):
    """Store GitHub search results for caching and analysis."""
    
    SEARCH_TYPE_CHOICES = [
        ('repositories', 'Repositories'),
        ('code', 'Code'),
        ('commits', 'Commits'),
        ('issues', 'Issues'),
        ('users', 'Users'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='github_searches')
    query = models.TextField()
    search_type = models.CharField(max_length=20, choices=SEARCH_TYPE_CHOICES)
    language = models.CharField(max_length=50, blank=True)
    results_data = models.JSONField(default=dict)
    total_count = models.IntegerField(default=0)
    search_time = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"GitHub Search: {self.query[:50]}... ({self.search_type})"


class GitHubCodeExample(models.Model):
    """Curated code examples from GitHub for learning."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    repository = models.ForeignKey(GitHubRepository, on_delete=models.CASCADE, related_name='code_examples', null=True, blank=True)
    file_path = models.TextField()
    code_content = models.TextField()
    language = models.CharField(max_length=50)
    concepts = models.JSONField(default=list, blank=True)  # Programming concepts demonstrated
    difficulty_level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ], default='intermediate')
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='added_examples')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-upvotes', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.language})"
    
    @property
    def vote_score(self):
        return self.upvotes - self.downvotes


class UserGitHubProfile(models.Model):
    """User's GitHub profile and preferences."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='github_profile')
    github_username = models.CharField(max_length=255, blank=True)
    github_token = models.CharField(max_length=255, blank=True)  # Encrypted in production
    preferred_languages = models.JSONField(default=list, blank=True)
    favorite_repos = models.ManyToManyField(GitHubRepository, blank=True, related_name='favorited_by')
    search_history = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"GitHub Profile: {self.user.username}"
