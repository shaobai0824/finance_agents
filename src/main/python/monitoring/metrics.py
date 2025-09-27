"""
監控和指標收集模組
提供系統效能監控、請求追蹤和業務指標統計
"""

import time
import psutil
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

@dataclass
class RequestMetric:
    """請求指標"""
    timestamp: float
    endpoint: str
    method: str
    status_code: int
    response_time: float
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class SystemMetric:
    """系統指標"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_percent: float
    active_sessions: int
    total_requests: int

@dataclass
class BusinessMetric:
    """業務指標"""
    timestamp: float
    total_queries: int
    successful_queries: int
    failed_queries: int
    average_confidence: float
    expert_usage: Dict[str, int]
    active_users: int

class MetricsCollector:
    """指標收集器"""

    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.request_metrics: deque = deque(maxlen=max_metrics)
        self.system_metrics: deque = deque(maxlen=max_metrics)
        self.business_metrics: deque = deque(maxlen=max_metrics)

        # 計數器
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)

        # 快取
        self._last_system_check = 0
        self._cached_system_metrics = None

        self.logger = logging.getLogger(__name__)

    def record_request(self,
                      endpoint: str,
                      method: str,
                      status_code: int,
                      response_time: float,
                      user_id: Optional[str] = None,
                      session_id: Optional[str] = None):
        """記錄請求指標"""
        metric = RequestMetric(
            timestamp=time.time(),
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            user_id=user_id,
            session_id=session_id
        )
        self.request_metrics.append(metric)

        # 更新計數器
        self.counters[f"requests_total"] += 1
        self.counters[f"requests_{endpoint}"] += 1
        self.counters[f"status_{status_code}"] += 1

        # 記錄回應時間
        self.timers[f"response_time_{endpoint}"].append(response_time)

    def record_system_metrics(self):
        """記錄系統指標"""
        now = time.time()

        # 避免頻繁查詢系統資源（快取 5 秒）
        if now - self._last_system_check < 5:
            return self._cached_system_metrics

        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            metric = SystemMetric(
                timestamp=now,
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                disk_percent=disk.percent,
                active_sessions=self.counters.get("active_sessions", 0),
                total_requests=self.counters.get("requests_total", 0)
            )

            self.system_metrics.append(metric)
            self._last_system_check = now
            self._cached_system_metrics = metric

            return metric

        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return None

    def record_business_metrics(self,
                              total_queries: int,
                              successful_queries: int,
                              failed_queries: int,
                              average_confidence: float,
                              expert_usage: Dict[str, int],
                              active_users: int):
        """記錄業務指標"""
        metric = BusinessMetric(
            timestamp=time.time(),
            total_queries=total_queries,
            successful_queries=successful_queries,
            failed_queries=failed_queries,
            average_confidence=average_confidence,
            expert_usage=expert_usage,
            active_users=active_users
        )
        self.business_metrics.append(metric)

    def get_summary_stats(self, minutes: int = 5) -> Dict[str, Any]:
        """取得摘要統計（過去 N 分鐘）"""
        cutoff_time = time.time() - (minutes * 60)

        # 過濾最近的請求
        recent_requests = [
            req for req in self.request_metrics
            if req.timestamp >= cutoff_time
        ]

        if not recent_requests:
            return {
                "time_window_minutes": minutes,
                "total_requests": 0,
                "avg_response_time": 0,
                "error_rate": 0,
                "requests_per_minute": 0
            }

        # 計算統計數據
        total_requests = len(recent_requests)
        response_times = [req.response_time for req in recent_requests]
        error_count = len([req for req in recent_requests if req.status_code >= 400])

        avg_response_time = sum(response_times) / len(response_times)
        error_rate = error_count / total_requests if total_requests > 0 else 0
        requests_per_minute = total_requests / minutes

        # 端點統計
        endpoint_stats = defaultdict(int)
        for req in recent_requests:
            endpoint_stats[req.endpoint] += 1

        return {
            "time_window_minutes": minutes,
            "total_requests": total_requests,
            "avg_response_time": round(avg_response_time, 3),
            "error_rate": round(error_rate, 3),
            "requests_per_minute": round(requests_per_minute, 2),
            "endpoint_breakdown": dict(endpoint_stats),
            "system_metrics": asdict(self._cached_system_metrics) if self._cached_system_metrics else None
        }

    def get_health_score(self) -> Dict[str, Any]:
        """計算系統健康評分"""
        stats = self.get_summary_stats(minutes=5)
        system_metric = self.record_system_metrics()

        # 健康評分因子
        scores = {}

        # 回應時間評分 (0-100)
        avg_response_time = stats.get("avg_response_time", 0)
        if avg_response_time < 1.0:
            scores["response_time"] = 100
        elif avg_response_time < 5.0:
            scores["response_time"] = 80
        elif avg_response_time < 10.0:
            scores["response_time"] = 60
        else:
            scores["response_time"] = 40

        # 錯誤率評分 (0-100)
        error_rate = stats.get("error_rate", 0)
        if error_rate == 0:
            scores["error_rate"] = 100
        elif error_rate < 0.01:
            scores["error_rate"] = 90
        elif error_rate < 0.05:
            scores["error_rate"] = 70
        else:
            scores["error_rate"] = 50

        # 系統資源評分 (0-100)
        if system_metric:
            cpu_score = max(0, 100 - system_metric.cpu_percent)
            memory_score = max(0, 100 - system_metric.memory_percent)
            scores["system_resources"] = (cpu_score + memory_score) / 2
        else:
            scores["system_resources"] = 0

        # 整體健康評分
        overall_score = sum(scores.values()) / len(scores)

        # 健康狀態
        if overall_score >= 90:
            health_status = "excellent"
        elif overall_score >= 75:
            health_status = "good"
        elif overall_score >= 60:
            health_status = "degraded"
        else:
            health_status = "critical"

        return {
            "overall_score": round(overall_score, 1),
            "health_status": health_status,
            "component_scores": scores,
            "recommendations": self._get_health_recommendations(scores)
        }

    def _get_health_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """根據評分提供改善建議"""
        recommendations = []

        if scores.get("response_time", 100) < 70:
            recommendations.append("建議優化 API 回應時間，檢查資料庫查詢和外部服務調用")

        if scores.get("error_rate", 100) < 80:
            recommendations.append("錯誤率偏高，建議檢查錯誤日誌並修復問題")

        if scores.get("system_resources", 100) < 70:
            recommendations.append("系統資源使用率偏高，建議檢查 CPU 和記憶體使用情況")

        return recommendations

    def export_metrics(self, format: str = "json") -> Dict[str, Any]:
        """匯出指標資料"""
        return {
            "collection_time": datetime.now().isoformat(),
            "summary_stats": self.get_summary_stats(),
            "health_score": self.get_health_score(),
            "total_metrics_collected": {
                "requests": len(self.request_metrics),
                "system": len(self.system_metrics),
                "business": len(self.business_metrics)
            }
        }

# 全域指標收集器
metrics_collector = MetricsCollector()