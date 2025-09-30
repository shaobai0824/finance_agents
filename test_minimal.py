"""最小化測試 - 找出卡住的組件"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

async def test_components():
    print("1. Testing ChromaDB...")
    try:
        from src.main.python.rag.chroma_vector_store import ChromaVectorStore
        store = ChromaVectorStore(collection_name="finance_knowledge_optimal")
        print("[OK] ChromaDB OK")
    except Exception as e:
        print(f"[FAIL] ChromaDB FAILED: {e}")
        return

    print("\n2. Testing KnowledgeRetriever...")
    try:
        from src.main.python.rag.knowledge_retriever import KnowledgeRetriever
        retriever = KnowledgeRetriever(store)
        print("[OK] KnowledgeRetriever OK")
    except Exception as e:
        print(f"[FAIL] KnowledgeRetriever FAILED: {e}")
        return

    print("\n3. Testing PersonalFinanceDB...")
    try:
        from src.main.python.database.personal_finance_db import PersonalFinanceDB
        db = PersonalFinanceDB()
        print("[OK] PersonalFinanceDB OK")
    except Exception as e:
        print(f"[FAIL] PersonalFinanceDB FAILED: {e}")
        return

    print("\n4. Testing ManagerAgent...")
    try:
        from src.main.python.agents.manager_agent import ManagerAgent
        manager = ManagerAgent()
        print("[OK] Manager Agent OK")
    except Exception as e:
        print(f"[FAIL] ManagerAgent FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n5. Testing FinancialPlannerAgentLLM...")
    try:
        from src.main.python.agents.financial_planner_agent_llm import FinancialPlannerAgentLLM
        planner = FinancialPlannerAgentLLM(
            name="理財規劃專家",
            knowledge_retriever=retriever,
            personal_db=db
        )
        print("[OK] FinancialPlanner OK")
    except Exception as e:
        print(f"[FAIL] FinancialPlanner FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\nAll components initialized successfully!")

if __name__ == "__main__":
    asyncio.run(test_components())