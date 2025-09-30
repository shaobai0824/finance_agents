"""
ManagerAgent - 智能路由管理人

職責：
1. 分析使用者查詢內容
2. 決定需要哪些專家參與
3. 協調多個代理人的工作流程
4. 彙整最終回應

Linus 哲學應用：
- 好品味：路由邏輯清晰，無複雜條件分支
- 實用主義：基於實際需求路由，不做過度複雜的分析
- 簡潔執念：專注路由決策，不處理具體領域問題
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Set

from .base_agent import AgentMessage, AgentType, BaseAgent, MessageType

logger = logging.getLogger(__name__)


class ManagerAgent(BaseAgent):
    """智能路由管理人

    負責分析查詢並決定專家參與策略
    """

    def __init__(self):
        super().__init__(AgentType.MANAGER, "FinanceManager", use_rag=False)

        # 關鍵字映射：查詢內容 -> 需要的專家
        # Linus 哲學：好品味的資料結構，避免複雜的 if/else
        self.expert_keywords = {
            AgentType.FINANCIAL_PLANNER: {
                "keywords": [
                    "理財規劃", "資產配置", "風險評估", "退休規劃", "投資建議",
                    "保險", "儲蓄", "個人財務", "投資組合", "資金分配", "理財",
                    "個人理財", "財務規劃", "風險管理", "退休", "養老",
                    "investment advice", "portfolio", "savings", "retirement", "insurance",
                    "personal finance", "financial planning"
                ],
                "confidence_boost": 0.3
            },
            AgentType.FINANCIAL_ANALYST: {
                "keywords": [
                    "市場分析", "股票", "債券", "基金", "匯率", "經濟情勢",
                    "技術分析", "財報分析", "產業趨勢", "金融數據", "台積電",
                    "個股", "股價", "漲跌", "市場", "分析", "報告", "投資分析",
                    "股市", "台股", "美股", "股票推薦", "股票建議", "股票投資",
                    "stock", "market", "analysis", "economic", "trend", "data",
                    "share", "equity", "finance"
                ],
                "confidence_boost": 0.3
            },
            AgentType.LEGAL_EXPERT: {
                "keywords": [
                    "法規", "合規", "稅務", "法律", "規範", "條文", "監管",
                    "金融法", "投資法規", "稅務規劃", "法律風險", "法律問題",
                    "合規問題", "稅法", "法律諮詢", "合規性", "法規遵循",
                    "legal", "regulation", "compliance", "tax", "law"
                ],
                "confidence_boost": 0.3
            }
        }

    def _get_system_prompt(self) -> str:
        """管理員的系統提示詞"""
        return """你是智能路由管理人，負責分析使用者查詢並決定需要哪些專家參與。

# 職責
- 分析使用者查詢內容和意圖
- 決定需要哪些專業領域的專家
- 協調多個代理人的工作流程
- 不處理具體的理財問題，只負責路由決策

# 專家類型
- financial_planner: 理財規劃專家 - 個人理財、投資建議、資產配置
- financial_analyst: 金融分析專家 - 市場分析、股票分析、技術分析
- legal_expert: 法律專家 - 法規合規、稅務問題、法律風險

# 路由原則
1. 基於關鍵字匹配決定專家參與
2. 可以同時調用多個專家
3. 如果查詢不明確，默認使用理財規劃專家
4. 確保每個查詢都有適當的專家處理"""

    async def _build_prompt(self, query: str, knowledge_results: List[Dict], personal_context: Dict[str, Any]) -> str:
        """構建路由分析提示詞"""
        prompt = f"""作為智能路由管理人，請分析以下查詢並決定需要哪些專家參與：

查詢內容：{query}

可用專家：
1. financial_planner - 理財規劃專家（個人理財、投資建議、資產配置）
2. financial_analyst - 金融分析專家（市場分析、股票分析、技術分析）
3. legal_expert - 法律專家（法規合規、稅務問題、法律風險）

請分析查詢內容，決定需要哪些專家參與，並說明原因。"""

        return prompt

    async def _generate_fallback_response(self, prompt: str) -> str:
        """LLM 不可用時的降級回應"""
        return """路由分析完成，基於查詢內容，建議調用以下專家：
- 理財規劃專家：處理投資建議和資產配置
- 金融分析專家：提供市場和股票分析
- 法律專家：處理稅務和法規問題

這是基於關鍵字匹配的標準路由建議。"""

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """處理路由決策請求"""
        try:
            if message.message_type == MessageType.QUERY:
                return await self._route_query(message)
            else:
                # 處理來自其他代理人的訊息（彙整回應等）
                return await self._coordinate_response(message)

        except Exception as e:
            logger.error(f"Manager agent processing error: {e}")
            return self.create_response(
                f"路由處理發生錯誤：{str(e)}",
                MessageType.ERROR,
                confidence=0.0
            )

    async def can_handle(self, query: str) -> float:
        """管理人可以處理所有查詢（路由功能）"""
        return 1.0

    async def _route_query(self, message: AgentMessage) -> AgentMessage:
        """分析查詢並決定專家參與策略

        Args:
            message: 使用者查詢訊息

        Returns:
            包含路由決策的訊息
        """
        query = message.content.lower()
        required_experts = await self._analyze_query_requirements(query)

        # 建立路由決策
        route_metadata = {
            "required_experts": [expert.value for expert in required_experts],
            "query_analysis": await self._extract_key_concepts(query),
            "routing_strategy": self._determine_routing_strategy(required_experts)
        }

        # 根據需要的專家數量決定信心度
        confidence = min(0.9, 0.5 + (len(required_experts) * 0.2))

        return self.create_response(
            content=f"路由分析完成，需要以下專家參與：{', '.join([e.value for e in required_experts])}",
            message_type=MessageType.ROUTE,
            metadata=route_metadata,
            confidence=confidence
        )

    async def _analyze_query_requirements(self, query: str) -> Set[AgentType]:
        """分析查詢需要哪些專家參與

        Linus 哲學：好品味的演算法
        - 避免複雜的條件判斷
        - 基於關鍵字權重計算
        - 可以輕鬆添加新的專家類型
        """
        required_experts = set()

        # 對每個專家類型計算匹配分數
        scores = {}
        for expert_type, config in self.expert_keywords.items():
            # 計算關鍵字匹配度
            matches = sum(1 for keyword in config["keywords"] if keyword in query)
            match_ratio = matches / len(config["keywords"])

            # 計算總分數（匹配數量 + 匹配比例）
            score = matches + match_ratio
            scores[expert_type] = score

            # 專家觸發邏輯優化
            if expert_type == AgentType.LEGAL_EXPERT and matches >= 1:
                # 法律專家：只要有一個法律關鍵字就觸發
                required_experts.add(expert_type)
                logger.info(f"Legal expert triggered by {matches} keyword matches")
            elif expert_type == AgentType.FINANCIAL_ANALYST and matches >= 1:
                # 金融分析專家：只要有一個關鍵字就觸發（因為關鍵字很具體）
                required_experts.add(expert_type)
                logger.info(f"Financial analyst triggered by {matches} keyword matches")
            elif expert_type == AgentType.FINANCIAL_PLANNER and (match_ratio > 0.08 or matches >= 2):
                # 理財規劃專家：使用較寬鬆的匹配條件
                required_experts.add(expert_type)
                logger.info(f"Financial planner triggered by {matches} keyword matches, ratio {match_ratio:.3f}")

        # 如果沒有明確匹配，默認使用理財專家
        if not required_experts:
            required_experts.add(AgentType.FINANCIAL_PLANNER)
            logger.info("No specific expertise detected, defaulting to financial planner")

        logger.info(f"Query: '{query}' -> Experts: {[e.value for e in required_experts]}, Scores: {[(k.value, v) for k, v in scores.items()]}")
        return required_experts

    async def _extract_key_concepts(self, query: str) -> List[str]:
        """從查詢中提取關鍵概念"""
        # 簡化的關鍵概念提取（可以後續用 NLP 改進）
        concepts = []

        # 金額相關
        if re.search(r'[\d,]+\s*萬|[\d,]+\s*元|\$[\d,]+', query):
            concepts.append("具體金額")

        # 時間相關
        if re.search(r'\d+年|短期|長期|近期', query):
            concepts.append("時間框架")

        # 風險相關
        if any(word in query for word in ["風險", "穩健", "保守", "積極"]):
            concepts.append("風險偏好")

        return concepts

    def _determine_routing_strategy(self, required_experts: Set[AgentType]) -> str:
        """決定路由策略"""
        if len(required_experts) == 1:
            return "single_expert"
        elif len(required_experts) == 2:
            return "collaborative"
        else:
            return "multi_expert_consensus"

    async def _coordinate_response(self, message: AgentMessage) -> AgentMessage:
        """協調來自其他代理人的回應"""
        # 這裡會處理來自各專家的回應，進行彙整
        # 目前先返回基本回應，後續實作完整的協調邏輯

        return self.create_response(
            content="正在協調各專家意見，準備彙整回應...",
            message_type=MessageType.RESPONSE,
            confidence=0.8
        )

    async def create_coordination_plan(self, experts: List[AgentType]) -> Dict[str, Any]:
        """建立協調計劃"""
        return {
            "execution_order": experts,  # 專家執行順序
            "parallel_execution": len(experts) <= 2,  # 是否可並行執行
            "consensus_required": len(experts) >= 3,  # 是否需要共識機制
            "timeout_seconds": 30 + (len(experts) * 10)  # 動態超時設定
        }