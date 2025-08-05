"""
GitHub Integration API Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import GitHubRepository, GitHubFile, GitHubSearchResult, GitHubCodeExample, UserGitHubProfile
from .serializers import GitHubRepositorySerializer, GitHubCodeExampleSerializer, UserGitHubProfileSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def github_search(request):
    """Search GitHub repositories."""
    query = request.data.get('query', '')
    language = request.data.get('language', '')
    search_type = request.data.get('search_type', 'repositories')
    
    if not query:
        return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Placeholder for GitHub search functionality
    # In production, this would integrate with GitHub API
    return Response({
        'success': True,
        'query': query,
        'search_type': search_type,
        'language': language,
        'results': [],
        'total_count': 0,
        'message': 'GitHub search functionality will be implemented with actual GitHub API integration'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def github_code_search(request):
    """Search GitHub code files."""
    query = request.data.get('query', '')
    language = request.data.get('language', '')
    fetch_content = request.data.get('fetch_content', False)
    
    if not query:
        return Response({'error': 'Query is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Placeholder for GitHub code search functionality
    return Response({
        'success': True,
        'query': query,
        'language': language,
        'fetch_content': fetch_content,
        'results': [],
        'total_count': 0,
        'files_with_content': 0,
        'message': 'GitHub code search functionality will be implemented with actual GitHub API integration'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_repositories(request):
    """List stored GitHub repositories."""
    repositories = GitHubRepository.objects.all().order_by('-stars_count')[:50]
    serializer = GitHubRepositorySerializer(repositories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_repository_detail(request, repo_id):
    """Get repository details."""
    repository = get_object_or_404(GitHubRepository, id=repo_id)
    serializer = GitHubRepositorySerializer(repository)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_repository_files(request, repo_id):
    """Get files in a repository."""
    repository = get_object_or_404(GitHubRepository, id=repo_id)
    files = repository.files.all()[:100]  # Limit to prevent overload
    
    file_data = []
    for file_obj in files:
        file_data.append({
            'id': str(file_obj.id),
            'path': file_obj.path,
            'filename': file_obj.filename,
            'size': file_obj.size,
            'file_type': file_obj.file_type,
            'language': file_obj.language,
            'last_fetched': file_obj.last_fetched
        })
    
    return Response({
        'repository': repository.full_name,
        'files': file_data,
        'total_files': len(file_data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_code_examples(request):
    """List curated code examples."""
    language = request.GET.get('language', '')
    difficulty = request.GET.get('difficulty', '')
    
    examples = GitHubCodeExample.objects.all()
    
    if language:
        examples = examples.filter(language=language)
    if difficulty:
        examples = examples.filter(difficulty_level=difficulty)
    
    examples = examples.order_by('-upvotes')[:20]
    serializer = GitHubCodeExampleSerializer(examples, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_code_example(request):
    """Create a new code example."""
    title = request.data.get('title', '')
    description = request.data.get('description', '')
    code_content = request.data.get('code_content', '')
    language = request.data.get('language', '')
    concepts = request.data.get('concepts', [])
    difficulty_level = request.data.get('difficulty_level', 'intermediate')
    
    if not all([title, code_content, language]):
        return Response({'error': 'Title, code content, and language are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # For now, create a placeholder repository if none exists
    # In production, this would be linked to actual repositories
    example = GitHubCodeExample.objects.create(
        title=title,
        description=description,
        code_content=code_content,
        language=language,
        concepts=concepts,
        difficulty_level=difficulty_level,
        added_by=request.user
    )
    
    serializer = GitHubCodeExampleSerializer(example)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vote_code_example(request, example_id):
    """Vote on a code example."""
    example = get_object_or_404(GitHubCodeExample, id=example_id)
    vote_type = request.data.get('vote_type', '')  # 'up' or 'down'
    
    if vote_type == 'up':
        example.upvotes += 1
    elif vote_type == 'down':
        example.downvotes += 1
    else:
        return Response({'error': 'Invalid vote type'}, status=status.HTTP_400_BAD_REQUEST)
    
    example.save()
    
    return Response({
        'success': True,
        'upvotes': example.upvotes,
        'downvotes': example.downvotes,
        'vote_score': example.vote_score
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_github_profile(request):
    """Get user's GitHub profile."""
    try:
        profile = request.user.github_profile
        serializer = UserGitHubProfileSerializer(profile)
        return Response(serializer.data)
    except UserGitHubProfile.DoesNotExist:
        return Response({'error': 'GitHub profile not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_github_profile(request):
    """Update user's GitHub profile."""
    github_username = request.data.get('github_username', '')
    preferred_languages = request.data.get('preferred_languages', [])
    
    profile, created = UserGitHubProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'github_username': github_username,
            'preferred_languages': preferred_languages
        }
    )
    
    if not created:
        profile.github_username = github_username
        profile.preferred_languages = preferred_languages
        profile.save()
    
    serializer = UserGitHubProfileSerializer(profile)
    return Response(serializer.data)
