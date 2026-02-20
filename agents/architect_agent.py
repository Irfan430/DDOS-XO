# Path: agents/architect_agent.py
# FIXED: BUG-001 - Added 'status' key to all return dicts for orchestrator compatibility
import os
import logging
from typing import Dict, Any, List
from llm.router import LLMRouter

class ArchitectAgent:
    """
    LUNA-ULTRA Architect Agent: Plans and builds multi-file projects.
    """
    def __init__(self, config: Dict[str, Any], llm_router: LLMRouter, permission_engine: Any = None):
        self.config = config
        self.llm_router = llm_router
        self.permission_engine = permission_engine

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "plan_project":
            return await self.plan_project(params.get("description"))
        elif action == "create_structure":
            return await self.create_structure(params.get("structure"))
        elif action == "write_file":
            return await self.write_file(params.get("path"), params.get("content"))
        elif action == "debug_project":
            return await self.debug_project(params.get("error_report"), params.get("files"))
        elif action == "generate_tests":
            return await self.generate_tests(params.get("project_path"))
        return {
            "status": "failed",
            "success": False,
            "error": f"Action {action} not supported by ArchitectAgent"
        }

    async def debug_project(self, error_report: str, files: List[str]) -> Dict[str, Any]:
        """Analyzes cross-file errors and suggests fixes."""
        logging.info(f"ArchitectAgent: Debugging project with error: {error_report}")
        file_contents = {}
        for f_path in (files or []):
            if os.path.exists(f_path):
                with open(f_path, 'r') as f:
                    file_contents[f_path] = f.read()
        
        prompt = (
            f"Error Report: {error_report}\n"
            f"Project Files: {list(file_contents.keys())}\n"
            f"Contents: {file_contents}\n"
            f"Analyze the error and provide the corrected code for the affected files.\n"
            f"Format as a JSON: {{\"fixes\": [{{\"path\": \"file_path\", \"content\": \"new_content\"}}]}}"
        )
        response = await self.llm_router.generate_response(prompt)
        return {
            "status": "success",
            "success": True,
            "analysis": response,
            "message": "Debug analysis complete.",
            "confidence": 0.85,
            "risk_level": "low"
        }

    async def generate_tests(self, project_path: str) -> Dict[str, Any]:
        """Generates unit tests for a given project path."""
        prompt = f"Generate unit tests for the project at {project_path}. Return a JSON list of test files and their content."
        response = await self.llm_router.generate_response(prompt)
        return {
            "status": "success",
            "success": True,
            "tests": response,
            "message": "Test generation complete.",
            "confidence": 0.80,
            "risk_level": "low"
        }

    async def plan_project(self, description: str) -> Dict[str, Any]:
        if not description:
            return {
                "status": "failed",
                "success": False,
                "error": "No project description provided.",
                "message": "Please provide a project description."
            }
        prompt = (
            f"Plan a multi-file project based on this description: {description}\n"
            f"Provide a JSON list of files and folders to create.\n"
            f"Example: {{\"structure\": [\"src/\", \"src/main.py\", \"requirements.txt\"]}}"
        )
        response = await self.llm_router.generate_response(prompt)
        return {
            "status": "success",
            "success": True,
            "plan": response,
            "content": response,
            "message": f"Project plan generated for: {description[:50]}",
            "confidence": 0.90,
            "risk_level": "low"
        }

    async def create_structure(self, structure: List[str]) -> Dict[str, Any]:
        if not structure:
            return {
                "status": "failed",
                "success": False,
                "error": "No structure provided.",
                "message": "Please provide a list of files/folders to create."
            }
        try:
            for item in structure:
                if item.endswith("/"):
                    os.makedirs(item, exist_ok=True)
                else:
                    dir_name = os.path.dirname(item)
                    if dir_name:
                        os.makedirs(dir_name, exist_ok=True)
                    with open(item, 'w') as f:
                        pass
            return {
                "status": "success",
                "success": True,
                "output": f"Created structure: {structure}",
                "message": f"Successfully created {len(structure)} files/folders.",
                "confidence": 0.99,
                "risk_level": "low"
            }
        except Exception as e:
            return {
                "status": "failed",
                "success": False,
                "error": str(e),
                "message": f"Failed to create structure: {str(e)}"
            }

    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        # Permission Check
        if self.permission_engine:
            if not self.permission_engine.check_permission("write_file", f"Write to {path}"):
                return {
                    "status": "failed",
                    "success": False,
                    "error": "Permission Denied by LUNA Security Engine.",
                    "message": "Permission denied."
                }

        try:
            dir_name = os.path.dirname(path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            return {
                "status": "success",
                "success": True,
                "output": f"Successfully wrote to {path}",
                "message": f"File written: {path}",
                "confidence": 0.99,
                "risk_level": "low"
            }
        except Exception as e:
            return {
                "status": "failed",
                "success": False,
                "error": str(e),
                "message": f"Failed to write file: {str(e)}"
            }
