"""
RAG 使用情況即時監控系統

提供即時的 RAG 使用統計、效能分析和異常檢測
"""

import asyncio
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class RAGUsageMetrics:
    """RAG 使用情況指標"""
    agent_name: str
    query: str
    knowledge_retrieved: int
    retrieval_time: float
    relevance_scores: List[float]
    embedding_time: float
    total_processing_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None

    @property
    def avg_relevance_score(self) -> float:
        """平均相關性分數"""
        return sum(self.relevance_scores) / len(self.relevance_scores) if self.relevance_scores else 0.0

    @property
    def is_effective(self) -> bool:
        """判斷 RAG 是否有效使用"""
        return self.knowledge_retrieved > 0 and self.avg_relevance_score > 0.5


class RAGMonitor:
    """RAG 使用情況監控器"""

    def __init__(self):
        self.metrics_history: List[RAGUsageMetrics] = []
        self.agent_stats: Dict[str, Dict] = defaultdict(lambda: {
            'total_queries': 0,
            'successful_retrievals': 0,
            'avg_retrieval_time': 0.0,
            'avg_relevance': 0.0,
            'total_knowledge_used': 0
        })
        self.session_tracking: Dict[str, List[RAGUsageMetrics]] = defaultdict(list)

    def record_usage(self, metrics: RAGUsageMetrics):
        """記錄 RAG 使用情況"""
        self.metrics_history.append(metrics)

        if metrics.session_id:
            self.session_tracking[metrics.session_id].append(metrics)

        # 更新代理人統計
        stats = self.agent_stats[metrics.agent_name]
        stats['total_queries'] += 1

        if metrics.knowledge_retrieved > 0:
            stats['successful_retrievals'] += 1
            stats['total_knowledge_used'] += metrics.knowledge_retrieved

            # 更新平均值
            n = stats['successful_retrievals']
            stats['avg_retrieval_time'] = (
                (stats['avg_retrieval_time'] * (n-1) + metrics.retrieval_time) / n
            )
            stats['avg_relevance'] = (
                (stats['avg_relevance'] * (n-1) + metrics.avg_relevance_score) / n
            )

        logger.info(f"RAG usage recorded for {metrics.agent_name}: "
                   f"{metrics.knowledge_retrieved} docs in {metrics.retrieval_time:.2f}s")

    def get_agent_efficiency(self, agent_name: str) -> Dict[str, Any]:
        """獲取特定代理人的 RAG 使用效率"""
        stats = self.agent_stats[agent_name]

        if stats['total_queries'] == 0:
            return {"error": f"No data for agent {agent_name}"}

        success_rate = stats['successful_retrievals'] / stats['total_queries']

        return {
            "agent_name": agent_name,
            "total_queries": stats['total_queries'],
            "success_rate": success_rate,
            "avg_retrieval_time": stats['avg_retrieval_time'],
            "avg_relevance_score": stats['avg_relevance'],
            "total_knowledge_used": stats['total_knowledge_used'],
            "efficiency_rating": self._calculate_efficiency_rating(stats, success_rate)
        }

    def _calculate_efficiency_rating(self, stats: Dict, success_rate: float) -> str:
        """計算效率評級"""
        if success_rate < 0.3:
            return "🔴 低效率"
        elif success_rate < 0.7:
            return "🟡 中等效率"
        elif stats['avg_relevance'] > 0.8 and stats['avg_retrieval_time'] < 2.0:
            return "🟢 高效率"
        else:
            return "🔵 良好"

    def get_session_analysis(self, session_id: str) -> Dict[str, Any]:
        """分析特定會話的 RAG 使用情況"""
        session_metrics = self.session_tracking.get(session_id, [])

        if not session_metrics:
            return {"error": f"No data for session {session_id}"}

        total_queries = len(session_metrics)
        successful_queries = sum(1 for m in session_metrics if m.is_effective)
        total_knowledge = sum(m.knowledge_retrieved for m in session_metrics)
        avg_processing_time = sum(m.total_processing_time for m in session_metrics) / total_queries

        # 找出最有效和最無效的查詢
        most_effective = max(session_metrics, key=lambda m: m.avg_relevance_score)
        least_effective = min(session_metrics, key=lambda m: m.avg_relevance_score)

        return {
            "session_id": session_id,
            "total_queries": total_queries,
            "effective_queries": successful_queries,
            "effectiveness_rate": successful_queries / total_queries,
            "total_knowledge_retrieved": total_knowledge,
            "avg_processing_time": avg_processing_time,
            "agents_used": list(set(m.agent_name for m in session_metrics)),
            "most_effective_query": {
                "query": most_effective.query[:50] + "...",
                "relevance": most_effective.avg_relevance_score,
                "agent": most_effective.agent_name
            },
            "least_effective_query": {
                "query": least_effective.query[:50] + "...",
                "relevance": least_effective.avg_relevance_score,
                "agent": least_effective.agent_name
            }
        }

    def get_system_health(self) -> Dict[str, Any]:
        """獲取系統健康狀況"""
        if not self.metrics_history:
            return {"status": "no_data", "message": "尚無 RAG 使用數據"}

        # 最近1小時的數據
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > recent_cutoff]

        if not recent_metrics:
            return {"status": "inactive", "message": "最近1小時無 RAG 活動"}

        # 計算健康指標
        total_recent = len(recent_metrics)
        effective_recent = sum(1 for m in recent_metrics if m.is_effective)
        avg_response_time = sum(m.total_processing_time for m in recent_metrics) / total_recent

        # 檢測異常
        anomalies = []

        # 響應時間異常
        if avg_response_time > 5.0:
            anomalies.append("響應時間過長")

        # 效率異常
        if effective_recent / total_recent < 0.5:
            anomalies.append("RAG 效率偏低")

        # 無知識檢索異常
        no_retrieval_count = sum(1 for m in recent_metrics if m.knowledge_retrieved == 0)
        if no_retrieval_count / total_recent > 0.3:
            anomalies.append("知識檢索失敗率過高")

        status = "healthy" if not anomalies else "warning"

        return {
            "status": status,
            "recent_queries": total_recent,
            "effectiveness_rate": effective_recent / total_recent,
            "avg_response_time": avg_response_time,
            "anomalies": anomalies,
            "active_agents": list(set(m.agent_name for m in recent_metrics)),
            "message": "系統運行正常" if status == "healthy" else f"發現 {len(anomalies)} 個異常"
        }

    def generate_daily_report(self) -> Dict[str, Any]:
        """生成每日 RAG 使用報告"""
        # 最近24小時的數據
        cutoff = datetime.now() - timedelta(days=1)
        daily_metrics = [m for m in self.metrics_history if m.timestamp > cutoff]

        if not daily_metrics:
            return {"error": "最近24小時無數據"}

        # 按代理人分組統計
        agent_performance = {}
        for agent_name in set(m.agent_name for m in daily_metrics):
            agent_metrics = [m for m in daily_metrics if m.agent_name == agent_name]
            agent_performance[agent_name] = {
                "queries": len(agent_metrics),
                "effective_queries": sum(1 for m in agent_metrics if m.is_effective),
                "total_knowledge": sum(m.knowledge_retrieved for m in agent_metrics),
                "avg_relevance": sum(m.avg_relevance_score for m in agent_metrics) / len(agent_metrics)
            }

        # 整體統計
        total_queries = len(daily_metrics)
        effective_queries = sum(1 for m in daily_metrics if m.is_effective)
        total_knowledge_retrieved = sum(m.knowledge_retrieved for m in daily_metrics)

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_queries": total_queries,
            "effective_queries": effective_queries,
            "effectiveness_rate": effective_queries / total_queries,
            "total_knowledge_retrieved": total_knowledge_retrieved,
            "avg_knowledge_per_query": total_knowledge_retrieved / total_queries,
            "agent_performance": agent_performance,
            "top_performing_agent": max(agent_performance.items(),
                                      key=lambda x: x[1]["avg_relevance"])[0] if agent_performance else None
        }


# 全域監控器實例
rag_monitor = RAGMonitor()


def track_rag_usage(agent_name: str, session_id: Optional[str] = None):
    """裝飾器：自動追蹤 RAG 使用情況"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # 從結果中提取 RAG 相關資訊
                if hasattr(result, 'metadata') and result.metadata:
                    knowledge_used = result.metadata.get('knowledge_used', 0)
                    relevance_scores = result.metadata.get('relevance_scores', [])
                    retrieval_time = result.metadata.get('retrieval_time', 0.0)
                    embedding_time = result.metadata.get('embedding_time', 0.0)
                    query = args[0].content if args and hasattr(args[0], 'content') else str(args)[:100]

                    total_time = time.time() - start_time

                    metrics = RAGUsageMetrics(
                        agent_name=agent_name,
                        query=query,
                        knowledge_retrieved=knowledge_used,
                        retrieval_time=retrieval_time,
                        relevance_scores=relevance_scores,
                        embedding_time=embedding_time,
                        total_processing_time=total_time,
                        session_id=session_id
                    )

                    rag_monitor.record_usage(metrics)

                return result

            except Exception as e:
                # 記錄失敗情況
                total_time = time.time() - start_time
                query = args[0].content if args and hasattr(args[0], 'content') else str(args)[:100]

                metrics = RAGUsageMetrics(
                    agent_name=agent_name,
                    query=query,
                    knowledge_retrieved=0,
                    retrieval_time=0.0,
                    relevance_scores=[],
                    embedding_time=0.0,
                    total_processing_time=total_time,
                    session_id=session_id
                )

                rag_monitor.record_usage(metrics)
                raise e

        return wrapper
    return decorator