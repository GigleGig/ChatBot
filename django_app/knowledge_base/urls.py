"""
URLs for Knowledge Base app
"""
from django.urls import path
from . import views

app_name = 'knowledge_base'

urlpatterns = [
    # Documents
    path('documents/', views.list_documents, name='list_documents'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/<uuid:document_id>/', views.get_document_detail, name='document_detail'),
    path('documents/<uuid:document_id>/delete/', views.delete_document, name='delete_document'),
    
    # File uploads
    path('upload/', views.upload_file, name='upload_file'),
    
    # Search
    path('search/', views.search_documents, name='search_documents'),
    path('rag/', views.rag_query, name='rag_query'),
    
    # Vector store management
    path('index/status/', views.get_index_status, name='index_status'),
    path('index/rebuild/', views.rebuild_index, name='rebuild_index'),
]