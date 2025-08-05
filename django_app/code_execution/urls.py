"""
URLs for Code Execution app
"""
from django.urls import path
from . import views

app_name = 'code_execution'

urlpatterns = [
    # Code execution
    path('execute/', views.execute_code, name='execute_code'),
    path('executions/', views.get_execution_history, name='execution_history'),
    path('executions/<uuid:execution_id>/', views.get_execution_detail, name='execution_detail'),
    
    # Projects
    path('projects/', views.list_projects, name='list_projects'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<uuid:project_id>/', views.get_project_detail, name='project_detail'),
    
    # Files
    path('projects/<uuid:project_id>/files/', views.save_file, name='save_file'),
    path('projects/<uuid:project_id>/files/<str:filename>/', views.delete_file, name='delete_file'),
    
    # Errors
    path('errors/', views.get_error_reports, name='error_reports'),
    path('errors/<uuid:error_id>/resolve/', views.mark_error_resolved, name='resolve_error'),
]