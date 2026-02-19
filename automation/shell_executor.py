# Path: automation/shell_executor.py
import subprocess
import shlex
import logging
import asyncio
from typing import Dict, Any

class ShellExecutor:
    """
    LUNA-ULTRA Shell Executor: Executes shell commands with permission gating and security hardening.
    Improved for better error reporting and subprocess stability.
    """
    def __init__(self, config: Dict[str, Any], permission_engine: Any):
        self.config = config
        self.permission_engine = permission_engine
        self.timeout = config.get('timeout', 60)

    async def execute(self, command: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Executes a command after permission check.
        Uses asyncio.to_thread to prevent blocking the main event loop.
        """
        # 1. Permission Check
        if not self.permission_engine.check_permission("shell_exec", command):
            return {
                "success": False, 
                "error": "Permission Denied by LUNA Security Engine.",
                "message": "The command was blocked for security reasons."
            }
        
        # 2. Dry-Run Mode
        if dry_run or self.config.get('dry_run', False):
            logging.info(f"ShellExecutor: DRY-RUN: {command}")
            return {
                "success": True, 
                "stdout": f"[DRY-RUN] Executed: {command}", 
                "stderr": "", 
                "returncode": 0,
                "message": "Dry-run successful."
            }
            
        try:
            # 3. Hardened Execution (No shell=True)
            # shlex.split might fail for complex commands with pipes, but we enforce this for security
            args = shlex.split(command)
            
            # Use asyncio.to_thread to run the blocking subprocess.run in a separate thread
            # this prevents the GUI/event loop from freezing
            result = await asyncio.to_thread(
                subprocess.run,
                args, 
                shell=False, 
                capture_output=True, 
                text=True, 
                timeout=self.timeout
            )
            
            success = result.returncode == 0
            return {
                "success": success, 
                "stdout": result.stdout, 
                "stderr": result.stderr,
                "returncode": result.returncode,
                "message": "Execution finished." if success else f"Command failed with return code {result.returncode}"
            }
        except subprocess.TimeoutExpired:
            logging.error(f"ShellExecutor: Command timed out: {command}")
            return {
                "success": False, 
                "error": f"Command timed out after {self.timeout} seconds.",
                "message": "The process took too long to respond."
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Executable not found for command: {command}",
                "message": "Please ensure the command exists and is in the system PATH."
            }
        except Exception as e:
            logging.error(f"ShellExecutor: Execution failed: {e}")
            return {
                "success": False, 
                "error": str(e),
                "message": "An unexpected error occurred during shell execution. Complex commands (pipes/redirects) may need to be split."
            }
