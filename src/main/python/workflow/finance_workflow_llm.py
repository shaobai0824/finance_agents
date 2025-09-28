"""
FinanceWorkflow with LLM - 多代理人理財諮詢工作流程 (使用真實 LLM)

實作 Linus 哲學：
1. 好品味：清晰的工作流程，每個節點職責單純
2. 資料結構優先：狀態驅動的工作流程設計
3. 實用主義：專注解決實際理財諮詢需求
4. 簡潔執念：避免複雜的條件分支和狀態轉換
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from langgraph.graph import END, START, StateGraph

from ..agents import ManagerAgent
from ..agents.financial_planner_agent_llm import FinancialPlannerAgentLLM
from ..agents.financial_analyst_agent_llm import FinancialAnalystAgentLLM
from ..agents.legal_expert_agent_llm import LegalExpertAgentLLM
from ..agents.base_agent import AgentMessage, AgentType, MessageType
from ..rag import KnowledgeRetriever, ChromaVectorStore
from ..database import PersonalFinanceDB
from ..llm import is_llm_configured
from .state_manager import FinanceState, StateManager, WorkflowStatus

logger = logging.getLogger(__name__)


class FinanceWorkflowLLM:
    """理財諮詢工作流程 (使用真實 LLM)

    工作流程：
    1. 使用者查詢 → 2. 路由分析 → 3. 專家處理 → 4. 回應整合 → 5. 最終回應

    所有 agents 都使用 GPT-4o-mini 模型
    """

    def __init__(self):
        """初始化理財諮詢工作流程 (LLM 版本)

        建立專家系統架構：
        - 法律專家：純 LLM 驅動，不使用 RAG
        - 金融/理財專家：LLM + RAG 系統，使用不同 prompt
        """
        self.state_manager = StateManager()

        # 初始化共用 RAG 系統 (僅供金融和理財專家使用)
        try:
            self.vector_store = ChromaVectorStore()
            self.knowledge_retriever = KnowledgeRetriever(self.vector_store)
            logger.info("共用 RAG 系統初始化成功")
        except Exception as e:
            logger.error(f"RAG 系統初始化失敗: {e}")
            self.knowledge_retriever = None

        # 初始化個人財務資料庫
        try:
            self.personal_db = PersonalFinanceDB()
            logger.info("個人財務資料庫連接成功")
        except Exception as e:
            logger.error(f"個人財務資料庫連接失敗: {e}")
            self.personal_db = None

        # 初始化 LLM 專家代理人
        self._initialize_llm_agents()

        # 建立 LangGraph 工作流程
        self._build_workflow()

    def _initialize_llm_agents(self):
        """初始化使用 LLM 的專家代理人"""
        try:
            # 初始化管理代理人 (用於路由)
            self.manager_agent = ManagerAgent()

            # 初始化理財規劃專家 (使用 LLM + RAG + 個人資料庫)
            self.financial_planner = FinancialPlannerAgentLLM(
                name="理財規劃專家",
                knowledge_retriever=self.knowledge_retriever,
                personal_db=self.personal_db
            )

            # 初始化金融分析專家 (使用 LLM + RAG)
            self.financial_analyst = FinancialAnalystAgentLLM(
                name="金融分析專家",
                knowledge_retriever=self.knowledge_retriever
            )

            # 初始化法律專家 (純 LLM，不使用 RAG)
            self.legal_expert = LegalExpertAgentLLM(
                name="法律專家"
            )

            # 專家映射
            self.experts = {
                AgentType.FINANCIAL_PLANNER: self.financial_planner,
                AgentType.FINANCIAL_ANALYST: self.financial_analyst,
                AgentType.LEGAL_EXPERT: self.legal_expert
            }

            # 檢查 LLM 配置狀態
            llm_status = "已配置" if is_llm_configured() else "使用模擬回應"
            logger.info(f"LLM 專家代理人初始化完成，LLM 狀態: {llm_status}")

            # 記錄每個 agent 的狀態
            for agent_type, agent in self.experts.items():
                status = agent.get_llm_status()
                logger.info(f"{agent.name} - LLM: {status['llm_configured']}, 模型: {status['model']}")

        except Exception as e:
            logger.error(f"專家代理人初始化失敗: {e}")
            raise

    def _build_workflow(self):
        """建立 LangGraph 工作流程"""
        # 建立狀態圖
        workflow = StateGraph(FinanceState)

        # 添加節點
        workflow.add_node("query_routing", self._route_query)
        workflow.add_node("expert_processing", self._process_experts)
        workflow.add_node("response_integration", self._integrate_responses)

        # 定義邊
        workflow.add_edge(START, "query_routing")
        workflow.add_edge("query_routing", "expert_processing")
        workflow.add_edge("expert_processing", "response_integration")
        workflow.add_edge("response_integration", END)

        # 編譯工作流程
        self.workflow = workflow.compile()

    async def run(self, user_query: str, user_profile: Dict = None, session_id: str = None) -> Dict:
        """執行理財諮詢工作流程

        Args:
            user_query: 使用者查詢
            user_profile: 使用者資料
            session_id: 會話 ID

        Returns:
            完整的諮詢結果
        """
        session_id = session_id or str(uuid.uuid4())

        try:
            # 初始化狀態
            initial_state = FinanceState(
                user_query=user_query,
                user_profile=user_profile or {},
                session_id=session_id,
                status=WorkflowStatus.PROCESSING,
                expert_responses={},
                expert_sources={},
                final_response="",
                confidence_score=0.0,
                processing_start_time=datetime.now()
            )

            logger.info(f"Starting query routing for session: {session_id}")

            # 執行工作流程
            final_state = await self.workflow.ainvoke(initial_state)

            # 更新狀態管理器
            self.state_manager.update_session_state(session_id, final_state)

            # 返回結果
            return {
                "session_id": session_id,
                "final_response": final_state["final_response"],
                "confidence_score": final_state["confidence_score"],
                "expert_responses": final_state["expert_responses"],
                "expert_sources": final_state["expert_sources"],
                "response_sources": final_state.get("response_sources", []),
                "status": final_state["status"].value,
                "llm_configured": is_llm_configured(),
                "agents_used": list(final_state["expert_responses"].keys())
            }

        except Exception as e:
            logger.error(f"Workflow execution failed for session {session_id}: {e}")
            return {
                "session_id": session_id,
                "final_response": f"工作流程執行失敗：{str(e)}",
                "confidence_score": 0.0,
                "expert_responses": {},
                "expert_sources": {},
                "status": "failed",
                "error": str(e)
            }

    async def _route_query(self, state: FinanceState) -> FinanceState:
        """路由查詢到適當的專家"""
        try:
            query = state["user_query"]

            # 使用管理代理人進行路由決策
            routing_message = AgentMessage(
                agent_type=AgentType.MANAGER,
                message_type=MessageType.ROUTING,
                content=query
            )

            routing_response = await self.manager_agent.process_message(routing_message)
            required_experts = routing_response.metadata.get("required_experts", [AgentType.FINANCIAL_PLANNER])

            logger.info(f"Routing complete. Required experts: {[exp.value for exp in required_experts]}")

            # 更新狀態
            state["required_experts"] = required_experts
            state["routing_decision"] = routing_response.content

            return state

        except Exception as e:
            logger.error(f"Query routing failed: {e}")
            state["required_experts"] = [AgentType.FINANCIAL_PLANNER]  # 預設使用理財規劃師
            return state

    async def _process_experts(self, state: FinanceState) -> FinanceState:
        """並行處理專家諮詢"""
        try:
            required_experts = state["required_experts"]
            query = state["user_query"]
            user_profile = state["user_profile"]

            logger.info(f"Processing experts for session: {state['session_id']}")

            # 準備專家任務
            expert_tasks = []
            for expert_type in required_experts:
                if expert_type in self.experts:
                    message = AgentMessage(
                        agent_type=expert_type,
                        message_type=MessageType.QUERY,
                        content=query,
                        metadata={"user_profile": user_profile}
                    )
                    task = self._process_single_expert(expert_type, message)
                    expert_tasks.append((expert_type, task))

            # 並行執行專家諮詢
            expert_results = {}
            expert_sources = {}

            for expert_type, task in expert_tasks:
                try:
                    response = await task
                    expert_results[expert_type.value] = {
                        "content": response.content,
                        "confidence": response.confidence,
                        "metadata": response.metadata
                    }
                    expert_sources[expert_type.value] = response.sources

                    logger.info(f"Expert {expert_type.value} responded successfully")

                except Exception as e:
                    logger.error(f"Expert {expert_type.value} failed: {e}")
                    expert_results[expert_type.value] = {
                        "content": f"專家諮詢失敗：{str(e)}",
                        "confidence": 0.0,
                        "metadata": {"error": str(e)}
                    }
                    expert_sources[expert_type.value] = []

            # 更新狀態
            state["expert_responses"] = expert_results
            state["expert_sources"] = expert_sources

            return state

        except Exception as e:
            logger.error(f"Expert processing failed: {e}")
            state["expert_responses"] = {}
            state["expert_sources"] = {}
            return state

    async def _process_single_expert(self, expert_type: AgentType, message: AgentMessage):
        """處理單一專家諮詢"""
        expert = self.experts[expert_type]
        return await expert.process_message(message)

    async def _integrate_responses(self, state: FinanceState) -> FinanceState:
        """整合專家回應"""
        try:
            logger.info(f"Integrating responses for session: {state['session_id']}")

            expert_responses = state["expert_responses"]

            if not expert_responses:
                state["final_response"] = "無法獲得專家回應，請稍後再試。"
                state["confidence_score"] = 0.0
                state["status"] = WorkflowStatus.FAILED
                return state

            # 如果只有一個專家回應，直接使用
            if len(expert_responses) == 1:
                expert_type, response_data = next(iter(expert_responses.items()))
                state["final_response"] = response_data["content"]
                state["confidence_score"] = response_data["confidence"]
            else:
                # 多專家回應整合
                integrated_response = self._merge_expert_responses(expert_responses)
                state["final_response"] = integrated_response["content"]
                state["confidence_score"] = integrated_response["confidence"]

            # 收集所有來源
            all_sources = []
            for sources in state["expert_sources"].values():
                all_sources.extend(sources)
            state["response_sources"] = list(set(all_sources))

            # 更新狀態
            state["status"] = WorkflowStatus.COMPLETED
            state["processing_end_time"] = datetime.now()

            logger.info(f"Response integration complete. Confidence: {state['confidence_score']}")

            return state

        except Exception as e:
            logger.error(f"Response integration failed: {e}")
            state["final_response"] = f"回應整合失敗：{str(e)}"
            state["confidence_score"] = 0.0
            state["status"] = WorkflowStatus.FAILED
            return state

    def _merge_expert_responses(self, expert_responses: Dict) -> Dict:
        """合併多個專家回應"""
        try:
            # 簡單的回應合併策略
            contents = []
            confidences = []

            for expert_type, response_data in expert_responses.items():
                if response_data["content"]:
                    contents.append(f"**{expert_type}建議**：\n{response_data['content']}")
                    confidences.append(response_data["confidence"])

            if not contents:
                return {
                    "content": "無法生成專家建議，請稍後再試。",
                    "confidence": 0.0
                }

            # 合併內容
            merged_content = "\n\n".join(contents)

            # 計算平均信心度
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return {
                "content": merged_content,
                "confidence": avg_confidence
            }

        except Exception as e:
            logger.error(f"Response merging failed: {e}")
            return {
                "content": "回應合併失敗",
                "confidence": 0.0
            }

    def get_workflow_status(self, session_id: str) -> Dict:
        """取得工作流程狀態"""
        try:
            state = self.state_manager.get_session_state(session_id)
            if not state:
                return {"error": "Session not found"}

            return {
                "session_id": session_id,
                "status": state["status"].value if state.get("status") else "unknown",
                "expert_count": len(state.get("expert_responses", {})),
                "confidence_score": state.get("confidence_score", 0.0),
                "llm_configured": is_llm_configured()
            }

        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {"error": str(e)}

    def get_system_info(self) -> Dict[str, Any]:
        """取得系統資訊"""
        return {
            "workflow_type": "LLM-Enhanced Finance Workflow",
            "llm_configured": is_llm_configured(),
            "agents": {
                name: agent.get_llm_status()
                for name, agent in self.experts.items()
            },
            "rag_system": bool(self.knowledge_retriever),
            "personal_db": bool(self.personal_db),
            "active_sessions": len(self.state_manager.sessions)
        }