"""
API 資料模型

實作 Linus 哲學：
1. 好品味：清晰的資料模型，避免冗餘欄位
2. Never break userspace：穩定的 API 契約
3. 簡潔執念：只包含必要的欄位
4. 資料結構優先：API 設計以資料結構為核心
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RiskTolerance(str, Enum):
    """風險承受度枚舉"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class QueryRequest(BaseModel):
    """諮詢請求模型"""
    query: str = Field(..., description="使用者查詢內容", min_length=1, max_length=1000)
    user_profile: Optional[Dict[str, Any]] = Field(None, description="使用者資料")
    session_id: Optional[str] = Field(None, description="會話 ID")

    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('查詢內容不能為空')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "query": "我想要投資建議，有什麼推薦的投資組合嗎？",
                "user_profile": {
                    "age": 30,
                    "risk_tolerance": "moderate",
                    "income_level": "middle"
                }
            }
        }


class UserProfile(BaseModel):
    """使用者資料模型"""
    age: Optional[int] = Field(None, description="年齡", ge=18, le=100)
    risk_tolerance: Optional[RiskTolerance] = Field(None, description="風險承受度")
    income_level: Optional[str] = Field(None, description="收入水平")
    investment_experience: Optional[str] = Field(None, description="投資經驗")
    financial_goals: Optional[List[str]] = Field(None, description="理財目標")

    class Config:
        json_schema_extra = {
            "example": {
                "age": 35,
                "risk_tolerance": "moderate",
                "income_level": "middle",
                "investment_experience": "beginner",
                "financial_goals": ["retirement_planning", "wealth_building"]
            }
        }


class ExpertResponse(BaseModel):
    """專家回應模型"""
    expert_type: str = Field(..., description="專家類型")
    content: str = Field(..., description="回應內容")
    confidence: float = Field(..., description="信心度", ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list, description="資料來源")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元資料")


class QueryResponse(BaseModel):
    """諮詢回應模型

    Linus 哲學：好品味的回應結構
    - 包含所有必要資訊
    - 支援透明度要求（來源追蹤）
    - 結構化的專家回應
    """
    session_id: str = Field(..., description="會話 ID")
    query: str = Field(..., description="原始查詢")
    final_response: str = Field(..., description="最終回應")
    confidence_score: float = Field(..., description="整體信心度", ge=0.0, le=1.0)
    expert_responses: List[ExpertResponse] = Field(default_factory=list, description="專家回應清單")
    sources: List[str] = Field(default_factory=list, description="資料來源清單")
    processing_time: float = Field(..., description="處理時間（秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="回應時間")
    status: str = Field(..., description="處理狀態")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "query": "我想要投資建議",
                "final_response": "基於您的風險偏好，建議以下投資組合...",
                "confidence_score": 0.85,
                "expert_responses": [
                    {
                        "expert_type": "financial_planner",
                        "content": "理財規劃建議...",
                        "confidence": 0.9,
                        "sources": ["理財專家知識庫"],
                        "metadata": {"advice_type": "investment_advice"}
                    }
                ],
                "sources": ["理財專家知識庫", "投資組合理論"],
                "processing_time": 2.5,
                "timestamp": "2025-01-26T10:00:00",
                "status": "completed"
            }
        }


class ErrorResponse(BaseModel):
    """錯誤回應模型"""
    error_code: str = Field(..., description="錯誤代碼")
    error_message: str = Field(..., description="錯誤訊息")
    details: Optional[Dict[str, Any]] = Field(None, description="錯誤詳情")
    timestamp: datetime = Field(default_factory=datetime.now, description="錯誤時間")

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "PROCESSING_ERROR",
                "error_message": "查詢處理時發生錯誤",
                "details": {"internal_error": "Agent processing failed"},
                "timestamp": "2025-01-26T10:00:00"
            }
        }


class HealthCheckResponse(BaseModel):
    """健康檢查回應模型"""
    status: str = Field(..., description="服務狀態")
    version: str = Field(..., description="API 版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="檢查時間")
    services: Dict[str, str] = Field(default_factory=dict, description="各服務狀態")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2025-01-26T10:00:00",
                "services": {
                    "database": "healthy",
                    "vector_store": "healthy",
                    "agents": "healthy"
                }
            }
        }


class SessionInfo(BaseModel):
    """會話資訊模型"""
    session_id: str = Field(..., description="會話 ID")
    created_at: datetime = Field(..., description="建立時間")
    last_activity: datetime = Field(..., description="最後活動時間")
    query_count: int = Field(..., description="查詢次數")
    status: str = Field(..., description="會話狀態")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-01-26T09:00:00",
                "last_activity": "2025-01-26T10:00:00",
                "query_count": 3,
                "status": "active"
            }
        }


class WorkflowStatus(BaseModel):
    """工作流程狀態模型"""
    session_id: str = Field(..., description="會話 ID")
    status: str = Field(..., description="工作流程狀態")
    current_step: str = Field(..., description="當前步驟")
    progress: float = Field(..., description="進度百分比", ge=0.0, le=1.0)
    estimated_completion: Optional[datetime] = Field(None, description="預估完成時間")
    error_messages: List[str] = Field(default_factory=list, description="錯誤訊息清單")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "current_step": "expert_consultation",
                "progress": 0.6,
                "estimated_completion": "2025-01-26T10:02:00",
                "error_messages": []
            }
        }