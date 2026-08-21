import ast
import subprocess
import tempfile
import os
import time
from typing import Any

class SecurityViolationError(Exception):
    pass

class SecurityVisitor(ast.NodeVisitor):
    FORBIDDEN_MODULES = {
        'os', 'sys', 'subprocess', 'socket', 'ctypes', 'pty', 'shutil', 
        'urllib', 'requests', 'http', 'posix', 'pwd', 'grp', 'builtins',
        'importlib', 'runpy', 'platform'
    }

    FORBIDDEN_FUNCTIONS = {
        'eval', 'exec', 'compile', 'input', 'breakpoint', '__import__', 'open'
    }

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.name.split('.')[0]
            if name in self.FORBIDDEN_MODULES:
                raise SecurityViolationError(f"Import of forbidden module '{alias.name}' is blocked.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            name = node.module.split('.')[0]
            if name in self.FORBIDDEN_MODULES:
                raise SecurityViolationError(f"Import from forbidden module '{node.module}' is blocked.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check call by name (e.g. eval())
        if isinstance(node.func, ast.Name):
            if node.func.id in self.FORBIDDEN_FUNCTIONS:
                raise SecurityViolationError(f"Call to forbidden function '{node.func.id}()' is blocked.")
        # Check call on attributes (e.g. sys.exit() or os.system())
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in self.FORBIDDEN_MODULES:
                    raise SecurityViolationError(f"Call to forbidden module attribute '{node.func.value.id}.{node.func.attr}' is blocked.")
            # Also block opening files via path operations
            if node.func.attr == 'open':
                raise SecurityViolationError("File open operations are blocked in the sandbox.")
        self.generic_visit(node)


class SandboxExecutor:
    @staticmethod
    def validate_code(code: str) -> None:
        try:
            tree = ast.parse(code)
            visitor = SecurityVisitor()
            visitor.visit(tree)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in experiment script: {e}")
        except SecurityViolationError as e:
            raise SecurityViolationError(f"Sandbox Validation Blocked: {e}")

    @staticmethod
    def run_code(code: str, timeout_seconds: float = 10.0) -> dict[str, Any]:
        # Validate statically first
        SandboxExecutor.validate_code(code)

        # Write to temporary file
        temp_dir = os.path.join(os.getcwd(), "backend", "scratch")
        os.makedirs(temp_dir, exist_ok=True)
        
        fd, temp_path = tempfile.mkstemp(suffix=".py", dir=temp_dir)
        try:
            with os.fdopen(fd, 'w') as tmp:
                tmp.write(code)

            start_time = time.time()
            
            # Execute subprocess with stripped environment
            # Run using the same python executable running this backend process
            python_exe = os.sys.executable
            
            # Clean environment (remove parent env vars for security)
            clean_env = {
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
                "PATH": os.environ.get("PATH", "")
            }

            process = subprocess.Popen(
                [python_exe, temp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=clean_env,
                text=True
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout_seconds)
                execution_time = (time.time() - start_time) * 1000.0
                status = "COMPLETED" if process.returncode == 0 else "FAILED"
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                execution_time = (time.time() - start_time) * 1000.0
                status = "FAILED"
                stderr += f"\nTimeoutExpired: Execution exceeded limit of {timeout_seconds} seconds."

            return {
                "stdout": stdout,
                "stderr": stderr,
                "status": status,
                "execution_time_ms": execution_time
            }

        finally:
            # Clean up file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
