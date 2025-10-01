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
from ..agents.base_agent import AgentMessage, AgentType, MessageType
from ..agents.financial_analyst_agent_llm import FinancialAnalystAgentLLM
from ..agents.financial_planner_agent_llm import FinancialPlannerAgentLLM
from ..agents.legal_expert_agent_llm import LegalExpertAgentLLM
from ..database import PersonalFinanceDB
from ..llm import is_llm_configured
from ..rag import ChromaVectorStore, KnowledgeRetriever
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
            self.vector_store = ChromaVectorStore(collection_name="finance_knowledge_optimal")
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

    async def run(
        self,
        user_query: str,
        user_profile: Dict = None,
        session_id: str = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict:
        """執行理財諮詢工作流程

        Args:
            user_query: 使用者查詢
            user_profile: 使用者資料
            session_id: 會話 ID
            conversation_history: 對話歷史（OpenAI 格式）

        Returns:
            完整的諮詢結果
        """
        session_id = session_id or str(uuid.uuid4())

        try:
            # 初始化狀態
            initial_state = self.state_manager.create_initial_state(
                session_id=session_id,
                user_query=user_query,
                user_profile=user_profile,
                conversation_history=conversation_history
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
            logger.info(f"Starting query routing for: {query[:50]}...")

            # 使用管理代理人進行路由決策（添加超時保護）
            routing_message = AgentMessage(
                agent_type=AgentType.MANAGER,
                message_type=MessageType.QUERY,
                content=query
            )

            logger.info("Calling manager agent for routing...")
            routing_response = await asyncio.wait_for(
                self.manager_agent.process_message(routing_message),
                timeout=10.0  # 路由決策最多 10 秒
            )
            logger.info("Manager agent routing completed")

            # 安全獲取 metadata
            if routing_response.metadata and "required_experts" in routing_response.metadata:
                expert_names = routing_response.metadata["required_experts"]
            else:
                expert_names = ["financial_planner"]  # 默認值

            # 轉換字符串為 AgentType 枚舉
            required_experts = []
            for name in expert_names:
                if name == "financial_planner":
                    required_experts.append(AgentType.FINANCIAL_PLANNER)
                elif name == "financial_analyst":
                    required_experts.append(AgentType.FINANCIAL_ANALYST)
                elif name == "legal_expert":
                    required_experts.append(AgentType.LEGAL_EXPERT)
                else:
                    required_experts.append(AgentType.FINANCIAL_PLANNER)  # 默認

            logger.info(f"Routing complete. Required experts: {[exp.value for exp in required_experts]}")

            # 更新狀態
            state["required_experts"] = required_experts
            state["routing_decision"] = routing_response.content

            return state

        except asyncio.TimeoutError:
            logger.error("Query routing timed out after 10s, using default expert")
            state["required_experts"] = [AgentType.FINANCIAL_PLANNER]  # 預設使用理財規劃師
            state["routing_decision"] = "路由超時，使用預設理財規劃專家"
            return state
        except Exception as e:
            logger.error(f"Query routing failed: {e}")
            import traceback
            traceback.print_exc()
            state["required_experts"] = [AgentType.FINANCIAL_PLANNER]  # 預設使用理財規劃師
            return state

    async def _process_experts(self, state: FinanceState) -> FinanceState:
        """並行處理專家諮詢

        Linus 實用主義：將對話歷史傳遞給所有專家
        """
        try:
            required_experts = state["required_experts"]
            query = state["user_query"]
            user_profile = state["user_profile"]
            conversation_history = state.get("conversation_history", [])

            logger.info(f"Processing experts for session: {state['session_id']}")
            logger.info(f"Required experts: {[e.value for e in required_experts]}")
            if conversation_history:
                logger.info(f"Using conversation history with {len(conversation_history)} messages")

            # 準備專家任務（添加超時保護）
            expert_tasks = []
            for expert_type in required_experts:
                if expert_type in self.experts:
                    logger.info(f"Preparing task for expert: {expert_type.value}")
                    message = AgentMessage(
                        agent_type=expert_type,
                        message_type=MessageType.QUERY,
                        content=query,
                        metadata={
                            "user_profile": user_profile,
                            "conversation_history": conversation_history  # 傳遞對話歷史
                        }
                    )
                    # 添加超時保護：每個專家最多 20 秒
                    task = asyncio.wait_for(
                        self._process_single_expert(expert_type, message),
                        timeout=20.0
                    )
                    expert_tasks.append((expert_type, task))
                else:
                    logger.warning(f"Expert type {expert_type.value} not found in experts dict")

            # 真正並行執行所有專家諮詢（使用 asyncio.gather）
            logger.info(f"Starting parallel execution of {len(expert_tasks)} expert tasks...")
            expert_results = {}
            expert_sources = {}

            # 分離 expert_types 和 tasks
            expert_types = [et for et, _ in expert_tasks]
            tasks = [t for _, t in expert_tasks]

            # 使用 gather 並行執行，return_exceptions=True 確保單個失敗不影響其他
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 處理結果
            for expert_type, result in zip(expert_types, results):
                try:
                    if isinstance(result, Exception):
                        # 處理異常（包括超時）
                        if isinstance(result, asyncio.TimeoutError):
                            logger.error(f"Expert {expert_type.value} timed out after 20s")
                            error_msg = "專家處理超時，請稍後再試"
                        else:
                            logger.error(f"Expert {expert_type.value} failed: {result}")
                            error_msg = f"專家諮詢失敗：{str(result)}"

                        expert_results[expert_type.value] = {
                            "content": error_msg,
                            "confidence": 0.0,
                            "metadata": {"error": str(result)}
                        }
                        expert_sources[expert_type.value] = []
                    else:
                        # 成功響應
                        response = result
                        expert_results[expert_type.value] = {
                            "content": response.content,
                            "confidence": response.confidence,
                            "metadata": response.metadata
                        }
                        expert_sources[expert_type.value] = response.sources
                        logger.info(f"Expert {expert_type.value} responded successfully")

                except Exception as e:
                    logger.error(f"Error processing result from {expert_type.value}: {e}")
                    expert_results[expert_type.value] = {
                        "content": f"結果處理失敗：{str(e)}",
                        "confidence": 0.0,
                        "metadata": {"error": str(e)}
                    }
                    expert_sources[expert_type.value] = []

            logger.info(f"Expert processing complete. Got {len(expert_results)} results")

            # 更新狀態
            state["expert_responses"] = expert_results
            state["expert_sources"] = expert_sources

            return state

        except Exception as e:
            logger.error(f"Expert processing failed: {e}")
            import traceback
            traceback.print_exc()
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
            "active_sessions": len(self.state_manager.session_id)
        }

    async def run_stream(
        self,
        user_query: str,
        user_profile: Dict = None,
        session_id: str = None,
        conversation_history: List[Dict[str, str]] = None
    ):
        """執行理財諮詢工作流程（流式模式）

        這個方法繞過 LangGraph，直接進行流式處理，讓用戶更快看到第一個回應

        Args:
            user_query: 使用者查詢
            user_profile: 使用者資料
            session_id: 會話 ID
            conversation_history: 對話歷史

        Yields:
            str: 逐塊生成的回應內容
        """
        session_id = session_id or str(uuid.uuid4())

        try:
            # 步驟 1: 路由決策（快速，1-2秒）
            logger.info(f"[Stream] Starting routing for session: {session_id}")
            routing_message = AgentMessage(
                agent_type=AgentType.MANAGER,
                message_type=MessageType.QUERY,
                content=user_query
            )

            routing_response = await asyncio.wait_for(
                self.manager_agent.process_message(routing_message),
                timeout=10.0
            )

            # 獲取需要的專家
            if routing_response.metadata and "required_experts" in routing_response.metadata:
                expert_names = routing_response.metadata["required_experts"]
            else:
                expert_names = ["financial_planner"]

            # 轉換為 AgentType
            required_experts = []
            for name in expert_names:
                if name == "financial_planner":
                    required_experts.append(AgentType.FINANCIAL_PLANNER)
                elif name == "financial_analyst":
                    required_experts.append(AgentType.FINANCIAL_ANALYST)
                elif name == "legal_expert":
                    required_experts.append(AgentType.LEGAL_EXPERT)

            logger.info(f"[Stream] Experts required: {[e.value for e in required_experts]}")

            # 步驟 2: 流式處理專家回應
            # 策略：依序處理每個專家，並即時流式輸出
            all_rag_docs = []  # 收集所有專家的 RAG 檢索結果

            for expert_type in required_experts:
                if expert_type not in self.experts:
                    continue

                expert = self.experts[expert_type]
                logger.info(f"[Stream] Processing expert: {expert_type.value}")

                # 準備訊息
                message = AgentMessage(
                    agent_type=expert_type,
                    message_type=MessageType.QUERY,
                    content=user_query,
                    metadata={
                        "user_profile": user_profile or {},
                        "conversation_history": conversation_history or []
                    }
                )

                # 檢查 expert 是否有流式方法
                if hasattr(expert, 'process_message_stream'):
                    # 使用流式處理
                    logger.info(f"[Stream] Using stream mode for {expert_type.value}")
                    async for chunk in expert.process_message_stream(message):
                        yield chunk

                    # 收集 RAG 檢索結果
                    if hasattr(expert, 'last_retrieved_docs') and expert.last_retrieved_docs:
                        all_rag_docs.extend(expert.last_retrieved_docs)
                else:
                    # 降級到普通模式（無超時限制，讓 LLM 自然完成）
                    logger.info(f"[Stream] Falling back to normal mode for {expert_type.value}")
                    response = await expert.process_message(message)

                    # 模擬流式輸出
                    content = response.content
                    chunk_size = 10
                    for i in range(0, len(content), chunk_size):
                        yield content[i:i+chunk_size]
                        await asyncio.sleep(0.01)  # 10ms 延遲

                # 如果有多個專家，在專家之間添加分隔
                if len(required_experts) > 1 and expert_type != required_experts[-1]:
                    yield "\n\n---\n\n"

            # 步驟 3: 在回應末尾附加 RAG 來源文件
            if all_rag_docs:
                yield "\n\n---\n\n### 📚 參考資料來源\n\n"
                for idx, doc in enumerate(all_rag_docs[:5], 1):  # 最多顯示 5 個來源
                    # RAG 文件是 RetrievalResult dataclass 物件
                    # 屬性: content, metadata, similarity_score, source, expert_domain, confidence
                    metadata = doc.metadata if hasattr(doc, 'metadata') else {}

                    title = metadata.get('title', '未知標題')
                    category = metadata.get('category', '未分類')
                    url = metadata.get('url', '')

                    # 使用 scrape_time 作為時間（原始資料沒有 publish_time）
                    scrape_time = metadata.get('scrape_time', '')
                    if scrape_time:
                        # 格式化時間：從 "2025-09-27T13:21:14.501841" 提取 "2025-09-27"
                        time_display = scrape_time.split('T')[0] if 'T' in scrape_time else scrape_time
                    else:
                        time_display = '--'

                    # source 是 dataclass 的直接屬性
                    source = doc.source if hasattr(doc, 'source') else metadata.get('source', '未知來源')

                    yield f"**{idx}. {title}**\n"
                    yield f"   - 📂 分類：{category}\n"
                    yield f"   - 📅 資料時間：{time_display}\n"
                    yield f"   - 🌐 來源：{source}\n"
                    if url:
                        yield f"   - 🔗 [查看原文]({url})\n"
                    yield "\n"

            logger.info(f"[Stream] Completed for session: {session_id}")

        except asyncio.TimeoutError:
            logger.error("[Stream] Processing timed out")
            yield "抱歉，處理超時，請稍後再試。"
        except Exception as e:
            logger.error(f"[Stream] Error: {e}")
            import traceback
            traceback.print_exc()
            yield f"抱歉，處理時發生錯誤：{str(e)}"