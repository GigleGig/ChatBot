from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Document(models.Model):
    """Documents stored in the knowledge base."""
    
    SOURCE_TYPE_CHOICES = [
        ('upload', 'User Upload'),
        ('github', 'GitHub'),
        ('web', 'Web Scraping'),
        ('user_input', 'User Input'),
        ('agent_generated', 'Agent Generated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    content = models.TextField()
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    source_url = models.URLField(blank=True, null=True)
    source_metadata = models.JSONField(default=dict, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents')
    file_type = models.CharField(max_length=50, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=50, blank=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title[:50]}... ({self.source_type})"


class DocumentChunk(models.Model):
    """Text chunks extracted from documents for vector storage."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    chunk_index = models.IntegerField()
    start_char = models.IntegerField(null=True, blank=True)
    end_char = models.IntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    embedding_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['document', 'chunk_index']
        ordering = ['document', 'chunk_index']
    
    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title[:30]}..."


class SearchQuery(models.Model):
    """Track user search queries for analytics and improvement."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='search_queries')
    query_text = models.TextField()
    search_type = models.CharField(max_length=50, default='similarity')
    results_count = models.IntegerField(default=0)
    response_time = models.FloatField(null=True, blank=True)
    user_rating = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Search: {self.query_text[:50]}..."


class VectorStoreIndex(models.Model):
    """Track vector store indices and their status."""
    
    STATUS_CHOICES = [
        ('building', 'Building'),
        ('active', 'Active'),
        ('updating', 'Updating'),
        ('error', 'Error'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    collection_name = models.CharField(max_length=200, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='building')
    document_count = models.IntegerField(default=0)
    chunk_count = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)
    config = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Index: {self.name} ({self.status})"
