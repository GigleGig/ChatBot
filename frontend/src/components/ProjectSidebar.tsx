import React, { useState } from 'react';
import { CodeProject, CodeFile } from '../types';

interface ProjectSidebarProps {
  projects: CodeProject[];
  selectedProject?: CodeProject;
  selectedFile?: CodeFile;
  projectFiles: CodeFile[];
  onSelectProject: (project: CodeProject) => void;
  onSelectFile: (file: CodeFile) => void;
  onCreateProject: () => void;
  onCreateFile: (filename: string) => void;
}

const ProjectSidebar: React.FC<ProjectSidebarProps> = ({
  projects,
  selectedProject,
  selectedFile,
  projectFiles,
  onSelectProject,
  onSelectFile,
  onCreateProject,
  onCreateFile,
}) => {
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [showCreateFile, setShowCreateFile] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectLanguage, setNewProjectLanguage] = useState('python');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [newFileName, setNewFileName] = useState('');

  const handleCreateProject = () => {
    if (newProjectName.trim()) {
      // This would call the API through the parent component
      onCreateProject();
      setNewProjectName('');
      setNewProjectDescription('');
      setShowCreateProject(false);
    }
  };

  const handleCreateFile = () => {
    if (newFileName.trim()) {
      onCreateFile(newFileName.trim());
      setNewFileName('');
      setShowCreateFile(false);
    }
  };

  const getFileIcon = (filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'py': return '🐍';
      case 'js': return '📜';
      case 'ts': return '📘';
      case 'java': return '☕';
      case 'cpp': case 'c': return '⚙️';
      case 'go': return '🚀';
      case 'rs': return '🦀';
      default: return '📄';
    }
  };

  const getLanguageColor = (language: string) => {
    const colors: Record<string, string> = {
      python: '#3776ab',
      javascript: '#f7df1e',
      typescript: '#3178c6',
      java: '#ed8b00',
      cpp: '#00599c',
      go: '#00add8',
      rust: '#000000',
    };
    return colors[language] || '#666';
  };

  return (
    <div style={styles.container}>
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <h3 style={styles.sectionTitle}>Projects</h3>
          <button
            onClick={() => setShowCreateProject(true)}
            style={styles.addButton}
            title="Create new project"
          >
            +
          </button>
        </div>

        {showCreateProject && (
          <div style={styles.createForm}>
            <input
              type="text"
              placeholder="Project name"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              style={styles.input}
            />
            <select
              value={newProjectLanguage}
              onChange={(e) => setNewProjectLanguage(e.target.value)}
              style={styles.select}
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="java">Java</option>
              <option value="cpp">C++</option>
              <option value="go">Go</option>
              <option value="rust">Rust</option>
            </select>
            <textarea
              placeholder="Description (optional)"
              value={newProjectDescription}
              onChange={(e) => setNewProjectDescription(e.target.value)}
              style={styles.textarea}
              rows={2}
            />
            <div style={styles.formButtons}>
              <button onClick={handleCreateProject} style={styles.createButton}>
                Create
              </button>
              <button 
                onClick={() => setShowCreateProject(false)} 
                style={styles.cancelButton}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        <div style={styles.projectList}>
          {projects.map((project) => (
            <div
              key={project.id}
              onClick={() => onSelectProject(project)}
              style={{
                ...styles.projectItem,
                backgroundColor: selectedProject?.id === project.id ? '#e3f2fd' : 'white',
              }}
            >
              <div style={styles.projectInfo}>
                <div style={styles.projectName}>{project.name}</div>
                <div style={styles.projectMeta}>
                  <span
                    style={{
                      ...styles.languageTag,
                      backgroundColor: getLanguageColor(project.language),
                    }}
                  >
                    {project.language}
                  </span>
                  <span style={styles.fileCount}>{project.file_count} files</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedProject && (
        <div style={styles.section}>
          <div style={styles.sectionHeader}>
            <h4 style={styles.sectionTitle}>Files</h4>
            <button
              onClick={() => setShowCreateFile(true)}
              style={styles.addButton}
              title="Create new file"
            >
              +
            </button>
          </div>

          {showCreateFile && (
            <div style={styles.createForm}>
              <input
                type="text"
                placeholder="filename.ext"
                value={newFileName}
                onChange={(e) => setNewFileName(e.target.value)}
                style={styles.input}
              />
              <div style={styles.formButtons}>
                <button onClick={handleCreateFile} style={styles.createButton}>
                  Create
                </button>
                <button 
                  onClick={() => setShowCreateFile(false)} 
                  style={styles.cancelButton}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div style={styles.fileList}>
            {projectFiles.map((file) => (
              <div
                key={file.id}
                onClick={() => onSelectFile(file)}
                style={{
                  ...styles.fileItem,
                  backgroundColor: selectedFile?.id === file.id ? '#e8f5e8' : 'white',
                }}
              >
                <span style={styles.fileIcon}>{getFileIcon(file.filename)}</span>
                <span style={styles.fileName}>{file.filename}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    height: '100%',
    backgroundColor: '#f8f9fa',
    borderRight: '1px solid #ddd',
    width: '300px',
    overflow: 'hidden',
  },
  section: {
    borderBottom: '1px solid #ddd',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    backgroundColor: '#e9ecef',
    borderBottom: '1px solid #ddd',
  },
  sectionTitle: {
    margin: 0,
    fontSize: '16px',
    fontWeight: '600',
    color: '#333',
  },
  addButton: {
    width: '24px',
    height: '24px',
    borderRadius: '12px',
    border: 'none',
    backgroundColor: '#007bff',
    color: 'white',
    fontSize: '16px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  createForm: {
    padding: '12px 16px',
    backgroundColor: '#fff',
    borderBottom: '1px solid #ddd',
  },
  input: {
    width: '100%',
    padding: '8px',
    margin: '4px 0',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
  },
  select: {
    width: '100%',
    padding: '8px',
    margin: '4px 0',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
  },
  textarea: {
    width: '100%',
    padding: '8px',
    margin: '4px 0',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    resize: 'vertical' as const,
  },
  formButtons: {
    display: 'flex',
    gap: '8px',
    marginTop: '8px',
  },
  createButton: {
    padding: '6px 12px',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  cancelButton: {
    padding: '6px 12px',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  projectList: {
    maxHeight: '300px',
    overflowY: 'auto' as const,
  },
  projectItem: {
    padding: '12px 16px',
    borderBottom: '1px solid #e9ecef',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  projectInfo: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px',
  },
  projectName: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#333',
  },
  projectMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  languageTag: {
    padding: '2px 6px',
    borderRadius: '3px',
    fontSize: '10px',
    color: 'white',
    fontWeight: '500',
  },
  fileCount: {
    fontSize: '12px',
    color: '#666',
  },
  fileList: {
    maxHeight: '400px',
    overflowY: 'auto' as const,
  },
  fileItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    borderBottom: '1px solid #e9ecef',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  fileIcon: {
    fontSize: '16px',
  },
  fileName: {
    fontSize: '14px',
    color: '#333',
  },
};

export default ProjectSidebar;