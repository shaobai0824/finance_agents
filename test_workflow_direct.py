"""直接測試 Workflow"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

# 初始化 workflow（模擬 API 的啟動流程）
from src.main.python.workflow.finance_workflow_llm import FinanceWorkflowLLM

async def test_workflow():
    print("Initializing workflow...")
    try:
        workflow = FinanceWorkflowLLM()
        print("Workflow initialized")

        print("\nTesting simple query...")
        result = await asyncio.wait_for(
            workflow.run(
                user_query="測試",
                user_profile={"risk_tolerance": "moderate", "income_level": "middle"}
            ),
            timeout=30.0
        )

        print(f"Success!")
        print(f"Response: {result['final_response'][:100]}...")
        print(f"Confidence: {result['confidence_score']}")
        print(f"Agents: {result.get('agents_used', [])}")

    except asyncio.TimeoutError:
        print("ERROR: Workflow timed out after 30 seconds")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow())