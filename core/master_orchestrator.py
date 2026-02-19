# Path: core/master_orchestrator.py
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.plan_engine import PlanEngine
from core.execution_state import ExecutionStateManager
from core.validation_engine import ValidationEngine
from core.resume_engine import ResumeEngine
from core.github_safe_flow import GitHubSafeFlow
from tools.registry import ToolRegistry


class MasterOrchestrator:
    """
    Master Orchestrator for Agent Mode.
    Coordinates structured planning, execution, validation, and resumption.
    Enforces standardized TaskResult output and GUI synchronization.
    """
    
    def __init__(self, controller):
        self.controller = controller
        self.plan_engine = PlanEngine(controller)
        self.state_manager = ExecutionStateManager()
        self.validation_engine = ValidationEngine(controller)
        self.resume_engine = ResumeEngine(controller, self.state_manager)
        self.github_flow = GitHubSafeFlow(controller)
        
        self.current_mode = "chat"  # chat, automation, agent
        self.agent_mode_active = False
        
        logging.info("MasterOrchestrator: Initialized for Agent Mode.")
    
    def set_mode(self, mode: str):
        """
        Set the current operating mode.
        """
        if mode not in ["chat", "automation", "agent"]:
            logging.warning(f"MasterOrchestrator: Invalid mode '{mode}'. Defaulting to 'chat'.")
            mode = "chat"
        
        self.current_mode = mode
        self.agent_mode_active = (mode == "agent")
        logging.info(f"MasterOrchestrator: Mode set to '{mode}'.")
    
    async def handle_agent_task(self, goal: str, user_approved: bool = False) -> Dict[str, Any]:
        """
        Main entry point for Agent Mode tasks with standardized output.
        """
        if not self.agent_mode_active:
            return {
                "status": "failed",
                "success": False,
                "error": "Agent Mode is not active.",
                "message": "Please switch to Agent Mode first."
            }
        
        # Check if we're resuming
        if self.state_manager.has_active_execution():
            logging.info("MasterOrchestrator: Resuming previous execution...")
            return await self.resume_engine.resume_execution()
        
        # Step 1: Generate Plan
        if not user_approved:
            logging.info(f"MasterOrchestrator: Generating plan for goal: {goal}")
            plan_result = await self.plan_engine.generate_plan(goal)
            
            if not plan_result.get("success"):
                return {
                    "status": "failed",
                    "success": False,
                    "error": f"Plan generation failed: {plan_result.get('error')}",
                    "message": "I couldn't form a valid plan for this goal."
                }
            
            return {
                "status": "success",
                "success": True,
                "requires_approval": True,
                "plan": plan_result.get("plan"),
                "message": "Plan generated. Please review and approve before execution."
            }
        
        # Step 2: Initialize & Execute
        plan = self.state_manager.get_state().get("plan") if self.state_manager.get_state() else None
        if not plan:
            # This case shouldn't happen if UI flow is correct, but added for safety
            plan_result = await self.plan_engine.generate_plan(goal)
            plan = plan_result.get("plan")
            
        self.state_manager.initialize_execution(goal, plan)
        
        # Step 3: Execute Plan
        execution_result = await self._execute_plan_with_validation(plan)
        
        # Step 4: Final Validation
        if execution_result.get("status") == "success":
            validation_result = await self.validation_engine.validate_project()
            execution_result["validation"] = validation_result
            
            if not validation_result.get("success"):
                logging.warning("MasterOrchestrator: Final validation failed. Attempting patch...")
                patch_result = await self._patch_validation_errors(validation_result)
                if patch_result.get("success"):
                    execution_result["status"] = "success"
                    execution_result["message"] += "\n\n✅ Final validation passed after automated patching."
                else:
                    execution_result["status"] = "partial"
                    execution_result["message"] += "\n\n⚠️ Final validation failed. Manual review required."
        
        # Step 5: Mark complete
        self.state_manager.mark_execution_complete(execution_result.get("status") == "success")
        
        # Step 6: GitHub Prep
        if execution_result.get("status") == "success":
            git_prep = self.github_flow.prepare_for_push(execution_result)
            execution_result["git_preparation"] = git_prep
        
        # Ensure backward compatibility for GUI signals while using new status
        execution_result["success"] = execution_result.get("status") == "success"
        return execution_result
    
    async def _execute_plan_with_validation(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute plan steps with validation and standardized output.
        """
        steps = plan.get("steps", [])
        results = []
        
        for idx, step in enumerate(steps):
            # Update state
            self.state_manager.update_current_step(idx)
            
            # GUI Update
            if hasattr(self.controller, 'gui') and self.controller.gui:
                self.controller.gui.activity_panel.update_activity({
                    "agent": step.get("agent", "master"),
                    "task": f"Step {idx+1}: {step.get('description')}",
                    "status": "executing",
                    "risk_level": plan.get("risk_level", "LOW")
                })

            # Execute step
            step_result = await self._execute_step_with_retry(step, max_retries=2)
            results.append(step_result)
            
            # Update state & GUI
            success = step_result.get("status") == "success"
            self.state_manager.mark_step_complete(idx, success, step_result)
            
            if hasattr(self.controller, 'gui') and self.controller.gui:
                self.controller.gui.activity_panel.update_activity({
                    "agent": step.get("agent", "master"),
                    "task": step_result.get("message", "Step completed"),
                    "status": step_result.get("status", "failed"),
                    "confidence": step_result.get("confidence", 0.0)
                })

            if not success:
                return {
                    "status": "failed",
                    "error": step_result.get("error"),
                    "message": f"Execution halted at step {idx+1}: {step_result.get('message')}",
                    "completed_steps": idx,
                    "total_steps": len(steps),
                    "results": results
                }
        
        return {
            "status": "success",
            "message": "All plan steps executed and verified successfully.",
            "completed_steps": len(steps),
            "total_steps": len(steps),
            "results": results
        }
    
    async def _execute_step_with_retry(self, step: Dict[str, Any], max_retries: int = 2) -> Dict[str, Any]:
        """
        Execute a single step with standardized retry logic.
        """
        last_result = None
        for attempt in range(max_retries + 1):
            try:
                agent_name = step.get("agent")
                agent = self.controller.orchestrator.agents.get(agent_name)
                
                if agent:
                    last_result = await agent.execute(step.get("action"), step.get("params", {}))
                else:
                    # Fallback to ToolRegistry
                    tool_res = ToolRegistry.execute_tool(step.get("action"), step.get("params", {}))
                    last_result = {
                        "status": "success" if tool_res.get("success") else "failed",
                        "content": tool_res.get("output", ""),
                        "message": tool_res.get("message", "Tool executed"),
                        "error": tool_res.get("error", ""),
                        "execution_used": True,
                        "confidence": 1.0,
                        "risk_level": "low"
                    }
                
                if last_result.get("status") == "success":
                    # Verify compilation if it was a code change
                    if agent_name == "code":
                        comp = await self.validation_engine.compile_project()
                        if not comp.get("success"):
                            last_result["status"] = "failed"
                            last_result["error"] = f"Compilation failed: {comp.get('errors')[0]}"
                            last_result["message"] = "Code was written but contains syntax errors."
                        else:
                            return last_result
                    else:
                        return last_result
                
                # If we're here, it failed. Try to patch if it's the code agent.
                if attempt < max_retries and agent_name == "code":
                    logging.info(f"MasterOrchestrator: Step failed. Attempting patch {attempt+1}/{max_retries}")
                    await self._attempt_patch({"error": last_result.get("error", "Unknown error")})
                    
            except Exception as e:
                logging.error(f"MasterOrchestrator: Exception in step: {e}")
                last_result = {
                    "status": "failed",
                    "error": str(e),
                    "message": "An unexpected exception occurred during step execution."
                }
        
        return last_result

    async def _attempt_patch(self, error_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to automatically patch an error.
        """
        error_msg = error_result.get("error", "")
        patch_prompt = f"The following error occurred: {error_msg}\nPlease provide a fix. Return only code fix instructions."
        try:
            patch_response = await self.controller.llm_router.generate_response(patch_prompt)
            return {"success": True, "patch": patch_response}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _patch_validation_errors(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Patch multiple validation errors.
        """
        errors = validation_result.get("errors", [])
        for error in errors:
            await self._attempt_patch({"error": error})
        return await self.validation_engine.validate_project()

    def get_current_state(self) -> Dict[str, Any]:
        return self.state_manager.get_state()
    
    def clear_state(self):
        self.state_manager.clear_state()
    
    async def push_to_github(self, branch_name: str) -> Dict[str, Any]:
        return self.github_flow.push_branch(branch_name)
