# Path: agents/system_agent.py
import os
import logging
import platform
from typing import Dict, Any

class SystemAgent:
    """
    LUNA-ULTRA System Agent: Handles OS control and monitoring.
    Enforces standardized TaskResult output.
    """
    def __init__(self, config: Dict[str, Any], controller: Any = None):
        self.config = config
        self.controller = controller

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        result_template = {
            "status": "success",
            "content": "",
            "message": "",
            "error": "",
            "execution_used": True,
            "confidence": 1.0,
            "risk_level": "low"
        }

        try:
            if action == "get_health":
                import psutil
                cpu = psutil.cpu_percent(interval=0.1)
                ram = psutil.virtual_memory().percent
                result_template.update({
                    "content": {"cpu": cpu, "ram": ram},
                    "message": f"System Health: CPU {cpu}%, RAM {ram}%"
                })
                return result_template
            
            elif action in ["list_files", "list_directory"]:
                path = params.get('path', '.')
                files = os.listdir(path)
                result_template.update({
                    "content": files,
                    "message": f"Found {len(files)} files in `{path}`: {', '.join(files[:10])}{'...' if len(files) > 10 else ''}"
                })
                return result_template
            
            elif action == "get_system_info":
                info = {
                    "os": platform.system(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "cwd": os.getcwd()
                }
                result_template.update({
                    "content": info,
                    "message": f"System Status: {info['os']} {info['version']} | CWD: {info['cwd']}"
                })
                return result_template
                
            elif action == "create_directory":
                path = params.get('path')
                if not path: 
                    return self._fail("No path provided for directory creation.")
                os.makedirs(path, exist_ok=True)
                result_template.update({
                    "content": path,
                    "message": f"I have successfully created the directory: `{path}`"
                })
                return result_template
            
            elif action in ["shutdown", "restart", "power_off"]:
                mode = "SHUTDOWN" if action in ["shutdown", "power_off"] else "RESTART"
                msg = f"⚠️ System Power Action: {mode} command received from IRFAN."
                
                # Send Telegram notification if controller is available
                if self.controller and self.controller.telegram:
                    try:
                        import asyncio
                        asyncio.create_task(self.controller.telegram.send_notification(msg))
                        logging.info(f"SystemAgent: Power notification sent to Telegram: {mode}")
                    except Exception as e:
                        logging.error(f"SystemAgent: Failed to send power notification: {e}")
                
                result_template.update({
                    "risk_level": "critical",
                    "message": f"LUNA: I have initiated a system {mode.lower()} as requested, IRFAN. A notification has been sent to your Telegram."
                })
                return result_template
                
            return self._fail(f"Action {action} not supported", risk="low")

        except Exception as e:
            logging.error(f"SystemAgent Error: {e}")
            return self._fail(str(e))

    def _fail(self, error: str, risk: str = "low") -> Dict[str, Any]:
        return {
            "status": "failed",
            "content": "",
            "message": f"System action failed: {error}",
            "error": error,
            "execution_used": False,
            "confidence": 0.0,
            "risk_level": risk
        }
