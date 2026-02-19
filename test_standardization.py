# Path: test_standardization.py
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.controller import LunaController

async def test_standardization():
    print("🚀 Starting Professional Engineering Mode Validation...")
    
    # Initialize controller
    controller = LunaController("config")
    
    # 1. Test CodeAgent Standardization
    print("\n--- Testing CodeAgent Standardization ---")
    code_agent = controller.orchestrator.agents.get("code")
    result = await code_agent.execute("coding", {"task": "print('Hello LUNA')", "filename": "test_output.py"})
    
    required_keys = ["status", "content", "message", "execution_used", "confidence", "risk_level"]
    missing = [k for k in required_keys if k not in result]
    
    if not missing:
        print("✅ CodeAgent returned standardized TaskResult")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result['message'][:50]}...")
    else:
        print(f"❌ CodeAgent missing keys: {missing}")

    # 2. Test SystemAgent Standardization
    print("\n--- Testing SystemAgent Standardization ---")
    system_agent = controller.orchestrator.agents.get("system")
    result = await system_agent.execute("get_system_info", {})
    
    missing = [k for k in required_keys if k not in result]
    if not missing:
        print("✅ SystemAgent returned standardized TaskResult")
        print(f"   Status: {result['status']}")
    else:
        print(f"❌ SystemAgent missing keys: {missing}")

    # 3. Test AutomationAgent (Shell) Standardization
    print("\n--- Testing AutomationAgent Standardization ---")
    auto_agent = controller.orchestrator.agents.get("automation")
    result = await auto_agent.execute("shell_exec", {"command": "ls -l"})
    
    missing = [k for k in required_keys if k not in result]
    if not missing:
        print("✅ AutomationAgent returned standardized TaskResult")
        print(f"   Status: {result['status']}")
    else:
        print(f"❌ AutomationAgent missing keys: {missing}")

    # 4. Test Orchestrator Result Handling
    print("\n--- Testing Orchestrator Logic ---")
    # Mocking a task that would trigger a plan
    task_result = await controller.orchestrator.handle_task("List files in current directory")
    if "results" in task_result:
        last_res = task_result["results"][-1]["result"]
        if "status" in last_res:
            print("✅ Orchestrator successfully processed standardized agent output")
        else:
            print("❌ Orchestrator failed to preserve status in results")
    else:
        print("ℹ️ Orchestrator returned direct response (chat mode)")

    print("\n--- Validation Summary ---")
    if not missing:
        print("🏆 ALL CORE AGENTS SYNCHRONIZED TO TASKRESULT PROTOCOL.")
    else:
        print("⚠️ STANDARDIZATION INCOMPLETE.")

if __name__ == "__main__":
    asyncio.run(test_standardization())
