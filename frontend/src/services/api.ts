import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  AuthToken, 
  CodeExecution, 
  CodeProject, 
  CodeFile, 
  Conversation, 
  Message, 
  ChatResponse 
} from '../types';

class ApiService {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: 'http://localhost:8001/api',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth token
    this.api.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Token ${this.token}`;
      }
      return config;
    });

    // Load token from localStorage
    this.token = localStorage.getItem('authToken');
  }

  // Authentication
  async login(username: string, password: string): Promise<AuthToken> {
    const response: AxiosResponse<AuthToken> = await this.api.post('/auth/token/', {
      username,
      password,
    });
    this.token = response.data.token;
    localStorage.setItem('authToken', this.token);
    return response.data;
  }

  logout(): void {
    this.token = null;
    localStorage.removeItem('authToken');
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  // Code Execution
  async executeCode(code: string, language: string, projectId?: string): Promise<CodeExecution> {
    const response: AxiosResponse<CodeExecution> = await this.api.post('/code/execute/', {
      code,
      language,
      project_id: projectId,
    });
    return response.data;
  }

  async getExecutionHistory(): Promise<CodeExecution[]> {
    const response: AxiosResponse<CodeExecution[]> = await this.api.get('/code/executions/');
    return response.data;
  }

  // Projects
  async createProject(name: string, language: string, description?: string): Promise<CodeProject> {
    const response: AxiosResponse<CodeProject> = await this.api.post('/code/projects/create/', {
      name,
      language,
      description,
    });
    return response.data;
  }

  async getProjects(): Promise<CodeProject[]> {
    const response: AxiosResponse<CodeProject[]> = await this.api.get('/code/projects/');
    return response.data;
  }

  async getProjectDetail(projectId: string): Promise<CodeProject & { files: CodeFile[] }> {
    const response: AxiosResponse<CodeProject & { files: CodeFile[] }> = await this.api.get(`/code/projects/${projectId}/`);
    return response.data;
  }

  async saveFile(projectId: string, filename: string, content: string): Promise<CodeFile> {
    const response: AxiosResponse<CodeFile> = await this.api.post(`/code/projects/${projectId}/files/`, {
      filename,
      content,
    });
    return response.data;
  }

  async deleteFile(projectId: string, filename: string): Promise<void> {
    await this.api.delete(`/code/projects/${projectId}/files/${filename}/`);
  }

  // Chat
  async startConversation(title?: string): Promise<{ conversation_id: string; session_id: string; title: string }> {
    const response = await this.api.post('/chat/conversations/start/', { title });
    return response.data;
  }

  async sendMessage(conversationId: string, message: string, useTools: boolean = true, workflow?: string): Promise<ChatResponse> {
    const response: AxiosResponse<ChatResponse> = await this.api.post(`/chat/conversations/${conversationId}/message/`, {
      message,
      use_tools: useTools,
      workflow,
    });
    return response.data;
  }

  async getConversationHistory(conversationId: string): Promise<{ conversation_id: string; title: string; messages: Message[]; message_count: number }> {
    const response = await this.api.get(`/chat/conversations/${conversationId}/`);
    return response.data;
  }

  async getConversations(): Promise<Conversation[]> {
    const response: AxiosResponse<Conversation[]> = await this.api.get('/chat/conversations/');
    return response.data;
  }

  async deleteConversation(conversationId: string): Promise<void> {
    await this.api.delete(`/chat/conversations/${conversationId}/delete/`);
  }

  // Agent Tools
  async getAgentTools(): Promise<{ tools: any[]; workflows: string[] }> {
    const response = await this.api.get('/chat/tools/');
    return response.data;
  }

  async getAgentStatus(): Promise<any> {
    const response = await this.api.get('/chat/status/');
    return response.data;
  }

  // File Upload
  async uploadFile(file: File): Promise<{ success: boolean; document_id?: string; error?: string }> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await this.api.post('/knowledge/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
}

export const apiService = new ApiService();