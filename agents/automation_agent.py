# Path: agents/automation_agent.py
from typing import Dict, Any
import logging
from automation.shell_executor import ShellExecutor
from automation.mouse_controller import MouseController
from automation.keyboard_controller import KeyboardController
from automation.browser_controller import BrowserController

class AutomationAgent:
    """
    LUNA-ULTRA Automation Agent: Handles task automation with permission gating.
    Enforces standardized TaskResult output.
    """
    def __init__(self, config: Dict[str, Any], permission_engine: Any):
        self.config = config
        self.permission_engine = permission_engine
        self.shell = ShellExecutor(config.get('automation', {}), permission_engine)
        self.mouse = MouseController(config.get('automation', {}))
        self.keyboard = KeyboardController(config.get('automation', {}))
        self.browser = BrowserController(config.get('automation', {}))

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes automation actions with explicit permission checks and standardized output.
        """
        try:
            if action == "shell_exec":
                command = params.get('command')
                if not command:
                    return self._fail("No command provided for shell execution.")
                
                # ShellExecutor now returns a dict, we need to adapt it to TaskResult
                res = await self.shell.execute(command)
                
                status = "success" if res.get("success") else "failed"
                message = f"Command executed: `{command}`"
                if not res.get("success"):
                    message = f"Command failed: `{command}`"
                
                return {
                    "status": status,
                    "content": res.get("stdout", ""),
                    "message": message,
                    "error": res.get("stderr", "") or res.get("error", ""),
                    "execution_used": True,
                    "confidence": 0.95 if status == "success" else 0.0,
                    "risk_level": "medium"
                }
                
            elif action == "mouse_click":
                x, y = params.get('x'), params.get('y')
                if x is None or y is None:
                    return self._fail("Invalid coordinates for mouse click.")
                    
                if self.permission_engine.check_permission("mouse_click", f"Click at {x}, {y}"):
                    self.mouse.click(x, y)
                    return {
                        "status": "success",
                        "content": f"Clicked at {x}, {y}",
                        "message": f"Successfully clicked at coordinates ({x}, {y}).",
                        "execution_used": True,
                        "confidence": 1.0,
                        "risk_level": "low"
                    }
                return self._fail("Permission Denied: Mouse control blocked by security engine.", risk="medium")
                
            elif action == "keyboard_type":
                text = params.get('text')
                if text is None:
                    return self._fail("No text provided for keyboard typing.")
                    
                if self.permission_engine.check_permission("keyboard_type", f"Typing: {text[:20]}..."):
                    self.keyboard.type(text)
                    return {
                        "status": "success",
                        "content": text,
                        "message": "Text successfully typed into active window.",
                        "execution_used": True,
                        "confidence": 1.0,
                        "risk_level": "low"
                    }
                return self._fail("Permission Denied: Keyboard input blocked by security engine.", risk="medium")
                
            elif action == "browser_open":
                url = params.get('url')
                if not url:
                    return self._fail("No URL provided for browser.")
                    
                if self.permission_engine.check_permission("read_file", f"Open URL: {url}"):
                    self.browser.open_url(url)
                    return {
                        "status": "success",
                        "content": url,
                        "message": f"Browser opened and navigated to: {url}",
                        "execution_used": True,
                        "confidence": 1.0,
                        "risk_level": "low"
                    }
                return self._fail("Permission Denied: Web access blocked by security engine.", risk="medium")
                
            return self._fail(f"Action {action} not supported.")

        except Exception as e:
            logging.error(f"AutomationAgent Error: {e}")
            return self._fail(str(e))

    def _fail(self, error: str, risk: str = "low") -> Dict[str, Any]:
        return {
            "status": "failed",
            "content": "",
            "message": f"Automation failed: {error}",
            "error": error,
            "execution_used": False,
            "confidence": 0.0,
            "risk_level": risk
        }
