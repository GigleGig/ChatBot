import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { CodeEditorProps, SupportedLanguage } from '../types';

const CodeEditor: React.FC<CodeEditorProps> = ({ value, language, onChange, onExecute }) => {
  const [editorTheme, setEditorTheme] = useState('vs-dark');

  const handleEditorChange = (newValue: string | undefined) => {
    onChange(newValue || '');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.ctrlKey && e.key === 'Enter' && onExecute) {
      e.preventDefault();
      onExecute();
    }
  };

  const getLanguageLabel = (lang: string): string => {
    const labels: Record<string, string> = {
      python: 'Python',
      javascript: 'JavaScript',
      typescript: 'TypeScript',
      java: 'Java',
      cpp: 'C++',
      go: 'Go',
      rust: 'Rust',
    };
    return labels[lang] || lang;
  };

  return (
    <div style={styles.container} onKeyDown={handleKeyDown}>
      <div style={styles.header}>
        <div style={styles.languageInfo}>
          <span style={styles.languageLabel}>{getLanguageLabel(language)}</span>
        </div>
        <div style={styles.controls}>
          <select
            value={editorTheme}
            onChange={(e) => setEditorTheme(e.target.value)}
            style={styles.themeSelect}
          >
            <option value="vs-dark">Dark Theme</option>
            <option value="light">Light Theme</option>
            <option value="hc-black">High Contrast</option>
          </select>
          {onExecute && (
            <button onClick={onExecute} style={styles.runButton}>
              Run Code (Ctrl+Enter)
            </button>
          )}
        </div>
      </div>
      <div style={styles.editorContainer}>
        <Editor
          height="100%"
          language={language}
          value={value}
          theme={editorTheme}
          onChange={handleEditorChange}
          options={{
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            readOnly: false,
            automaticLayout: true,
            minimap: { enabled: false },
            wordWrap: 'on',
            tabSize: 2,
            insertSpaces: true,
            renderWhitespace: 'selection',
            bracketPairColorization: { enabled: true },
          }}
        />
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column' as const,
    height: '100%',
    border: '1px solid #ddd',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 12px',
    backgroundColor: '#f8f9fa',
    borderBottom: '1px solid #ddd',
  },
  languageInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  languageLabel: {
    fontSize: '14px',
    fontWeight: '500',
    color: '#333',
  },
  controls: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  themeSelect: {
    padding: '4px 8px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '12px',
    backgroundColor: 'white',
  },
  runButton: {
    padding: '6px 12px',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  editorContainer: {
    flex: 1,
    minHeight: '300px',
  },
};

export default CodeEditor;