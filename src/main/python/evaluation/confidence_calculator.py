"""
智能信心度計算系統

改進信心度計算，基於多維度分析而非簡單規則
Linus 哲學：好品味的演算法，消除固定加成的特殊情況
"""

import re
import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceMetrics:
    """信心度計算指標"""
    relevance_score: float = 0.0      # 語意相關性分數 (0-1)
    response_quality: float = 0.0     # 回應品質分數 (0-1)
    knowledge_coverage: float = 0.0   # 知識覆蓋度 (0-1)
    domain_expertise: float = 0.0     # 領域專業度 (0-1)
    data_freshness: float = 0.0       # 資料新鮮度 (0-1)
    source_authority: float = 0.0     # 來源權威性 (0-1)

    @property
    def overall_confidence(self) -> float:
        """計算總體信心度"""
        # 權重配置（可調整）
        weights = {
            'relevance': 0.3,      # 語意相關性最重要
            'quality': 0.25,       # 回應品質次之
            'coverage': 0.2,       # 知識覆蓋度
            'expertise': 0.15,     # 領域專業度
            'freshness': 0.05,     # 資料新鮮度
            'authority': 0.05      # 來源權威性
        }

        score = (
            weights['relevance'] * self.relevance_score +
            weights['quality'] * self.response_quality +
            weights['coverage'] * self.knowledge_coverage +
            weights['expertise'] * self.domain_expertise +
            weights['freshness'] * self.data_freshness +
            weights['authority'] * self.source_authority
        )

        return min(0.99, max(0.1, score))  # 確保在合理範圍內


class SmartConfidenceCalculator:
    """智能信心度計算器

    Linus 哲學應用：
    - 好品味：用數據驅動的方法替代硬編碼規則
    - 實用主義：專注解決實際的信心度評估問題
    - 簡潔執念：清晰的評分邏輯，避免複雜公式
    """

    def __init__(self):
        # 領域關鍵字權重表
        self.domain_keywords = {
            'financial_planner': {
                'high': ['理財規劃', '資產配置', '風險評估', '退休規劃', '保險規劃'],
                'medium': ['投資', '儲蓄', '基金', '股票', '債券'],
                'low': ['金融', '財務', '投資建議']
            },
            'financial_analyst': {
                'high': ['技術分析', '財報分析', '股價預測', '市場分析', '投資分析'],
                'medium': ['股票', '市場', '經濟', '產業', '公司'],
                'low': ['分析', '數據', '趨勢']
            },
            'legal_expert': {
                'high': ['法規遵循', '稅務規劃', '投資法規', '金融法'],
                'medium': ['法律', '稅務', '合規', '監管'],
                'low': ['規範', '條文', '法規']
            }
        }

        # 品質指標關鍵字
        self.quality_indicators = {
            'professional': ['建議', '分析', '評估', '策略', '規劃', '建議您'],
            'detailed': ['具體', '詳細', '明確', '清楚', '完整'],
            'actionable': ['可以', '應該', '建議', '考慮', '執行'],
            'structured': ['首先', '其次', '最後', '步驟', '階段']
        }

    async def calculate_confidence(
        self,
        query: str,
        response_content: str,
        knowledge_results: List[Dict],
        agent_type: str,
        personal_context: Dict[str, Any] = None
    ) -> ConfidenceMetrics:
        """計算智能信心度

        Args:
            query: 使用者查詢
            response_content: 代理人回應內容
            knowledge_results: RAG 檢索結果
            agent_type: 代理人類型
            personal_context: 個人上下文

        Returns:
            ConfidenceMetrics: 詳細的信心度指標
        """

        metrics = ConfidenceMetrics()

        # 1. 語意相關性評分
        metrics.relevance_score = await self._calculate_relevance_score(
            query, knowledge_results
        )

        # 2. 回應品質分析
        metrics.response_quality = self._analyze_response_quality(
            query, response_content
        )

        # 3. 知識覆蓋度評估
        metrics.knowledge_coverage = self._evaluate_knowledge_coverage(
            query, knowledge_results
        )

        # 4. 領域專業度匹配
        metrics.domain_expertise = self._assess_domain_expertise(
            query, agent_type
        )

        # 5. 資料新鮮度評估
        metrics.data_freshness = self._evaluate_data_freshness(
            knowledge_results
        )

        # 6. 來源權威性評估
        metrics.source_authority = self._assess_source_authority(
            knowledge_results
        )

        logger.info(f"Confidence calculation for {agent_type}: "
                   f"relevance={metrics.relevance_score:.2f}, "
                   f"quality={metrics.response_quality:.2f}, "
                   f"overall={metrics.overall_confidence:.2f}")

        return metrics

    async def _calculate_relevance_score(
        self,
        query: str,
        knowledge_results: List[Dict]
    ) -> float:
        """計算語意相關性分數

        基於檢索結果與查詢的相關性分數
        """
        if not knowledge_results:
            return 0.3  # 無知識檢索的基礎分數

        # 提取相關性分數
        relevance_scores = []
        for result in knowledge_results:
            # 從 ChromaDB 的距離轉換為相關性分數
            distance = result.get('distance', 1.0)
            relevance = max(0, 1.0 - distance)  # 距離越小，相關性越高
            relevance_scores.append(relevance)

        if not relevance_scores:
            return 0.4

        # 使用加權平均：前面的結果權重更高
        weighted_scores = []
        for i, score in enumerate(relevance_scores[:5]):  # 只考慮前5個結果
            weight = 1.0 / (i + 1)  # 權重遞減
            weighted_scores.append(score * weight)

        avg_relevance = sum(weighted_scores) / sum(1.0/(i+1) for i in range(len(weighted_scores)))

        # 標準化到 0.2-0.95 範圍
        normalized_score = 0.2 + (avg_relevance * 0.75)

        return min(0.95, max(0.2, normalized_score))

    def _analyze_response_quality(self, query: str, response_content: str) -> float:
        """分析回應品質

        基於回應的專業性、完整性、可操作性等因素
        """
        if not response_content or len(response_content) < 50:
            return 0.2

        quality_score = 0.0

        # 1. 專業詞彙使用 (0.3 權重)
        professional_count = sum(
            1 for word in self.quality_indicators['professional']
            if word in response_content
        )
        professional_score = min(1.0, professional_count / 3) * 0.3
        quality_score += professional_score

        # 2. 詳細程度 (0.25 權重)
        detailed_count = sum(
            1 for word in self.quality_indicators['detailed']
            if word in response_content
        )
        detailed_score = min(1.0, detailed_count / 2) * 0.25
        quality_score += detailed_score

        # 3. 可操作性 (0.25 權重)
        actionable_count = sum(
            1 for word in self.quality_indicators['actionable']
            if word in response_content
        )
        actionable_score = min(1.0, actionable_count / 3) * 0.25
        quality_score += actionable_score

        # 4. 結構化程度 (0.2 權重)
        structured_count = sum(
            1 for word in self.quality_indicators['structured']
            if word in response_content
        )
        structured_score = min(1.0, structured_count / 2) * 0.2
        quality_score += structured_score

        # 5. 長度適中性調整
        length = len(response_content)
        if 200 <= length <= 1000:
            quality_score += 0.1  # 適中長度加分
        elif length < 100:
            quality_score *= 0.8  # 太短扣分
        elif length > 2000:
            quality_score *= 0.9  # 太長略扣分

        return min(0.95, max(0.1, quality_score))

    def _evaluate_knowledge_coverage(
        self,
        query: str,
        knowledge_results: List[Dict]
    ) -> float:
        """評估知識覆蓋度

        基於檢索到的知識量和多樣性
        """
        if not knowledge_results:
            return 0.2

        # 1. 數量評分 (0.4 權重)
        count_score = min(1.0, len(knowledge_results) / 5) * 0.4

        # 2. 來源多樣性 (0.3 權重)
        unique_sources = len(set(
            result.get('source', 'unknown')
            for result in knowledge_results
        ))
        diversity_score = min(1.0, unique_sources / 3) * 0.3

        # 3. 內容長度 (0.3 權重)
        total_content_length = sum(
            len(result.get('document', ''))
            for result in knowledge_results
        )
        content_score = min(1.0, total_content_length / 2000) * 0.3

        coverage_score = count_score + diversity_score + content_score

        return min(0.9, max(0.1, coverage_score))

    def _assess_domain_expertise(self, query: str, agent_type: str) -> float:
        """評估領域專業度匹配

        基於查詢內容與代理人專業領域的匹配度
        """
        if agent_type not in self.domain_keywords:
            return 0.5  # 未知代理人類型

        query_lower = query.lower()
        keywords = self.domain_keywords[agent_type]

        # 高價值關鍵字匹配
        high_matches = sum(
            1 for keyword in keywords['high']
            if keyword in query_lower
        )

        # 中等價值關鍵字匹配
        medium_matches = sum(
            1 for keyword in keywords['medium']
            if keyword in query_lower
        )

        # 低價值關鍵字匹配
        low_matches = sum(
            1 for keyword in keywords['low']
            if keyword in query_lower
        )

        # 加權計算
        expertise_score = (
            high_matches * 0.6 +
            medium_matches * 0.3 +
            low_matches * 0.1
        ) / 3  # 標準化

        return min(0.95, max(0.3, expertise_score))

    def _evaluate_data_freshness(self, knowledge_results: List[Dict]) -> float:
        """評估資料新鮮度

        基於知識來源的時間戳記
        """
        if not knowledge_results:
            return 0.5

        current_time = datetime.now()
        freshness_scores = []

        for result in knowledge_results:
            # 嘗試從 metadata 中提取時間戳記
            timestamp_str = result.get('metadata', {}).get('timestamp')
            if not timestamp_str:
                # 如果沒有時間戳記，假設為中等新鮮度
                freshness_scores.append(0.6)
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                days_old = (current_time - timestamp).days

                # 新鮮度評分邏輯
                if days_old <= 30:
                    freshness = 1.0
                elif days_old <= 90:
                    freshness = 0.8
                elif days_old <= 365:
                    freshness = 0.6
                else:
                    freshness = 0.3

                freshness_scores.append(freshness)

            except (ValueError, TypeError):
                freshness_scores.append(0.5)

        return sum(freshness_scores) / len(freshness_scores) if freshness_scores else 0.5

    def _assess_source_authority(self, knowledge_results: List[Dict]) -> float:
        """評估來源權威性

        基於資料來源的可信度
        """
        if not knowledge_results:
            return 0.5

        authority_scores = []

        # 權威來源清單（可擴展）
        high_authority = ['中央銀行', '金管會', '財政部', '證交所', '投信投顧']
        medium_authority = ['銀行', '券商', '投信', '會計師', '理財專家']

        for result in knowledge_results:
            source = result.get('source', '').lower()

            # 判斷來源權威性
            if any(auth in source for auth in high_authority):
                authority_scores.append(0.9)
            elif any(auth in source for auth in medium_authority):
                authority_scores.append(0.7)
            else:
                authority_scores.append(0.5)  # 一般來源

        return sum(authority_scores) / len(authority_scores) if authority_scores else 0.5


# 全域計算器實例
confidence_calculator = SmartConfidenceCalculator()