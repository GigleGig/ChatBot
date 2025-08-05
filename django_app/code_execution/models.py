from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class CodeProject(models.Model):
    """User's coding projects."""
    
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('typescript', 'TypeScript'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
        ('swift', 'Swift'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='code_projects')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.language}) - {self.user.username}"


class CodeFile(models.Model):
    """Files within a code project."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(CodeProject, on_delete=models.CASCADE, related_name='files')
    filename = models.CharField(max_length=255)
    content = models.TextField(default='')
    file_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['project', 'filename']
        ordering = ['filename']
    
    def __str__(self):
        return f"{self.project.name}/{self.filename}"


class CodeExecution(models.Model):
    """Track code execution sessions and results."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='code_executions')
    project = models.ForeignKey(CodeProject, on_delete=models.CASCADE, related_name='executions', null=True, blank=True)
    code_content = models.TextField()
    language = models.CharField(max_length=20, choices=CodeProject.LANGUAGE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    output = models.TextField(blank=True)
    error_output = models.TextField(blank=True)
    execution_time = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Execution {self.id} - {self.status}"


class ErrorReport(models.Model):
    """Error reports and debugging information."""
    
    ERROR_TYPE_CHOICES = [
        ('syntax', 'Syntax Error'),
        ('runtime', 'Runtime Error'),
        ('logic', 'Logic Error'),
        ('import', 'Import Error'),
        ('type', 'Type Error'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='error_reports')
    execution = models.ForeignKey(CodeExecution, on_delete=models.CASCADE, related_name='error_reports', null=True, blank=True)
    error_type = models.CharField(max_length=20, choices=ERROR_TYPE_CHOICES)
    error_message = models.TextField()
    traceback = models.TextField(blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    agent_suggestion = models.TextField(blank=True)
    user_feedback = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Error {self.error_type} - {self.error_message[:50]}..."
