"""
Serializers for Code Execution app
"""
from rest_framework import serializers
from .models import CodeProject, CodeFile, CodeExecution, ErrorReport


class CodeFileSerializer(serializers.ModelSerializer):
    """Serializer for CodeFile model."""
    
    class Meta:
        model = CodeFile
        fields = [
            'id', 'filename', 'content', 'file_type', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CodeProjectSerializer(serializers.ModelSerializer):
    """Serializer for CodeProject model."""
    file_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CodeProject
        fields = [
            'id', 'name', 'description', 'language', 'is_public',
            'created_at', 'updated_at', 'file_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'file_count']
    
    def get_file_count(self, obj):
        """Get the number of files in the project."""
        return obj.files.count()


class CodeExecutionSerializer(serializers.ModelSerializer):
    """Serializer for CodeExecution model."""
    
    class Meta:
        model = CodeExecution
        fields = [
            'id', 'code_content', 'language', 'status', 'output',
            'error_output', 'execution_time', 'created_at', 
            'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'status', 'output', 'error_output', 'execution_time',
            'created_at', 'started_at', 'completed_at'
        ]


class ErrorReportSerializer(serializers.ModelSerializer):
    """Serializer for ErrorReport model."""
    
    class Meta:
        model = ErrorReport
        fields = [
            'id', 'error_type', 'error_message', 'traceback',
            'line_number', 'agent_suggestion', 'user_feedback',
            'resolved', 'created_at'
        ]
        read_only_fields = [
            'id', 'error_type', 'error_message', 'traceback',
            'line_number', 'agent_suggestion', 'created_at'
        ]