import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { apiService } from '../services/api';
import ProjectSidebar from './ProjectSidebar';
import CodeEditor from './CodeEditor';
import ChatPanel from './ChatPanel';
import CodeExecutionPanel from './CodeExecutionPanel';
import { CodeProject, CodeFile, CodeExecution, SupportedLanguage } from '../types';

const MainLayout: React.FC = () => {
  const { logout } = useAuth();
  const [projects, setProjects] = useState<CodeProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<CodeProject | undefined>();
  const [selectedFile, setSelectedFile] = useState<CodeFile | undefined>();
  const [projectFiles, setProjectFiles] = useState<CodeFile[]>([]);
  const [currentCode, setCurrentCode] = useState('# Welcome to Code Agent Platform\n# Start coding!');
  const [currentLanguage, setCurrentLanguage] = useState<SupportedLanguage>('python');
  const [execution, setExecution] = useState<CodeExecution | undefined>();
  const [isExecuting, setIsExecuting] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [showChat, setShowChat] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadProjectFiles(selectedProject.id);
      setCurrentLanguage(selectedProject.language as SupportedLanguage);
    }
  }, [selectedProject]);

  const loadProjects = async () => {
    try {
      const projectsData = await apiService.getProjects();
      setProjects(projectsData);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  const loadProjectFiles = async (projectId: string) => {
    try {
      const projectDetail = await apiService.getProjectDetail(projectId);
      setProjectFiles(projectDetail.files);
    } catch (error) {
      console.error('Failed to load project files:', error);
    }
  };

  const handleSelectProject = (project: CodeProject) => {
    setSelectedProject(project);
    setSelectedFile(undefined);
    setCurrentCode('# Welcome to ' + project.name + '\n# Start coding!');
  };

  const handleSelectFile = (file: CodeFile) => {
    setSelectedFile(file);
    setCurrentCode(file.content);
  };

  const handleCreateProject = async () => {
    // This would be triggered by the sidebar component
    // For now, just reload projects
    await loadProjects();
  };

  const handleCreateFile = async (filename: string) => {
    if (!selectedProject) return;

    try {
      const newFile = await apiService.saveFile(selectedProject.id, filename, '');
      await loadProjectFiles(selectedProject.id);
      setSelectedFile(newFile);
      setCurrentCode('');
    } catch (error) {
      console.error('Failed to create file:', error);
    }
  };

  const handleCodeChange = (newCode: string) => {
    setCurrentCode(newCode);
  };

  const handleCodeInsert = (code: string) => {
    setCurrentCode(prevCode => {
      // If there's existing code, add the new code below it
      if (prevCode.trim()) {
        return prevCode + '\n\n' + code;
      }
      // Otherwise, replace with the new code
      return code;
    });
  };

  const handleSaveFile = async () => {
    if (!selectedProject || !selectedFile) return;

    try {
      await apiService.saveFile(selectedProject.id, selectedFile.filename, currentCode);
      console.log('File saved successfully');
    } catch (error) {
      console.error('Failed to save file:', error);
    }
  };

  const handleExecuteCode = async () => {
    if (!currentCode.trim()) return;

    setIsExecuting(true);
    setExecution(undefined);

    try {
      const result = await apiService.executeCode(
        currentCode,
        currentLanguage,
        selectedProject?.id
      );
      setExecution(result);
    } catch (error) {
      console.error('Failed to execute code:', error);
      setExecution({
        execution_id: 'error-' + Date.now(),
        success: false,
        output: '',
        error: 'Failed to execute code: ' + (error as Error).message,
        execution_time: 0,
        status: 'error',
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleNewConversation = async () => {
    try {
      const result = await apiService.startConversation('Code Discussion');
      setConversationId(result.conversation_id);
    } catch (error) {
      console.error('Failed to start conversation:', error);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.title}>Code Agent Platform</h1>
          <div style={styles.projectInfo}>
            {selectedProject && (
              <span style={styles.currentProject}>
                {selectedProject.name}
                {selectedFile && ` / ${selectedFile.filename}`}
              </span>
            )}
          </div>
        </div>
        <div style={styles.headerRight}>
          <button
            onClick={() => setShowChat(!showChat)}
            style={styles.toggleButton}
          >
            {showChat ? 'Hide Chat' : 'Show Chat'}
          </button>
          {selectedFile && (
            <button onClick={handleSaveFile} style={styles.saveButton}>
              Save File (Ctrl+S)
            </button>
          )}
          <button onClick={logout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </div>

      <div style={styles.content}>
        <ProjectSidebar
          projects={projects}
          selectedProject={selectedProject}
          selectedFile={selectedFile}
          projectFiles={projectFiles}
          onSelectProject={handleSelectProject}
          onSelectFile={handleSelectFile}
          onCreateProject={handleCreateProject}
          onCreateFile={handleCreateFile}
        />

        <div style={styles.mainContent}>
          <div style={styles.editorSection}>
            <CodeEditor
              value={currentCode}
              language={currentLanguage}
              onChange={handleCodeChange}
              onExecute={handleExecuteCode}
            />
          </div>

          <div style={styles.resultSection}>
            <CodeExecutionPanel
              execution={execution}
              isExecuting={isExecuting}
            />
          </div>
        </div>

        {showChat && (
          <div style={styles.chatSection}>
            <ChatPanel
              conversationId={conversationId}
              onNewConversation={handleNewConversation}
              onCodeInsert={handleCodeInsert}
            />
          </div>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    height: '100vh',
    backgroundColor: '#f5f5f5',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 24px',
    backgroundColor: 'white',
    borderBottom: '1px solid #ddd',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  title: {
    margin: 0,
    fontSize: '20px',
    fontWeight: '600',
    color: '#333',
  },
  projectInfo: {
    fontSize: '14px',
    color: '#666',
  },
  currentProject: {
    padding: '4px 8px',
    backgroundColor: '#e3f2fd',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '500',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  toggleButton: {
    padding: '6px 12px',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  saveButton: {
    padding: '6px 12px',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  logoutButton: {
    padding: '6px 12px',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  content: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },
  mainContent: {
    display: 'flex',
    flexDirection: 'column' as const,
    flex: 1,
    gap: '8px',
    padding: '8px',
  },
  editorSection: {
    flex: 1,
    minHeight: '400px',
  },
  resultSection: {
    height: '300px',
  },
  chatSection: {
    width: '400px',
    padding: '8px 8px 8px 0',
  },
};

export default MainLayout;