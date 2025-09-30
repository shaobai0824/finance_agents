"""測試 LangGraph workflow 編譯"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

async def test_workflow():
    print("1. Importing FinanceWorkflowLLM...")
    from src.main.python.workflow.finance_workflow_llm import FinanceWorkflowLLM

    print("2. Creating workflow instance (this may take a few seconds)...")
    workflow = FinanceWorkflowLLM()
    print("[OK] Workflow created!")

    print("\n3. Testing workflow execution with timeout...")
    try:
        result = await asyncio.wait_for(
            workflow.run(
                user_query="簡單測試",
                user_profile={"risk_tolerance": "moderate", "income_level": "middle"}
            ),
            timeout=15.0
        )
        print(f"[OK] Workflow executed successfully!")
        print(f"Response preview: {result['final_response'][:50]}...")
    except asyncio.TimeoutError:
        print("[TIMEOUT] Workflow execution timed out after 15s")
        print("This indicates the workflow is hanging during execution")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow())