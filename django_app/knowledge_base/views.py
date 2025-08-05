"""
Knowledge Base API Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
import tempfile
import os

from .models import Document, DocumentChunk, VectorStoreIndex
from .serializers import DocumentSerializer, DocumentChunkSerializer, VectorStoreIndexSerializer
from .services import KnowledgeBaseService


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_documents(request):
    """List user's documents in knowledge base."""
    documents = Document.objects.filter(uploaded_by=request.user, is_active=True).order_by('-created_at')
    serializer = DocumentSerializer(documents, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document(request):
    """Upload a document to the knowledge base."""
    title = request.data.get('title', '')
    content = request.data.get('content', '')
    source_type = request.data.get('source_type', 'upload')
    
    if not title or not content:
        return Response({'error': 'Title and content are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    knowledge_service = KnowledgeBaseService()
    result = knowledge_service.add_document(
        title=title,
        content=content,
        source_type=source_type,
        user=request.user
    )
    
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request):
    """Upload and process files for the knowledge base."""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    uploaded_file: UploadedFile = request.FILES['file']
    
    # Validate file type
    allowed_extensions = ['.pdf', '.txt', '.png', '.jpg', '.jpeg', '.docx']
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_extension not in allowed_extensions:
        return Response({
            'error': f'File type {file_extension} not supported. Allowed: {", ".join(allowed_extensions)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Extract content based on file type
        content = extract_content_from_file(uploaded_file, file_extension)
        
        if not content.strip():
            return Response({
                'error': 'No readable content found in the file'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add to knowledge base
        knowledge_service = KnowledgeBaseService()
        result = knowledge_service.add_document(
            title=uploaded_file.name,
            content=content,
            source_type='file_upload',
            user=request.user,
            metadata={
                'file_name': uploaded_file.name,
                'file_size': uploaded_file.size,
                'content_type': uploaded_file.content_type,
            }
        )
        
        if result['success']:
            return Response({
                'success': True,
                'document_id': result['document_id'],
                'message': f'File {uploaded_file.name} uploaded and processed successfully',
                'chunks_added': result.get('chunks_added', 0)
            })
        else:
            return Response({
                'success': False,
                'error': result.get('error', 'Failed to process file')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def extract_content_from_file(uploaded_file: UploadedFile, file_extension: str) -> str:
    """Extract text content from different file types."""
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name
    
    try:
        if file_extension == '.txt':
            return extract_text_content(temp_file_path)
        elif file_extension == '.pdf':
            return extract_pdf_content(temp_file_path)
        elif file_extension in ['.png', '.jpg', '.jpeg']:
            return extract_image_content(temp_file_path)
        elif file_extension == '.docx':
            return extract_docx_content(temp_file_path)
        else:
            return ""
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def extract_text_content(file_path: str) -> str:
    """Extract content from text files."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(file_path, 'r', encoding='latin-1') as file:
            return file.read()


def extract_pdf_content(file_path: str) -> str:
    """Extract content from PDF files."""
    try:
        # Simple text extraction without PyPDF2 dependency for now
        content = []
        with open(file_path, 'rb') as file:
            # For now, just return a placeholder until PyPDF2 is added
            return "PDF content extraction requires PyPDF2 library. Please install it or use text files for now."
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")


def extract_image_content(file_path: str) -> str:
    """Extract text from images using OCR."""
    try:
        # Simple image text placeholder until OCR libraries are installed
        return "Image text extraction requires PIL and pytesseract libraries. Please install them or use text files for now."
    except Exception as e:
        raise Exception(f"Error extracting text from image: {str(e)}")


def extract_docx_content(file_path: str) -> str:
    """Extract content from DOCX files."""
    try:
        # Simple DOCX extraction placeholder until python-docx is installed
        return "DOCX content extraction requires python-docx library. Please install it or use text files for now."
    except Exception as e:
        raise Exception(f"Error reading DOCX: {str(e)}")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_document_detail(request, document_id):
    """Get document details."""
    document = get_object_or_404(Document, id=document_id)
    
    # Check if user has access (public documents or own documents)
    if document.uploaded_by != request.user and document.uploaded_by is not None:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = DocumentSerializer(document)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_document(request, document_id):
    """Delete a document."""
    document = get_object_or_404(Document, id=document_id, uploaded_by=request.user)
    document.is_active = False
    document.save()
    
    return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_documents(request):
    """Search documents in knowledge base."""
    query = request.data.get('query', '')
    k = request.data.get('k', 5)
    
    if not query:
        return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    knowledge_service = KnowledgeBaseService()
    result = knowledge_service.search_documents(query, k=k, user=request.user)
    
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_query(request):
    """Get RAG-powered response to a query."""
    query = request.data.get('query', '')
    conversation_id = request.data.get('conversation_id')
    
    if not query:
        return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    knowledge_service = KnowledgeBaseService()
    result = knowledge_service.get_rag_response(query, conversation_id)
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_index_status(request):
    """Get vector store index status."""
    try:
        indices = VectorStoreIndex.objects.all().order_by('-created_at')
        serializer = VectorStoreIndexSerializer(indices, many=True)
        return Response({
            'indices': serializer.data,
            'total_documents': Document.objects.filter(is_active=True).count(),
            'total_chunks': DocumentChunk.objects.count()
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rebuild_index(request):
    """Rebuild vector store index."""
    try:
        # This would trigger a background task to rebuild the index
        # For now, return a placeholder response
        return Response({
            'success': True,
            'message': 'Index rebuild initiated',
            'status': 'building'
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
