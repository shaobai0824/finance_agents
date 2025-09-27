"""
FinanceWorkflow - 多代理人理財諮詢工作流程

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
from ..agents.financial_planner_agent_new import FinancialPlannerAgent
from ..agents.financial_analyst_agent import FinancialAnalystAgent
from ..agents.legal_expert_agent import LegalExpertAgent
from ..agents.base_agent import AgentMessage, AgentType, MessageType
from ..rag import KnowledgeRetriever, ChromaVectorStore
from .state_manager import FinanceState, StateManager, WorkflowStatus

logger = logging.getLogger(__name__)


class FinanceWorkflow:
    """理財諮詢工作流程

    工作流程：
    1. 使用者查詢 → 2. 路由分析 → 3. 專家處理 → 4. 回應整合 → 5. 最終回應
    """

    def __init__(self):
        """初始化理財諮詢工作流程

        建立專家系統架構：
        - 法律專家：純 prompt 驅動，不使用 RAG
        - 金融/理財專家：共用 RAG 系統，但使用不同 prompt
        """
        self.state_manager = StateManager()

        # 初始化共用 RAG 系統 (僅供金融和理財專家使用)
        try:
            self.vector_store = ChromaVectorStore()
            self.knowledge_retriever = KnowledgeRetriever(self.vector_store)
            logger.info("共用 RAG 系統初始化成功")
        except Exception as e:
            logger.warning(f"RAG 系統初始化失敗: {e}")
            self.vector_store = None
            self.knowledge_retriever = None

        # 初始化各類專家
        self.manager_agent = ManagerAgent()

        # 法律專家 - 純 prompt 驅動 (不使用 RAG)
        self.legal_expert = LegalExpertAgent(name="法律合規專家")

        # 金融分析專家 - 使用共用 RAG 系統
        self.financial_analyst = FinancialAnalystAgent(
            name="金融分析專家",
            knowledge_retriever=self.knowledge_retriever
        )

        # 初始化個人理財資料庫
        try:
            from ..database import PersonalFinanceDB
            self.personal_db = PersonalFinanceDB()
            logger.info("個人理財資料庫初始化成功")
        except Exception as e:
            logger.warning(f"個人理財資料庫初始化失敗: {e}")
            self.personal_db = None

        # 理財規劃專家 - 使用共用 RAG 系統 + 個人資料庫
        self.financial_planner = FinancialPlannerAgent(
            name="理財規劃專家",
            knowledge_retriever=self.knowledge_retriever,
            personal_db=self.personal_db
        )

        # 專家對應表
        self.agents = {
            AgentType.MANAGER.value: self.manager_agent,
            AgentType.LEGAL_EXPERT.value: self.legal_expert,
            AgentType.FINANCIAL_ANALYST.value: self.financial_analyst,
            AgentType.FINANCIAL_PLANNER.value: self.financial_planner,
        }

        logger.info(f"專家系統初始化完成：{len(self.agents)} 個專家")
        logger.info(f"法律專家 RAG 狀態: {self.legal_expert.use_rag}")
        logger.info(f"金融專家 RAG 狀態: {self.financial_analyst.use_rag}")
        logger.info(f"理財專家 RAG 狀態: {self.financial_planner.use_rag}")

        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """建立 LangGraph 工作流程

        Linus 哲學：好品味的工作流程設計
        - 每個節點職責單純
        - 狀態轉換邏輯清晰
        - 避免複雜的條件判斷
        """
        workflow = StateGraph(FinanceState)

        # 定義節點
        workflow.add_node("route_query", self._route_query)
        workflow.add_node("process_experts", self._process_experts)
        workflow.add_node("integrate_responses", self._integrate_responses)
        workflow.add_node("handle_error", self._handle_error)

        # 定義邊
        workflow.add_edge(START, "route_query")
        workflow.add_conditional_edges(
            "route_query",
            self._should_continue_after_routing,
            {
                "process": "process_experts",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "process_experts",
            self._should_continue_after_processing,
            {
                "integrate": "integrate_responses",
                "error": "handle_error"
            }
        )
        workflow.add_edge("integrate_responses", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    async def _route_query(self, state: FinanceState) -> FinanceState:
        """路由查詢到適當的專家

        Linus 哲學：單一職責
        - 只負責路由決策，不處理具體業務邏輯
        """
        try:
            logger.info(f"Starting query routing for session: {state['session_id']}")

            # 建立管理代理人訊息
            query_message = AgentMessage(
                agent_type=AgentType.MANAGER,
                message_type=MessageType.QUERY,
                content=state["user_query"],
                metadata={"user_profile": state.get("user_profile")}
            )

            # 管理代理人進行路由分析
            route_response = await self.manager_agent.process_message(query_message)

            if route_response.message_type == MessageType.ERROR:
                return self.state_manager.add_error(state, route_response.content)

            # 更新路由資訊
            routing_metadata = route_response.metadata or {}
            required_experts = routing_metadata.get("required_experts", [])

            state = self.state_manager.update_routing_info(
                state,
                required_experts=required_experts,
                confidence=route_response.confidence or 0.5,
                metadata=routing_metadata
            )

            logger.info(f"Routing complete. Required experts: {required_experts}")
            return state

        except Exception as e:
            logger.error(f"Error in route_query: {e}")
            return self.state_manager.add_error(state, f"路由分析失敗: {str(e)}")

    async def _process_experts(self, state: FinanceState) -> FinanceState:
        """處理專家諮詢

        Linus 哲學：實用主義
        - 可以並行處理多個專家（如果需要）
        - 容錯處理，單個專家失敗不影響整體流程
        """
        try:
            logger.info(f"Processing experts for session: {state['session_id']}")

            required_experts = state["required_experts"]
            if not required_experts:
                return self.state_manager.add_error(state, "沒有找到適合的專家")

            # 準備專家查詢訊息
            expert_message = AgentMessage(
                agent_type=AgentType.MANAGER,  # 來源是管理者
                message_type=MessageType.QUERY,
                content=state["user_query"],
                metadata={
                    "user_profile": state.get("user_profile"),
                    "routing_metadata": state["routing_metadata"]
                }
            )

            # 處理每個專家（目前序列處理，後續可改為並行）
            for expert_type in required_experts:
                if expert_type in self.agents:
                    try:
                        agent = self.agents[expert_type]
                        response = await agent.process_message(expert_message)

                        if response.message_type != MessageType.ERROR:
                            state = self.state_manager.add_expert_response(
                                state,
                                expert_type=expert_type,
                                response_content=response.content,
                                metadata=response.metadata or {},
                                sources=response.sources or [],
                                confidence=response.confidence or 0.5
                            )
                            logger.info(f"Expert {expert_type} responded successfully")
                        else:
                            logger.warning(f"Expert {expert_type} returned error: {response.content}")
                            state = self.state_manager.add_error(
                                state,
                                f"專家 {expert_type} 處理失敗: {response.content}"
                            )

                    except Exception as e:
                        logger.error(f"Error processing expert {expert_type}: {e}")
                        state = self.state_manager.add_error(
                            state,
                            f"專家 {expert_type} 處理異常: {str(e)}"
                        )
                else:
                    logger.warning(f"Expert {expert_type} not found in available agents")
                    state = self.state_manager.add_error(
                        state,
                        f"找不到專家: {expert_type}"
                    )

            return state

        except Exception as e:
            logger.error(f"Error in process_experts: {e}")
            return self.state_manager.add_error(state, f"專家處理流程失敗: {str(e)}")

    async def _integrate_responses(self, state: FinanceState) -> FinanceState:
        """整合專家回應

        Linus 哲學：好品味的資料整合
        - 簡單的整合邏輯勝過複雜的演算法
        - 保持來源追蹤的透明性
        """
        try:
            logger.info(f"Integrating responses for session: {state['session_id']}")

            expert_responses = state["expert_responses"]
            if not expert_responses:
                return self.state_manager.add_error(state, "沒有專家回應可以整合")

            # 簡單的整合策略：按專家類型組織回應
            integrated_response = self._create_integrated_response(expert_responses)

            # 收集所有資料來源
            all_sources = []
            for expert_type, sources in state["expert_sources"].items():
                all_sources.extend(sources)

            # 計算整體信心度
            overall_confidence = self.state_manager.calculate_overall_confidence(state)

            # 設定最終回應
            state = self.state_manager.set_final_response(
                state,
                final_response=integrated_response,
                confidence_score=overall_confidence,
                sources=list(set(all_sources))  # 去重
            )

            logger.info(f"Response integration complete. Confidence: {overall_confidence}")
            return state

        except Exception as e:
            logger.error(f"Error in integrate_responses: {e}")
            return self.state_manager.add_error(state, f"回應整合失敗: {str(e)}")

    def _create_integrated_response(self, expert_responses: Dict[str, Dict[str, Any]]) -> str:
        """建立整合回應

        Linus 哲學：簡潔執念
        - 清晰的回應結構
        - 避免冗餘資訊
        """
        if len(expert_responses) == 1:
            # 單一專家，直接返回回應
            response = list(expert_responses.values())[0]
            return response["content"]

        # 多專家整合
        integrated = "# 🤖 綜合理財建議\n\n"
        integrated += "基於多位專家的分析，為您提供以下建議：\n\n"

        expert_names = {
            "financial_planner": "💰 理財規劃專家",
            "financial_analyst": "📊 金融分析專家",
            "legal_expert": "⚖️ 法律專家"
        }

        for expert_type, response in expert_responses.items():
            expert_name = expert_names.get(expert_type, f"專家 ({expert_type})")
            confidence = response.get("confidence", 0.5)

            integrated += f"## {expert_name}\n"
            integrated += f"**信心度：{confidence:.1%}**\n\n"
            integrated += f"{response['content']}\n\n"
            integrated += "---\n\n"

        # 添加整合說明
        integrated += "## 💡 整合建議\n\n"
        integrated += "以上建議來自不同領域的專家，請根據您的具體情況進行評估。"
        integrated += "如需更詳細的個人化建議，建議諮詢專業理財顧問。\n\n"

        integrated += "*本建議僅供參考，投資有風險，請謹慎評估。*"

        return integrated

    async def _handle_error(self, state: FinanceState) -> FinanceState:
        """處理錯誤狀態"""
        logger.error(f"Workflow error for session {state['session_id']}: {state['error_messages']}")

        error_response = "很抱歉，處理您的查詢時發生了問題。\n\n"
        error_response += "錯誤詳情：\n"
        for i, error in enumerate(state["error_messages"], 1):
            error_response += f"{i}. {error}\n"

        error_response += "\n請稍後再試，或聯繫客服人員協助。"

        state["final_response"] = error_response
        state["confidence_score"] = 0.0
        state["status"] = WorkflowStatus.FAILED.value

        return state

    def _should_continue_after_routing(self, state: FinanceState) -> str:
        """路由後的條件判斷"""
        if state["error_messages"]:
            return "error"
        if self.state_manager.is_routing_complete(state):
            return "process"
        return "error"

    def _should_continue_after_processing(self, state: FinanceState) -> str:
        """處理後的條件判斷"""
        if state["error_messages"] and not state["expert_responses"]:
            return "error"
        if state["expert_responses"]:
            return "integrate"
        return "error"

    async def run(
        self,
        user_query: str,
        user_profile: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> FinanceState:
        """執行理財諮詢工作流程

        Args:
            user_query: 使用者查詢
            user_profile: 使用者資料（可選）
            session_id: 會話 ID（可選，會自動生成）

        Returns:
            最終的工作流程狀態
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        # 建立初始狀態
        initial_state = self.state_manager.create_initial_state(
            session_id=session_id,
            user_query=user_query,
            user_profile=user_profile
        )

        try:
            # 執行工作流程
            final_state = await self.workflow.ainvoke(initial_state)
            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            error_state = self.state_manager.add_error(initial_state, f"工作流程執行失敗: {str(e)}")
            return await self._handle_error(error_state)