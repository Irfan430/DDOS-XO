# Path: core/controller.py
import os
import yaml
import logging
import asyncio
import time
import re
from typing import Dict, Any

from llm.router import LLMRouter
from security.permission_engine import PermissionEngine
from memory.memory_manager import MemoryManager
from core.orchestrator import Orchestrator
from core.state_manager import StateManager
from core.cognitive_mode import CognitiveMode
from security.sandbox_executor import SandboxExecutor
from core.skill_manager import SkillManager
from core.module_loader import ModuleLoader

class LunaController:
    """
    The central brain of LUNA-ULTRA. Coordinates all modules and agents.
    Refined for Professional Engineering Mode: Improved synchronization and output enforcement.
    """
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.config = self.load_modular_configs()
        
        # Core Components
        self.llm_router = LLMRouter(self.config.get("llm", {}))
        from core.personality_engine import PersonalityEngine
        self.personality_engine = PersonalityEngine(self.config)
        self.permission_engine = PermissionEngine(self.config)
        self.sandbox_executor = SandboxExecutor(self.config.get("security", {}), self.permission_engine)
        self.memory_manager = MemoryManager(self.config.get("features", {}).get("memory", {}))
        self.state_manager = StateManager()
        self.cognitive_mode = CognitiveMode()
        
        # Advanced Features
        from agents.thought_loop import ThoughtLoop
        from core.system_health import SystemHealth
        from agents.skill_acquisition import SkillAcquisition
        from automation.browser_controller import BrowserController
        
        self.browser = BrowserController(self.config.get("automation", {}).get("browser", {}))
        self.thought_loop = ThoughtLoop(self)
        self.system_health = SystemHealth(self)
        self.skill_acquisition = SkillAcquisition(self)
        
        from core.execution_watchdog import ExecutionWatchdog
        from core.error_intelligence import ErrorIntelligence
        self.watchdog = ExecutionWatchdog(self)
        self.watchdog.start()
        self.error_intelligence = ErrorIntelligence(self)
        
        from core.github_manager import GitHubManager
        from core.validation_loop import ValidationLoop
        from core.task_queue import TaskQueue, CostMonitor, RiskScoringEngine
        from plugins.loader import PluginLoader
        
        self.github_manager = GitHubManager(self)
        self.validation_loop = ValidationLoop(self)
        self.task_queue = TaskQueue(self)
        self.cost_monitor = CostMonitor(self)
        self.risk_engine = RiskScoringEngine(self)
        self.plugin_loader = PluginLoader(self)
        self.plugin_loader.load_all()
        
        self.skill_manager = SkillManager()
        self.orchestrator = Orchestrator(self)
        
        from core.master_orchestrator import MasterOrchestrator
        self.master_orchestrator = MasterOrchestrator(self)
        self.resume_engine = self.master_orchestrator.resume_engine
        
        # Optional Modules
        self.telegram = self.init_optional_module("automation.telegram_controller", "TelegramController", self)
        self.vision_loop = self.init_optional_module("vision.vision_loop", "VisionLoop", self)
        self.security_sentinel = self.init_optional_module("security.security_sentinel", "SecuritySentinel", self)
        
        self.system_prompt = self.load_system_prompt()
        logging.info("LunaController: Modular initialization complete.")

    def load_modular_configs(self) -> Dict[str, Any]:
        combined_config = {}
        config_files = ["core.yaml", "llm.yaml", "security.yaml", "automation.yaml", "features.yaml"]
        for cf in config_files:
            path = os.path.join(self.config_dir, cf)
            if os.path.exists(path):
                with open(path, "r") as f:
                    combined_config.update(yaml.safe_load(f) or {})
        return combined_config

    def init_optional_module(self, module_path: str, class_name: str, *args):
        module_class = ModuleLoader.safe_import(module_path, class_name)
        if module_class:
            try:
                return module_class(*args)
            except Exception as e:
                logging.error(f"LunaController: Failed to initialize {class_name}: {e}")
        return None

    async def start_services(self):
        self.watchdog.start()
        if self.telegram and self.config.get("automation", {}).get("telegram", {}).get("enabled"):
            asyncio.create_task(self.telegram.run_bot())
        if self.vision_loop and self.config.get("features", {}).get("vision", {}).get("enabled"):
            asyncio.create_task(self.vision_loop.start())
        if self.security_sentinel and self.config.get("security", {}).get("sentinel_enabled"):
            asyncio.create_task(self.security_sentinel.start())

    async def shutdown_services(self):
        if self.telegram: await self.telegram.stop_bot()
        if self.vision_loop and hasattr(self.vision_loop, 'running') and self.vision_loop.running:
            await self.vision_loop.stop()
        if self.security_sentinel and hasattr(self.security_sentinel, 'running') and self.security_sentinel.running:
            await self.security_sentinel.stop()

    def load_system_prompt(self) -> str:
        path = "config/system_prompt.txt"
        if os.path.exists(path):
            with open(path, "r") as f: return f.read()
        return "You are LUNA-ULTRA, a professional AI assistant."

    async def process_input(self, user_input: str) -> str:
        """Central entry point for user input with refined TaskResult processing."""
        if user_input.lower() == "resume" and self.master_orchestrator.state_manager.has_active_execution():
            logging.info("LunaController: Resuming previous task...")
            resume_result = await self.resume_engine.resume_execution()
            return f"Resumed: {resume_result.get('message', 'Task in progress...')}"

        task_id = f"task_{int(time.time())}"
        self.watchdog.register_task(task_id, user_input)
        
        response_data = await self.orchestrator.handle_task(user_input)
        self.watchdog.unregister_task(task_id)
        
        is_success = False
        final_response = ""

        if response_data.get("type") == "chat":
            final_response = response_data.get("response")
            is_success = True
            if "TOKEN_LIMIT_ERROR" in final_response:
                await self.resume_engine.handle_token_limit_error(final_response)
                return "I've hit a token limit, but I've saved my progress. Type 'resume' to continue."
        else:
            # Handle standardized tool execution results
            if "output" in response_data:
                final_response = response_data["output"]
                is_success = response_data.get("success", True)
            else:
                results = response_data.get("results", [])
                if results:
                    last_res = results[-1].get("result", {})
                    is_success = last_res.get("status") == "success"
                    
                    if not is_success:
                        error = last_res.get("error", "Unknown error")
                        analysis = await self.error_intelligence.analyze_failure(user_input, error, results)
                        final_response = f"I encountered an issue: {error}\n\n### Root Cause Analysis\n{analysis['analysis']}"
                        
                        if hasattr(self, 'gui') and self.gui and self.gui.voice_engine.enabled:
                            self.gui.voice_engine.announce_task_status(user_input, "failed", analysis['root_cause'])
                    else:
                        final_response = last_res.get("message", "Task completed successfully.")
                        # If there's content (like code), append it
                        if last_res.get("content") and isinstance(last_res["content"], str) and "```" in last_res["content"]:
                            final_response += f"\n\n**Result Content:**\n{last_res['content']}"
                else:
                    final_response = "Action performed successfully."
                    is_success = True

        # Telegram Notification
        if is_success and self.telegram and self.config.get("automation", {}).get("telegram", {}).get("enabled", True):
            if not any(word in user_input.lower() for word in ["shutdown", "restart"]):
                try:
                    clean_res = re.sub(r'```.*?```', '[Code Block]', final_response, flags=re.DOTALL)
                    notify_msg = f"✅ Task Successful!\n\nTask: {user_input[:100]}...\n\nResult: {clean_res[:300]}..."
                    asyncio.create_task(self.telegram.send_notification(notify_msg))
                except Exception as e:
                    logging.error(f"LunaController: Telegram notify error: {e}")
        
        self.memory_manager.store_interaction(user_input, final_response)
        return final_response

    def update_config(self, new_config: Dict[str, Any]):
        logging.info(f"LunaController: Updating configuration: {new_config}")
        for section, values in new_config.items():
            if section not in self.config: self.config[section] = {}
            self.config[section].update(values)
            
        if "llm" in new_config:
            self.llm_router.mode = self.config["llm"].get("mode", "api")
            self.llm_router.default_provider = self.config["llm"].get("default_provider", "deepseek")
            
        if "permissions" in new_config or "security" in new_config:
            from security.permission_engine import PermissionLevel
            level_str = self.config.get("permissions", {}).get("level") or self.config.get("security", {}).get("level", "SAFE")
            self.permission_engine.current_level = PermissionLevel[level_str]

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": "IDLE",
            "mode": "COGNITIVE",
            "permission": self.config.get("permissions", {}).get("level") or self.config.get("security", {}).get("level", "STANDARD"),
            "provider": self.config.get("llm", {}).get("default_provider", "deepseek")
        }
