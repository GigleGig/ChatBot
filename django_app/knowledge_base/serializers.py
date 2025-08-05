"""
Serializers for Knowledge Base app
"""
from rest_framework import serializers
from .models import Document, DocumentChunk, SearchQuery, VectorStoreIndex


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    chunk_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'content', 'source_type', 'source_url',
            'source_metadata', 'file_type', 'file_size', 'language',
            'tags', 'created_at', 'updated_at', 'chunk_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'chunk_count']
    
    def get_chunk_count(self, obj):
        """Get the number of chunks for this document."""
        return obj.chunks.count()


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for DocumentChunk model."""
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = DocumentChunk
        fields = [
            'id', 'content', 'chunk_index', 'start_char', 'end_char',
            'metadata', 'embedding_id', 'created_at', 'document_title'
        ]
        read_only_fields = ['id', 'created_at', 'document_title']


class SearchQuerySerializer(serializers.ModelSerializer):
    """Serializer for SearchQuery model."""
    
    class Meta:
        model = SearchQuery
        fields = [
            'id', 'query_text', 'search_type', 'results_count',
            'response_time', 'user_rating', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class VectorStoreIndexSerializer(serializers.ModelSerializer):
    """Serializer for VectorStoreIndex model."""
    
    class Meta:
        model = VectorStoreIndex
        fields = [
            'id', 'name', 'description', 'collection_name', 'status',
            'document_count', 'chunk_count', 'last_updated', 'created_at',
            'config'
        ]
        read_only_fields = ['id', 'last_updated', 'created_at']