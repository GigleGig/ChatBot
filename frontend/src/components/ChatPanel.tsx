import React, { useState, useEffect, useRef } from 'react';
import { apiService } from '../services/api';
import { Message, ChatResponse } from '../types';

interface ChatPanelProps {
  conversationId?: string;
  onNewConversation: () => void;
  onCodeInsert?: (code: string) => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ conversationId, onNewConversation, onCodeInsert }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [chatMode, setChatMode] = useState<'chat' | 'agent'>('chat');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (conversationId) {
      loadConversationHistory();
    } else {
      setMessages([]);
    }
  }, [conversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadConversationHistory = async () => {
    if (!conversationId) return;
    
    try {
      const response = await apiService.getConversationHistory(conversationId);
      setMessages(response.messages);
    } catch (error) {
      console.error('Failed to load conversation:', error);
      setError('Failed to load conversation history');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const extractCodeFromResponse = (response: string): string | null => {
    // Extract code blocks from markdown format
    const codeBlockRegex = /```(?:python|javascript|java|js|py)?\n?([\s\S]*?)```/i;
    const match = response.match(codeBlockRegex);
    return match ? match[1].trim() : null;
  };

  const handleFileUpload = async (files: FileList) => {
    const validFiles = Array.from(files).filter(file => {
      const validTypes = ['text/plain', 'application/pdf', 'image/png', 'image/jpeg'];
      return validTypes.includes(file.type) || file.name.endsWith('.txt');
    });

    if (validFiles.length === 0) {
      setError('Please upload valid files: PDF, TXT, PNG, or JPG');
      return;
    }

    setUploadedFiles(prev => [...prev, ...validFiles]);
    
    // Upload files to knowledge base
    for (const file of validFiles) {
      try {
        await apiService.uploadFile(file);
      } catch (error) {
        console.error('Failed to upload file:', error);
        setError(`Failed to upload ${file.name}`);
      }
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !conversationId || loading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setLoading(true);
    setError('');

    // Add user message to UI immediately
    const newUserMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response: ChatResponse = await apiService.sendMessage(
        conversationId, 
        userMessage,
        true,
        chatMode === 'agent' ? 'code_assistant' : undefined
      );
      
      // Add assistant response
      const assistantMessage: Message = {
        id: response.message_id,
        role: 'assistant',
        content: response.response,
        tools_used: response.tools_used,
        execution_time: response.execution_time,
        created_at: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, assistantMessage]);

      // Auto-insert code if in agent mode
      if (chatMode === 'agent' && onCodeInsert) {
        const extractedCode = extractCodeFromResponse(response.response);
        if (extractedCode) {
          onCodeInsert(extractedCode);
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Failed to send message. Please try again.');
      
      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'error',
        content: 'Failed to get response from agent. Please try again.',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatMessage = (content: string) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, index) => (
        <span key={index}>
          {line}
          {index < content.split('\n').length - 1 && <br />}
        </span>
      ));
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'user': return '#007bff';
      case 'assistant': return '#28a745';
      case 'system': return '#6c757d';
      case 'error': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'user': return 'You';
      case 'assistant': return 'Agent';
      case 'system': return 'System';
      case 'error': return 'Error';
      default: return role;
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>AI Code Agent</h3>
        <div style={styles.headerControls}>
          <div style={styles.modeSelector}>
            <label>
              <input
                type="radio"
                name="chatMode"
                value="chat"
                checked={chatMode === 'chat'}
                onChange={(e) => setChatMode(e.target.value as 'chat' | 'agent')}
              />
              Chat Mode
            </label>
            <label>
              <input
                type="radio"
                name="chatMode"
                value="agent"
                checked={chatMode === 'agent'}
                onChange={(e) => setChatMode(e.target.value as 'chat' | 'agent')}
              />
              Agent Mode (Auto-apply code)
            </label>
          </div>
          <button onClick={onNewConversation} style={styles.newChatButton}>
            New Chat
          </button>
        </div>
      </div>

      <div style={styles.messagesContainer}>
        {messages.length === 0 && !conversationId && (
          <div style={styles.welcomeMessage}>
            <h4>Welcome to Code Agent Platform</h4>
            <p>Start a new conversation to get coding assistance from your AI agent.</p>
            <ul style={styles.featureList}>
              <li>Ask questions about programming concepts</li>
              <li>Get help debugging your code</li>
              <li>Request code examples and explanations</li>
              <li>Search GitHub for relevant implementations</li>
            </ul>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} style={styles.messageWrapper}>
            <div
              style={{
                ...styles.message,
                backgroundColor: message.role === 'user' ? '#e3f2fd' : '#f8f9fa',
              }}
            >
              <div style={styles.messageHeader}>
                <span
                  style={{
                    ...styles.roleLabel,
                    color: getRoleColor(message.role),
                  }}
                >
                  {getRoleLabel(message.role)}
                </span>
                <span style={styles.timestamp}>
                  {new Date(message.created_at).toLocaleTimeString()}
                </span>
              </div>
              <div style={styles.messageContent}>
                {formatMessage(message.content)}
              </div>
              {message.tools_used && message.tools_used.length > 0 && (
                <div style={styles.toolsUsed}>
                  <small>Tools used: {message.tools_used.join(', ')}</small>
                </div>
              )}
              {message.execution_time && (
                <div style={styles.executionTime}>
                  <small>Response time: {message.execution_time.toFixed(2)}s</small>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div style={styles.messageWrapper}>
            <div style={styles.loadingMessage}>
              <span>Agent is thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {/* File Upload Section */}
      <div style={styles.fileUploadSection}>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.txt,.png,.jpg,.jpeg"
          onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
          style={{ display: 'none' }}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          style={styles.fileUploadButton}
        >
          Upload Files (PDF, TXT, PNG)
        </button>
        {uploadedFiles.length > 0 && (
          <div style={styles.uploadedFiles}>
            <small>Uploaded: {uploadedFiles.map(f => f.name).join(', ')}</small>
          </div>
        )}
      </div>

      <div style={styles.inputContainer}>
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={
            conversationId 
              ? `${chatMode === 'agent' ? '[Agent Mode] Ask for code assistance...' : '[Chat Mode] Ask your agent anything...'}`
              : "Start a new conversation to begin chatting"
          }
          style={styles.messageInput}
          rows={3}
          disabled={!conversationId || loading}
        />
        <button
          onClick={handleSendMessage}
          disabled={!inputValue.trim() || !conversationId || loading}
          style={styles.sendButton}
        >
          Send
        </button>
      </div>
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
    padding: '16px',
    borderBottom: '1px solid #ddd',
    backgroundColor: '#f8f9fa',
  },
  title: {
    margin: 0,
    fontSize: '18px',
    color: '#333',
  },
  headerControls: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  modeSelector: {
    display: 'flex',
    gap: '8px',
    fontSize: '12px',
  },
  newChatButton: {
    padding: '6px 12px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  fileUploadSection: {
    padding: '8px 16px',
    borderTop: '1px solid #ddd',
    backgroundColor: '#f8f9fa',
  },
  fileUploadButton: {
    padding: '6px 12px',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    cursor: 'pointer',
  },
  uploadedFiles: {
    marginTop: '4px',
    color: '#666',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '16px',
    maxHeight: 'calc(100vh - 200px)',
  },
  welcomeMessage: {
    textAlign: 'center' as const,
    color: '#666',
    padding: '32px 16px',
  },
  featureList: {
    textAlign: 'left' as const,
    marginTop: '16px',
    color: '#888',
  },
  messageWrapper: {
    marginBottom: '12px',
  },
  message: {
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid #e9ecef',
  },
  messageHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  roleLabel: {
    fontWeight: 'bold',
    fontSize: '14px',
  },
  timestamp: {
    fontSize: '12px',
    color: '#666',
  },
  messageContent: {
    fontSize: '14px',
    lineHeight: '1.5',
    color: '#333',
  },
  toolsUsed: {
    marginTop: '8px',
    padding: '4px 8px',
    backgroundColor: '#e3f2fd',
    borderRadius: '4px',
    color: '#1976d2',
  },
  executionTime: {
    marginTop: '4px',
    color: '#666',
  },
  loadingMessage: {
    padding: '12px',
    borderRadius: '8px',
    backgroundColor: '#f8f9fa',
    border: '1px solid #e9ecef',
    color: '#666',
    fontStyle: 'italic',
  },
  error: {
    padding: '8px 16px',
    backgroundColor: '#f8d7da',
    color: '#721c24',
    borderTop: '1px solid #ddd',
    fontSize: '14px',
  },
  inputContainer: {
    display: 'flex',
    padding: '16px',
    borderTop: '1px solid #ddd',
    gap: '8px',
  },
  messageInput: {
    flex: 1,
    padding: '8px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    resize: 'none' as const,
    fontSize: '14px',
    outline: 'none',
  },
  sendButton: {
    padding: '8px 16px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    whiteSpace: 'nowrap' as const,
  },
};

export default ChatPanel;