"""
KnowledgeRetriever - 知識檢索器

實作 Linus 哲學：
1. 好品味：統一的檢索介面，支援多種檢索策略
2. 資料結構優先：檢索結果的結構化設計
3. 實用主義：專注實際的知識檢索需求
4. 簡潔執念：避免過度複雜的檢索演算法
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import re
from dataclasses import dataclass
from enum import Enum

from .chroma_vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class ExpertDomain(Enum):
    """專家領域枚舉"""
    FINANCIAL_PLANNING = "financial_planning"
    FINANCIAL_ANALYSIS = "financial_analysis"
    LEGAL_COMPLIANCE = "legal_compliance"
    GENERAL = "general"


@dataclass
class RetrievalResult:
    """檢索結果資料結構

    Linus 哲學：好品味的資料結構
    - 所有檢索結果使用統一格式
    - 包含足夠的上下文資訊
    - 支援來源追蹤
    """
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    source: str
    expert_domain: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "similarity_score": self.similarity_score,
            "source": self.source,
            "expert_domain": self.expert_domain,
            "confidence": self.confidence
        }


class KnowledgeRetriever:
    """知識檢索器

    為不同的理財專家提供專業知識檢索服務
    """

    def __init__(self, vector_store: ChromaVectorStore):
        self.vector_store = vector_store
        self.logger = logging.getLogger(f"{__name__}.KnowledgeRetriever")

        # 專家領域關鍵字映射
        self.domain_keywords = {
            ExpertDomain.FINANCIAL_PLANNING: [
                "投資建議", "理財規劃", "資產配置", "風險評估", "退休規劃",
                "保險", "儲蓄", "個人財務", "投資組合", "資金分配"
            ],
            ExpertDomain.FINANCIAL_ANALYSIS: [
                "市場分析", "股票", "債券", "基金", "匯率", "經濟情勢",
                "技術分析", "財報分析", "產業趨勢", "金融數據"
            ],
            ExpertDomain.LEGAL_COMPLIANCE: [
                "法規", "合規", "稅務", "法律", "規範", "條文", "監管",
                "金融法", "投資法規", "稅務規劃", "法律風險"
            ]
        }

    async def retrieve_for_expert(
        self,
        query: str,
        expert_domain: ExpertDomain,
        max_results: int = 5,
        similarity_threshold: float = 0.6
    ) -> List[RetrievalResult]:
        """為特定專家檢索相關知識

        Args:
            query: 查詢內容
            expert_domain: 專家領域
            max_results: 最大結果數
            similarity_threshold: 相似度閾值

        Returns:
            檢索結果清單

        Linus 哲學：實用主義
        - 基於專家領域優化檢索策略
        - 簡單有效的相似度計算
        """
        try:
            # 增強查詢：添加領域相關關鍵字
            enhanced_query = self._enhance_query_for_domain(query, expert_domain)

            # 執行向量搜尋
            search_results = self.vector_store.get_similar_documents(
                query=enhanced_query,
                similarity_threshold=similarity_threshold,
                max_results=max_results * 2  # 搜尋更多結果以供篩選
            )

            # 轉換為結構化結果
            retrieval_results = []
            for result in search_results[:max_results]:
                retrieval_result = self._create_retrieval_result(
                    result, expert_domain, query
                )
                retrieval_results.append(retrieval_result)

            self.logger.info(
                f"Retrieved {len(retrieval_results)} results for {expert_domain.value} expert"
            )
            return retrieval_results

        except Exception as e:
            self.logger.error(f"Knowledge retrieval failed: {e}")
            return []

    async def retrieve_cross_domain(
        self,
        query: str,
        max_results_per_domain: int = 3
    ) -> Dict[str, List[RetrievalResult]]:
        """跨領域知識檢索

        Args:
            query: 查詢內容
            max_results_per_domain: 每個領域的最大結果數

        Returns:
            按領域分組的檢索結果
        """
        results = {}

        for domain in ExpertDomain:
            if domain == ExpertDomain.GENERAL:
                continue

            domain_results = await self.retrieve_for_expert(
                query=query,
                expert_domain=domain,
                max_results=max_results_per_domain
            )
            results[domain.value] = domain_results

        return results

    def _enhance_query_for_domain(self, query: str, domain: ExpertDomain) -> str:
        """為特定領域增強查詢

        Linus 哲學：好品味的查詢增強
        - 基於關鍵字的簡單增強
        - 避免複雜的 NLP 處理
        """
        if domain == ExpertDomain.GENERAL:
            return query

        # 取得領域關鍵字
        domain_keywords = self.domain_keywords.get(domain, [])

        # 簡單的關鍵字匹配增強
        query_lower = query.lower()
        matched_keywords = [
            keyword for keyword in domain_keywords
            if any(word in query_lower for word in keyword.split())
        ]

        if matched_keywords:
            # 添加最相關的關鍵字到查詢中
            enhanced_query = f"{query} {' '.join(matched_keywords[:2])}"
        else:
            enhanced_query = query

        return enhanced_query

    def _create_retrieval_result(
        self,
        search_result: Dict[str, Any],
        expert_domain: ExpertDomain,
        original_query: str
    ) -> RetrievalResult:
        """建立結構化的檢索結果"""

        # 計算信心度（基於相似度和領域匹配度）
        similarity_score = search_result.get("similarity", 0.0)
        domain_relevance = self._calculate_domain_relevance(
            search_result["document"], expert_domain
        )
        confidence = (similarity_score * 0.7) + (domain_relevance * 0.3)

        # 取得來源資訊
        metadata = search_result.get("metadata", {})
        source = metadata.get("source", "未知來源")

        return RetrievalResult(
            content=search_result["document"],
            metadata=metadata,
            similarity_score=similarity_score,
            source=source,
            expert_domain=expert_domain.value,
            confidence=min(1.0, confidence)
        )

    def _calculate_domain_relevance(self, content: str, domain: ExpertDomain) -> float:
        """計算內容與領域的相關度

        Linus 哲學：簡潔執念
        - 基於關鍵字匹配的簡單演算法
        - 避免複雜的語言模型計算
        """
        if domain == ExpertDomain.GENERAL:
            return 0.5

        domain_keywords = self.domain_keywords.get(domain, [])
        if not domain_keywords:
            return 0.5

        content_lower = content.lower()
        matched_count = sum(
            1 for keyword in domain_keywords
            if keyword.lower() in content_lower
        )

        relevance = matched_count / len(domain_keywords)
        return min(1.0, relevance * 2)  # 放大相關度分數

    async def get_contextual_knowledge(
        self,
        query: str,
        context: Dict[str, Any],
        expert_domain: ExpertDomain
    ) -> List[RetrievalResult]:
        """取得上下文相關的知識

        Args:
            query: 查詢內容
            context: 上下文資訊（使用者資料、對話歷史等）
            expert_domain: 專家領域

        Returns:
            考慮上下文的檢索結果
        """
        # 基於上下文調整檢索策略
        adjusted_query = self._adjust_query_with_context(query, context)

        # 執行檢索
        results = await self.retrieve_for_expert(
            query=adjusted_query,
            expert_domain=expert_domain,
            max_results=5
        )

        # 基於上下文重新排序結果
        contextualized_results = self._rerank_with_context(results, context)

        return contextualized_results

    def _adjust_query_with_context(self, query: str, context: Dict[str, Any]) -> str:
        """基於上下文調整查詢"""
        adjusted_query = query

        # 如果有使用者年齡資訊，添加相關上下文
        user_profile = context.get("user_profile", {})
        age = user_profile.get("age")

        if age:
            if age < 30:
                adjusted_query += " 年輕人 長期投資"
            elif age > 50:
                adjusted_query += " 中年 退休規劃 保守投資"

        # 如果有風險偏好資訊
        risk_tolerance = user_profile.get("risk_tolerance")
        if risk_tolerance:
            adjusted_query += f" {risk_tolerance} 風險"

        return adjusted_query

    def _rerank_with_context(
        self,
        results: List[RetrievalResult],
        context: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """基於上下文重新排序結果"""
        # 簡單的重排序：基於上下文相關度調整信心度
        user_profile = context.get("user_profile", {})

        for result in results:
            context_boost = 0.0

            # 年齡相關度加成
            age = user_profile.get("age")
            if age:
                content_lower = result.content.lower()
                if age < 30 and any(word in content_lower for word in ["長期", "成長", "積極"]):
                    context_boost += 0.1
                elif age > 50 and any(word in content_lower for word in ["保守", "穩健", "退休"]):
                    context_boost += 0.1

            # 更新信心度
            result.confidence = min(1.0, result.confidence + context_boost)

        # 按信心度排序
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results

    def get_retriever_stats(self) -> Dict[str, Any]:
        """取得檢索器統計資訊"""
        try:
            collection_info = self.vector_store.get_collection_info()

            stats = {
                "collection_name": collection_info.get("name"),
                "total_documents": collection_info.get("document_count", 0),
                "expert_domains": len(self.domain_keywords),
                "total_keywords": sum(len(keywords) for keywords in self.domain_keywords.values())
            }

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get retriever stats: {e}")
            return {"error": str(e)}