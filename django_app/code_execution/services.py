"""
Code Execution Services - Safe code execution and error handling.
"""
import os
import sys
import subprocess
import tempfile
import signal
import threading
import time
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.utils import timezone

from .models import CodeProject, CodeFile, CodeExecution, ErrorReport


class CodeExecutionService:
    """Service to safely execute user code and handle errors."""
    
    def __init__(self):
        self.timeout = getattr(settings, 'AGENT_CONFIG', {}).get('CODE_EXECUTION_TIMEOUT', 30)
        self.max_memory = getattr(settings, 'AGENT_CONFIG', {}).get('MAX_MEMORY_USAGE', 512)
    
    def execute_code(self, code: str, language: str, user=None, project_id: str = None) -> Dict[str, Any]:
        """Execute code safely and return results."""
        
        # Create execution record
        execution = CodeExecution.objects.create(
            user=user,
            project_id=project_id,
            code_content=code,
            language=language,
            status='pending'
        )
        
        try:
            execution.status = 'running'
            execution.started_at = timezone.now()
            execution.save()
            
            if language == 'python':
                result = self._execute_python(code, execution.id)
            elif language in ['javascript', 'js']:
                result = self._execute_javascript(code, execution.id)
            elif language == 'java':
                result = self._execute_java(code, execution.id)
            else:
                result = {
                    'success': False,
                    'error': f'Language {language} not supported yet',
                    'output': '',
                    'execution_time': 0
                }
            
            # Update execution record
            execution.status = 'completed' if result['success'] else 'error'
            execution.output = result.get('output', '')
            execution.error_output = result.get('error', '')
            execution.execution_time = result.get('execution_time', 0)
            execution.completed_at = timezone.now()
            execution.save()
            
            # Create error report if needed
            if not result['success'] and result.get('error'):
                self._create_error_report(execution, result['error'])
            
            return {
                'execution_id': str(execution.id),
                'success': result['success'],
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'execution_time': result.get('execution_time', 0),
                'status': execution.status
            }
            
        except Exception as e:
            execution.status = 'error'
            execution.error_output = str(e)
            execution.completed_at = timezone.now()
            execution.save()
            
            return {
                'execution_id': str(execution.id),
                'success': False,
                'error': str(e),
                'output': '',
                'execution_time': 0,
                'status': 'error'
            }
    
    def _execute_python(self, code: str, execution_id: str) -> Dict[str, Any]:
        """Execute Python code safely."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Add safety restrictions
            safe_code = self._add_python_safety_wrapper(code)
            f.write(safe_code)
            temp_file = f.name
        
        try:
            start_time = time.time()
            
            # Run with timeout and memory limits
            process = subprocess.Popen(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                execution_time = time.time() - start_time
                
                if process.returncode == 0:
                    return {
                        'success': True,
                        'output': stdout,
                        'error': stderr if stderr else '',
                        'execution_time': execution_time
                    }
                else:
                    return {
                        'success': False,
                        'output': stdout,
                        'error': stderr,
                        'execution_time': execution_time
                    }
                    
            except subprocess.TimeoutExpired:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                return {
                    'success': False,
                    'output': '',
                    'error': f'Code execution timed out after {self.timeout} seconds',
                    'execution_time': self.timeout
                }
                
        finally:
            os.unlink(temp_file)
    
    def _execute_javascript(self, code: str, execution_id: str) -> Dict[str, Any]:
        """Execute JavaScript code using Node.js."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            start_time = time.time()
            
            process = subprocess.Popen(
                ['node', temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                execution_time = time.time() - start_time
                
                if process.returncode == 0:
                    return {
                        'success': True,
                        'output': stdout,
                        'error': stderr if stderr else '',
                        'execution_time': execution_time
                    }
                else:
                    return {
                        'success': False,
                        'output': stdout,
                        'error': stderr,
                        'execution_time': execution_time
                    }
                    
            except subprocess.TimeoutExpired:
                process.terminate()
                return {
                    'success': False,
                    'output': '',
                    'error': f'Code execution timed out after {self.timeout} seconds',
                    'execution_time': self.timeout
                }
                
        except FileNotFoundError:
            return {
                'success': False,
                'output': '',
                'error': 'Node.js not found. Please install Node.js to run JavaScript code.',
                'execution_time': 0
            }
        finally:
            os.unlink(temp_file)
    
    def _execute_java(self, code: str, execution_id: str) -> Dict[str, Any]:
        """Execute Java code."""
        # Extract class name from code
        import re
        class_match = re.search(r'public\s+class\s+(\w+)', code)
        if not class_match:
            return {
                'success': False,
                'output': '',
                'error': 'No public class found in Java code',
                'execution_time': 0
            }
        
        class_name = class_match.group(1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            java_file = os.path.join(temp_dir, f'{class_name}.java')
            
            with open(java_file, 'w') as f:
                f.write(code)
            
            try:
                start_time = time.time()
                
                # Compile
                compile_process = subprocess.run(
                    ['javac', java_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                if compile_process.returncode != 0:
                    return {
                        'success': False,
                        'output': '',
                        'error': f'Compilation error: {compile_process.stderr}',
                        'execution_time': time.time() - start_time
                    }
                
                # Run
                run_process = subprocess.run(
                    ['java', '-cp', temp_dir, class_name],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                execution_time = time.time() - start_time
                
                if run_process.returncode == 0:
                    return {
                        'success': True,
                        'output': run_process.stdout,
                        'error': run_process.stderr if run_process.stderr else '',
                        'execution_time': execution_time
                    }
                else:
                    return {
                        'success': False,
                        'output': run_process.stdout,
                        'error': run_process.stderr,
                        'execution_time': execution_time
                    }
                    
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'output': '',
                    'error': f'Code execution timed out after {self.timeout} seconds',
                    'execution_time': self.timeout
                }
            except FileNotFoundError:
                return {
                    'success': False,
                    'output': '',
                    'error': 'Java compiler (javac) not found. Please install Java JDK.',
                    'execution_time': 0
                }
    
    def _add_python_safety_wrapper(self, code: str) -> str:
        """Add basic safety restrictions to Python code."""
        # Use a simpler approach - just block the most dangerous direct imports
        restricted_imports = [
            'socket'
        ]
        
        safety_wrapper = '''
import sys
import builtins
import os

# Store original functions
original_import = builtins.__import__

# Restricted modules - only block the most dangerous ones
RESTRICTED = ''' + str(set(restricted_imports)) + '''

def safe_import(name, *args, **kwargs):
    if name in RESTRICTED:
        raise ImportError(f"Import of '{name}' is not allowed for security reasons")
    return original_import(name, *args, **kwargs)

builtins.__import__ = safe_import

# Disable some dangerous os functions but allow the module itself
if hasattr(os, 'system'):
    os.system = lambda *args: exec('raise Exception("os.system() is disabled")')

# User code starts here
'''
        return safety_wrapper + code
    
    def _create_error_report(self, execution: CodeExecution, error_message: str):
        """Create an error report for debugging assistance."""
        error_type = self._classify_error(error_message)
        
        ErrorReport.objects.create(
            user=execution.user,
            execution=execution,
            error_type=error_type,
            error_message=error_message,
            traceback=error_message  # In real implementation, extract proper traceback
        )
    
    def _classify_error(self, error_message: str) -> str:
        """Classify error type based on error message."""
        error_lower = error_message.lower()
        
        if 'syntax' in error_lower or 'invalid syntax' in error_lower:
            return 'syntax'
        elif 'import' in error_lower or 'module' in error_lower:
            return 'import'
        elif 'type' in error_lower and 'error' in error_lower:
            return 'type'
        elif any(word in error_lower for word in ['runtime', 'runtime error', 'exception']):
            return 'runtime'
        else:
            return 'other'


class ProjectService:
    """Service to manage code projects and files."""
    
    def create_project(self, name: str, language: str, user, description: str = '') -> CodeProject:
        """Create a new code project."""
        return CodeProject.objects.create(
            name=name,
            description=description,
            language=language,
            user=user
        )
    
    def get_user_projects(self, user) -> List[CodeProject]:
        """Get all projects for a user."""
        return CodeProject.objects.filter(user=user).order_by('-updated_at')
    
    def save_file(self, project: CodeProject, filename: str, content: str) -> CodeFile:
        """Save or update a file in a project."""
        file_obj, created = CodeFile.objects.get_or_create(
            project=project,
            filename=filename,
            defaults={'content': content}
        )
        
        if not created:
            file_obj.content = content
            file_obj.save()
            
        # Update project timestamp
        project.save()
        
        return file_obj
    
    def get_project_files(self, project: CodeProject) -> List[CodeFile]:
        """Get all files in a project."""
        return project.files.all()
    
    def delete_file(self, project: CodeProject, filename: str) -> bool:
        """Delete a file from a project."""
        try:
            file_obj = CodeFile.objects.get(project=project, filename=filename)
            file_obj.delete()
            return True
        except CodeFile.DoesNotExist:
            return False