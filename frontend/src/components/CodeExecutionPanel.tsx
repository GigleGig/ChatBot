import React, { useState, useEffect } from 'react';
import { CodeExecution } from '../types';

interface CodeExecutionPanelProps {
  execution?: CodeExecution;
  isExecuting: boolean;
}

const CodeExecutionPanel: React.FC<CodeExecutionPanelProps> = ({ execution, isExecuting }) => {
  const [activeTab, setActiveTab] = useState<'output' | 'error'>('output');

  useEffect(() => {
    if (execution) {
      setActiveTab(execution.success ? 'output' : 'error');
    }
  }, [execution]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#28a745';
      case 'error': return '#dc3545';
      case 'running': return '#ffc107';
      case 'pending': return '#6c757d';
      case 'timeout': return '#fd7e14';
      default: return '#6c757d';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✓';
      case 'error': return '✗';
      case 'running': return '⟳';
      case 'pending': return '⏳';
      case 'timeout': return '⏰';
      default: return '?';
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h4 style={styles.title}>Execution Results</h4>
        {execution && (
          <div style={styles.statusInfo}>
            <span
              style={{
                ...styles.statusBadge,
                backgroundColor: getStatusColor(execution.status),
              }}
            >
              {getStatusIcon(execution.status)} {execution.status}
            </span>
            <span style={styles.executionTime}>
              {execution.execution_time.toFixed(3)}s
            </span>
          </div>
        )}
        {isExecuting && (
          <div style={styles.statusInfo}>
            <span style={{...styles.statusBadge, backgroundColor: '#ffc107'}}>
              ⟳ Running...
            </span>
          </div>
        )}
      </div>

      {(execution || isExecuting) && (
        <>
          <div style={styles.tabs}>
            <button
              onClick={() => setActiveTab('output')}
              style={{
                ...styles.tab,
                backgroundColor: activeTab === 'output' ? '#007bff' : '#f8f9fa',
                color: activeTab === 'output' ? 'white' : '#333',
              }}
            >
              Output
              {execution && execution.output && (
                <span style={styles.contentIndicator}>•</span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('error')}
              style={{
                ...styles.tab,
                backgroundColor: activeTab === 'error' ? '#dc3545' : '#f8f9fa',
                color: activeTab === 'error' ? 'white' : '#333',
              }}
            >
              Errors
              {execution && execution.error && (
                <span style={styles.contentIndicator}>•</span>
              )}
            </button>
          </div>

          <div style={styles.content}>
            {isExecuting ? (
              <div style={styles.loading}>
                <div style={styles.spinner}></div>
                <span>Executing code...</span>
              </div>
            ) : execution ? (
              <div style={styles.outputContainer}>
                {activeTab === 'output' && (
                  <pre style={styles.output}>
                    {execution.output || 'No output generated'}
                  </pre>
                )}
                {activeTab === 'error' && (
                  <pre style={{...styles.output, color: '#dc3545'}}>
                    {execution.error || 'No errors'}
                  </pre>
                )}
              </div>
            ) : (
              <div style={styles.placeholder}>
                <p>No execution results yet.</p>
                <p>Run some code to see output here.</p>
              </div>
            )}
          </div>

          {execution && (
            <div style={styles.footer}>
              <div style={styles.executionInfo}>
                <span style={styles.infoItem}>
                  <strong>Execution ID:</strong> {execution.execution_id.substring(0, 8)}...
                </span>
                <span style={styles.infoItem}>
                  <strong>Status:</strong> {execution.status}
                </span>
                <span style={styles.infoItem}>
                  <strong>Time:</strong> {execution.execution_time.toFixed(3)}s
                </span>
              </div>
            </div>
          )}
        </>
      )}

      {!execution && !isExecuting && (
        <div style={styles.placeholder}>
          <div style={styles.placeholderContent}>
            <h5>Ready to Execute</h5>
            <p>Write some code and press "Run Code" or use Ctrl+Enter to execute.</p>
            <div style={styles.tips}>
              <h6>Tips:</h6>
              <ul>
                <li>Use print() statements to see output</li>
                <li>Code runs in a secure sandbox environment</li>
                <li>Execution time is limited for safety</li>
                <li>Import restrictions apply for security</li>
              </ul>
            </div>
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
    backgroundColor: 'white',
    border: '1px solid #ddd',
    borderRadius: '4px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    borderBottom: '1px solid #ddd',
    backgroundColor: '#f8f9fa',
  },
  title: {
    margin: 0,
    fontSize: '16px',
    color: '#333',
  },
  statusInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  statusBadge: {
    padding: '4px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '500',
    color: 'white',
  },
  executionTime: {
    fontSize: '12px',
    color: '#666',
    fontFamily: 'monospace',
  },
  tabs: {
    display: 'flex',
    borderBottom: '1px solid #ddd',
  },
  tab: {
    flex: 1,
    padding: '8px 16px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'all 0.2s',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '4px',
  },
  contentIndicator: {
    fontSize: '16px',
    color: '#28a745',
  },
  content: {
    flex: 1,
    overflow: 'hidden',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '32px',
    color: '#666',
  },
  spinner: {
    width: '16px',
    height: '16px',
    border: '2px solid #f3f3f3',
    borderTop: '2px solid #007bff',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  outputContainer: {
    height: '100%',
    overflow: 'auto',
  },
  output: {
    margin: 0,
    padding: '16px',
    fontSize: '13px',
    fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
    lineHeight: '1.4',
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-word' as const,
    backgroundColor: '#fafafa',
    color: '#333',
    height: '100%',
    border: 'none',
  },
  placeholder: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    padding: '32px',
    color: '#666',
    textAlign: 'center' as const,
  },
  placeholderContent: {
    maxWidth: '300px',
  },
  tips: {
    marginTop: '16px',
    textAlign: 'left' as const,
    fontSize: '12px',
    color: '#888',
  },
  footer: {
    padding: '8px 16px',
    borderTop: '1px solid #ddd',
    backgroundColor: '#f8f9fa',
  },
  executionInfo: {
    display: 'flex',
    gap: '16px',
    flexWrap: 'wrap' as const,
  },
  infoItem: {
    fontSize: '12px',
    color: '#666',
  },
};

// Add CSS animation for spinner
const spinKeyframes = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = spinKeyframes;
document.head.appendChild(styleSheet);

export default CodeExecutionPanel;