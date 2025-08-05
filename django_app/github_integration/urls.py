"""
URLs for GitHub Integration app
"""
from django.urls import path
from . import views

app_name = 'github_integration'

urlpatterns = [
    # GitHub search
    path('search/', views.github_search, name='github_search'),
    path('search/code/', views.github_code_search, name='github_code_search'),
    
    # Repositories
    path('repositories/', views.list_repositories, name='list_repositories'),
    path('repositories/<uuid:repo_id>/', views.get_repository_detail, name='repository_detail'),
    path('repositories/<uuid:repo_id>/files/', views.get_repository_files, name='repository_files'),
    
    # Code examples
    path('examples/', views.list_code_examples, name='list_code_examples'),
    path('examples/create/', views.create_code_example, name='create_code_example'),
    path('examples/<uuid:example_id>/vote/', views.vote_code_example, name='vote_code_example'),
    
    # User profile
    path('profile/', views.get_github_profile, name='github_profile'),
    path('profile/update/', views.update_github_profile, name='update_github_profile'),
]