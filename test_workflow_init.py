"""測試 Workflow 初始化的每個步驟"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

print("Step 1: Importing modules...")
from src.main.python.workflow.finance_workflow_llm import FinanceWorkflowLLM
print("[OK] Import successful")

print("\nStep 2: Creating workflow instance...")
print("This will initialize:")
print("  - StateManager")
print("  - ChromaDB vector store")
print("  - KnowledgeRetriever")
print("  - PersonalFinanceDB")
print("  - LLM agents (manager, planner, analyst, legal)")
print("  - LangGraph workflow compilation")
print("\nWaiting...")

try:
    workflow = FinanceWorkflowLLM()
    print("\n[SUCCESS] Workflow instance created!")
except Exception as e:
    print(f"\n[FAILED] Workflow creation failed: {e}")
    import traceback
    traceback.print_exc()