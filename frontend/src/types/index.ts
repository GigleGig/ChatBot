// API Types
export interface User {
  id: string;
  username: string;
  email: string;
}

export interface AuthToken {
  token: string;
}

// Code Execution Types
export interface CodeExecution {
  execution_id: string;
  success: boolean;
  output: string;
  error: string;
  execution_time: number;
  status: 'pending' | 'running' | 'completed' | 'error' | 'timeout';
}

export interface CodeProject {
  id: string;
  name: string;
  description: string;
  language: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  file_count: number;
}

export interface CodeFile {
  id: string;
  filename: string;
  content: string;
  file_type: string;
  created_at: string;
  updated_at: string;
}

// Chat Types
export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  message_count: number;
  latest_message?: {
    role: string;
    content: string;
    created_at: string;
  };
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'error';
  content: string;
  metadata?: any;
  tools_used?: string[];
  created_at: string;
  execution_time?: number;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  tools_used: string[];
  execution_time: number;
  message_id: string;
}

// Component Props Types
export interface CodeEditorProps {
  value: string;
  language: string;
  onChange: (value: string) => void;
  onExecute?: () => void;
}

export interface ChatPanelProps {
  conversationId?: string;
  onNewConversation: () => void;
}

export interface ProjectSidebarProps {
  projects: CodeProject[];
  selectedProject?: CodeProject;
  onSelectProject: (project: CodeProject) => void;
  onCreateProject: () => void;
}

// Language Types
export type SupportedLanguage = 'python' | 'javascript' | 'typescript' | 'java' | 'cpp' | 'go' | 'rust';