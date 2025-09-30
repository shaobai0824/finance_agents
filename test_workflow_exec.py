"""測試 Workflow 執行 - 帶詳細日誌"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_execution():
    print("=== Workflow Execution Test ===\n")

    print("1. Creating workflow...")
    from src.main.python.workflow.finance_workflow_llm import FinanceWorkflowLLM
    workflow = FinanceWorkflowLLM()
    print("[OK] Workflow created\n")

    print("2. Starting execution with 15s timeout...")
    print("Query: '測試查詢'")
    print("Profile: moderate risk, middle income\n")

    try:
        result = await asyncio.wait_for(
            workflow.run(
                user_query="測試查詢",
                user_profile={"risk_tolerance": "moderate", "income_level": "middle"}
            ),
            timeout=15.0
        )
        print("\n[SUCCESS] Execution completed!")
        print(f"Response: {result['final_response'][:100]}...")
        print(f"Confidence: {result['confidence_score']}")
        print(f"Agents used: {result.get('agents_used', [])}")

    except asyncio.TimeoutError:
        print("\n[TIMEOUT] Execution timed out after 15s")
        print("\nCheck logs above to see where it got stuck:")
        print("- If no 'Starting query routing' -> stuck before routing")
        print("- If 'Starting query routing' but no 'routing completed' -> stuck in manager agent")
        print("- If 'routing completed' but no expert logs -> stuck in expert processing")

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_execution())