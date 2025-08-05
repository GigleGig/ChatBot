"""
Code Execution API Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import CodeProject, CodeFile, CodeExecution, ErrorReport
from .serializers import CodeProjectSerializer, CodeFileSerializer, CodeExecutionSerializer, ErrorReportSerializer
from .services import CodeExecutionService, ProjectService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_code(request):
    """Execute code and return results."""
    code = request.data.get('code', '')
    language = request.data.get('language', 'python')
    project_id = request.data.get('project_id')
    
    if not code:
        return Response({'error': 'Code cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    execution_service = CodeExecutionService()
    result = execution_service.execute_code(
        code=code,
        language=language,
        user=request.user,
        project_id=project_id
    )
    
    return Response(result)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_execution_history(request):
    """Get user's code execution history."""
    executions = CodeExecution.objects.filter(user=request.user).order_by('-created_at')[:50]
    serializer = CodeExecutionSerializer(executions, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_execution_detail(request, execution_id):
    """Get detailed execution results."""
    execution = get_object_or_404(CodeExecution, id=execution_id, user=request.user)
    serializer = CodeExecutionSerializer(execution)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_project(request):
    """Create a new code project."""
    project_service = ProjectService()
    
    name = request.data.get('name', '')
    language = request.data.get('language', 'python')
    description = request.data.get('description', '')
    
    if not name:
        return Response({'error': 'Project name is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    project = project_service.create_project(
        name=name,
        language=language,
        user=request.user,
        description=description
    )
    
    serializer = CodeProjectSerializer(project)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_projects(request):
    """List user's code projects."""
    project_service = ProjectService()
    projects = project_service.get_user_projects(request.user)
    serializer = CodeProjectSerializer(projects, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_project_detail(request, project_id):
    """Get project details with files."""
    project = get_object_or_404(CodeProject, id=project_id, user=request.user)
    project_service = ProjectService()
    
    files = project_service.get_project_files(project)
    
    project_data = CodeProjectSerializer(project).data
    project_data['files'] = CodeFileSerializer(files, many=True).data
    
    return Response(project_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_file(request, project_id):
    """Save or update a file in the project."""
    project = get_object_or_404(CodeProject, id=project_id, user=request.user)
    project_service = ProjectService()
    
    filename = request.data.get('filename', '')
    content = request.data.get('content', '')
    
    if not filename:
        return Response({'error': 'Filename is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    file_obj = project_service.save_file(project, filename, content)
    serializer = CodeFileSerializer(file_obj)
    
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_file(request, project_id, filename):
    """Delete a file from the project."""
    project = get_object_or_404(CodeProject, id=project_id, user=request.user)
    project_service = ProjectService()
    
    success = project_service.delete_file(project, filename)
    
    if success:
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
    else:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_error_reports(request):
    """Get user's error reports."""
    errors = ErrorReport.objects.filter(user=request.user, resolved=False).order_by('-created_at')[:20]
    serializer = ErrorReportSerializer(errors, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_error_resolved(request, error_id):
    """Mark an error report as resolved."""
    error_report = get_object_or_404(ErrorReport, id=error_id, user=request.user)
    error_report.resolved = True
    error_report.user_feedback = request.data.get('feedback', '')
    error_report.save()
    
    return Response({'success': True})
