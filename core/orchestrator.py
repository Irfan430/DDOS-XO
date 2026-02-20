# Path: core/orchestrator.py
import logging
import json
import re
from typing import Dict, Any, List

class Orchestrator:
    """
    LUNA-ULTRA Orchestrator: Multi-agent coordination with deep intent analysis.
    Enforces standardized TaskResult processing and GUI synchronization.
    """
    def __init__(self, controller):
        self.controller = controller
        self.agents = {}
        self.initialize_agents()

    def initialize_agents(self):
        from agents.code_agent import CodeAgent
        from agents.automation_agent import AutomationAgent
        from agents.screen_agent import ScreenAgent
        from agents.system_agent import SystemAgent
        from agents.dynamic_agent import DynamicAgent
        from agents.architect_agent import ArchitectAgent

        self.agents["code"] = CodeAgent(self.controller.config, self.controller.llm_router)
        self.agents["automation"] = AutomationAgent(self.controller.config, self.controller.permission_engine)
        self.agents["screen"] = ScreenAgent(self.controller.config, self.controller.permission_engine)
        self.agents["system"] = SystemAgent(self.controller.config, self.controller)
        self.agents["dynamic"] = DynamicAgent(self.controller.config, self.controller.llm_router, self.controller.permission_engine)
        self.agents["architect"] = ArchitectAgent(self.controller.config, self.controller.llm_router, self.controller.permission_engine)
        
        logging.info(f"Orchestrator: Initialized {len(self.agents)} agents.")

    async def handle_task(self, user_input: str) -> Dict[str, Any]:
        logging.info(f"Orchestrator: Analyzing task: {user_input}")
        
        # 0. Get Memory Context
        memory_context = self.controller.memory_manager.get_context(user_input)

        # Quick check for simple math
        math_pattern = r'(what is|calculate|compute|solve|how much).*(\d+.*[\+\-\*\/\^].*\d+|square root|factorial|power|multiply|divide|add|subtract)'
        if re.search(math_pattern, user_input.lower()):
            logging.info("Orchestrator: Detected simple math question, treating as conversation")
            chat_prompt = (
                f"{self.controller.system_prompt}\n\n"
                f"Context:\n{memory_context}\n\n"
                f"User: {user_input}\n\n"
                f"Provide a clear, direct answer to this mathematical question."
            )
            chat_response = await self.controller.llm_router.generate_response(chat_prompt)
            return {"response": chat_response, "type": "chat", "thought": "Simple mathematical calculation"}

        # 1. Intent Classification
        intent_prompt = (
            f"Context:\n{memory_context}\n\n"
            f"Classify the user intent for: \"{user_input}\"\n\n"
            f"Categories:\n"
            f"- GREETING: Simple greetings\n"
            f"- CONVERSATION: General chat, factual queries\n"
            f"- CODING: Writing, debugging, or executing code\n"
            f"- SYSTEM_ACTION: File operations, system commands\n"
            f"- WEB_ACTION: Web browsing, scraping\n"
            f"- AUTOMATION: Browser automation, keyboard/mouse control\n"
            f"- ANALYSIS: Complex data analysis\n\n"
            f"Respond in format: INTENT: <CATEGORY> | THOUGHT: <REASONING>"
        )
        reasoning_response = await self.controller.llm_router.generate_response(intent_prompt)
        
        intent = "CONVERSATION"
        thought = "Direct response."
        if "INTENT:" in reasoning_response:
            parts = reasoning_response.split("|")
            intent = parts[0].replace("INTENT:", "").strip().upper()
            if len(parts) > 1:
                thought = parts[1].replace("THOUGHT:", "").strip()

        # Update GUI/Telegram with Thought
        if hasattr(self.controller, 'gui') and self.controller.gui:
            self.controller.gui.update_activity(f"🧠 THOUGHT: {thought}")

        # 2. Routing Logic
        # FIXED: BUG-009 - Handle GREETING intent explicitly with a warm, direct response
        if intent == "GREETING":
            greeting_prompt = (
                f"{self.controller.system_prompt}\n\n"
                f"The user just greeted you. Respond warmly and briefly as LUNA.\n"
                f"User: {user_input}"
            )
            greeting_response = await self.controller.llm_router.generate_response(greeting_prompt)
            return {"response": greeting_response, "type": "greeting", "thought": thought}

        action_intents = ["CODING", "SYSTEM_ACTION", "WEB_ACTION", "AUTOMATION", "ANALYSIS"]
        if intent not in action_intents:
            chat_prompt = (
                f"{self.controller.system_prompt}\n\n"
                f"Context:\n{memory_context}\n\n"
                f"User: {user_input}"
            )
            chat_response = await self.controller.llm_router.generate_response(chat_prompt)
            return {"response": chat_response, "type": "chat", "thought": thought}

        # 3. Tool Planning
        plan_prompt = f"""
User Task: {user_input}
Thought: {thought}
Available Agents: {list(self.agents.keys())}.
Generate a JSON list of steps: [{{"agent": "name", "action": "method", "params": {{}} }}]
Return ONLY the JSON list.
"""
        plan_str = await self.controller.llm_router.generate_response(plan_prompt)
        
        plan = []
        try:
            json_match = re.search(r"\[.*\]", plan_str, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(0))
        except Exception as e:
            logging.error(f"Orchestrator: Plan error: {e}")

        # 4. Execution
        if plan:
            if hasattr(self.controller, 'master_orchestrator'):
                self.controller.master_orchestrator.state_manager.initialize_execution(user_input, {"steps": plan})

            # Use ThoughtLoop for complex multi-step tasks
            if len(plan) > 1 or intent in ["CODING", "AUTOMATION"]:
                if hasattr(self.controller, 'gui') and self.controller.gui:
                    self.controller.gui.update_activity("🧠 LUNA: Entering Thought Loop for self-reflection...")
                loop_result = await self.controller.thought_loop.run_with_reflection(user_input, plan)
                
                if hasattr(self.controller, 'master_orchestrator'):
                    self.controller.master_orchestrator.state_manager.mark_execution_complete(loop_result.get("success", False))
                
                return {
                    "plan": plan, 
                    "results": loop_result.get("results"), 
                    "type": "tool_action", 
                    "thought": thought, 
                    "success": loop_result.get("success"),
                    "output": loop_result.get("output")
                }
            
            results = []
            for idx, step in enumerate(plan):
                agent_name = step.get("agent")
                agent = self.agents.get(agent_name)
                if agent:
                    if hasattr(self.controller, 'master_orchestrator'):
                        self.controller.master_orchestrator.state_manager.update_current_step(idx)
                    
                    # GUI Transparency Update
                    if hasattr(self.controller, 'gui') and self.controller.gui:
                        self.controller.gui.activity_panel.update_activity({
                            "agent": agent_name,
                            "task": f"Executing: {step.get('action')}",
                            "confidence": 0.90,
                            "risk_level": "LOW",
                            "status": "executing"
                        })

                    res = await agent.execute(step.get("action"), step.get("params", {}))
                    results.append({"step": step, "result": res})
                    
                    # Update GUI with result
                    if hasattr(self.controller, 'gui') and self.controller.gui:
                        status = res.get("status", "failed")
                        self.controller.gui.activity_panel.update_activity({
                            "agent": agent_name,
                            "task": res.get("message", f"{step.get('action')} completed"),
                            "confidence": res.get("confidence", 0.0),
                            "risk_level": res.get("risk_level", "LOW"),
                            "status": status
                        })
                    
                    if hasattr(self.controller, 'master_orchestrator'):
                        self.controller.master_orchestrator.state_manager.mark_step_complete(idx, res.get("status") == "success", res)
                    
                    if res.get("status") != "success": break
            
            if hasattr(self.controller, 'master_orchestrator'):
                success = all(r.get("result", {}).get("status") == "success" for r in results)
                self.controller.master_orchestrator.state_manager.mark_execution_complete(success)

            return {"plan": plan, "results": results, "type": "tool_action", "thought": thought}
        
        return {"response": "I understood your request but couldn't form a plan.", "type": "chat"}
