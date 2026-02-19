# Path: agents/code_agent.py
import subprocess
import os
import tempfile
import re
import logging
from typing import Dict, Any, Optional, List
from llm.router import LLMRouter

class CodeAgent:
    """
    LUNA-ULTRA Code Agent: Writes, executes, and self-heals code with a robust feedback loop.
    Enforces standardized TaskResult output.
    """
    def __init__(self, config: Dict[str, Any], llm_router: LLMRouter):
        self.config = config
        self.llm_router = llm_router
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('execution_timeout', 30)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action in ["write_and_run", "write_function", "coding", "create_script"]:
            task = params.get('task') or params.get('function_name') or params.get('content') or "Write code"
            filename = params.get('filename') or params.get('path')
            result = await self.self_healing_loop(task, params.get('initial_code', ""))
            
            # If a filename was provided, save the code to that file
            if filename and result.get("status") == "success" and result.get("content"):
                try:
                    with open(filename, "w") as f:
                        f.write(result["content"])
                    result["message"] += f"\n\n✅ Code has been saved to `{filename}`."
                except Exception as e:
                    result["message"] += f"\n\n⚠️ Failed to save code to `{filename}`: {e}"
            
            return result
        return {
            "status": "failed",
            "error": f"Action {action} not supported",
            "message": "Operation failed due to unsupported action.",
            "execution_used": False,
            "confidence": 0.0,
            "risk_level": "low"
        }

    def extract_code(self, text: str) -> str:
        """
        Extracts python code from markdown blocks or returns the text if no blocks found.
        Improved to handle multiple blocks and nested formatting.
        """
        # Try to find python blocks first
        blocks = re.findall(r"```python\n(.*?)\n```", text, re.DOTALL)
        if blocks:
            return "\n\n".join(blocks).strip()
        
        # Fallback to generic code blocks
        blocks = re.findall(r"```\n(.*?)\n```", text, re.DOTALL)
        if blocks:
            return "\n\n".join(blocks).strip()
            
        return text.strip()

    async def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        if language != "python":
            return {"success": False, "error": f"Language {language} not supported."}

        code = self.extract_code(code)
        if not code:
            return {"success": False, "error": "No valid code found to execute."}

        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            tmp.write(code.encode('utf-8'))
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["python3", tmp_path], 
                capture_output=True, 
                text=True, 
                timeout=self.timeout
            )
            return {
                "success": result.returncode == 0, 
                "stdout": result.stdout, 
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Code execution timed out after {self.timeout}s."}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def self_healing_loop(self, task: str, initial_code: str) -> Dict[str, Any]:
        """
        The self-healing loop: Run -> Error -> LLM Fix -> Run again.
        Returns standardized TaskResult.
        """
        current_code = initial_code
        history = []

        for attempt in range(1, self.max_retries + 1):
            logging.info(f"LUNA Code Agent: Execution attempt {attempt}/{self.max_retries}")
            
            if not current_code:
                gen_prompt = (
                    f"Task: {task}\n"
                    f"Write a complete, standalone Python script to achieve this. "
                    f"Include a main block to demonstrate the code. "
                    f"DO NOT use external libraries or complex CLI arguments unless requested. "
                    f"Wrap the code in a ```python block."
                )
                current_code = await self.llm_router.generate_response(gen_prompt)
                current_code = self.extract_code(current_code)

            result = await self.execute_code(current_code)
            
            if result["success"]:
                message = f"I have written and verified the code for you, IRFAN.\n\n**Execution Output:**\n```\n{result['stdout']}\n```"
                return {
                    "status": "success",
                    "content": current_code,
                    "message": message,
                    "execution_used": True,
                    "confidence": 0.98,
                    "risk_level": "medium",
                    "attempt": attempt
                }
            
            error_msg = result.get("stderr") or result.get("error")
            logging.warning(f"LUNA Code Agent: Attempt {attempt} failed: {error_msg}")
            history.append({"attempt": attempt, "error": error_msg})
            
            if attempt < self.max_retries:
                fix_prompt = (
                    f"Task: {task}\n"
                    f"Previous Code:\n```python\n{current_code}\n```\n"
                    f"Error encountered:\n{error_msg}\n"
                    f"The code failed to run. Please fix it. Ensure it is a standalone script that doesn't require manual input. "
                    f"Wrap in ```python code block."
                )
                fix_response = await self.llm_router.generate_response(fix_prompt)
                current_code = self.extract_code(fix_response)
            else:
                break
                
        # Even if it fails, return the code so the user can see it
        fail_message = (
            f"I tried to write the code but encountered issues during execution, IRFAN.\n\n"
            f"**Error:**\n{history[-1]['error']}"
        )
        return {
            "status": "failed",
            "content": current_code,
            "error": history[-1]['error'],
            "message": fail_message,
            "execution_used": True,
            "confidence": 0.4,
            "risk_level": "medium",
            "history": history
        }
