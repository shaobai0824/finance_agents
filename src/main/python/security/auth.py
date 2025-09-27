"""
認證與授權模組
提供 JWT 認證、API 金鑰驗證和速率限制功能
"""

import os
import jwt
import time
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

class AuthConfig:
    """認證配置"""
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_DELTA = timedelta(hours=24)
    API_KEY_SALT = os.getenv("API_KEY_SALT", "dev-salt-change-in-production")

class TokenData(BaseModel):
    """JWT Token 資料模型"""
    user_id: str
    username: str
    scopes: list[str] = []
    exp: datetime

class RateLimiter:
    """簡單的記憶體速率限制器"""

    def __init__(self):
        self.requests = {}  # {client_id: [timestamp, ...]}
        self.limits = {
            "query": (60, 60),      # 每分鐘 60 次查詢
            "health": (300, 60),    # 每分鐘 300 次健康檢查
            "default": (100, 60)    # 每分鐘 100 次預設請求
        }

    def is_allowed(self, client_id: str, endpoint_type: str = "default") -> bool:
        """檢查是否允許請求"""
        now = time.time()
        max_requests, window_seconds = self.limits.get(endpoint_type, self.limits["default"])

        # 清理過期記錄
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if now - req_time < window_seconds
            ]
        else:
            self.requests[client_id] = []

        # 檢查是否超出限制
        if len(self.requests[client_id]) >= max_requests:
            return False

        # 記錄當前請求
        self.requests[client_id].append(now)
        return True

class JWTManager:
    """JWT 管理器"""

    @staticmethod
    def create_access_token(user_data: Dict[str, Any]) -> str:
        """建立存取令牌"""
        expire = datetime.now(timezone.utc) + AuthConfig.JWT_EXPIRATION_DELTA
        to_encode = user_data.copy()
        to_encode.update({"exp": expire})

        return jwt.encode(
            to_encode,
            AuthConfig.JWT_SECRET_KEY,
            algorithm=AuthConfig.JWT_ALGORITHM
        )

    @staticmethod
    def verify_token(token: str) -> TokenData:
        """驗證並解析令牌"""
        try:
            payload = jwt.decode(
                token,
                AuthConfig.JWT_SECRET_KEY,
                algorithms=[AuthConfig.JWT_ALGORITHM]
            )

            return TokenData(
                user_id=payload.get("user_id"),
                username=payload.get("username"),
                scopes=payload.get("scopes", []),
                exp=datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的認證令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

class APIKeyManager:
    """API 金鑰管理器"""

    @staticmethod
    def generate_api_key(user_id: str) -> str:
        """生成 API 金鑰"""
        data = f"{user_id}:{time.time()}:{AuthConfig.API_KEY_SALT}"
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """驗證 API 金鑰（簡化版，實際應查詢資料庫）"""
        # TODO: 實作資料庫查詢
        return len(api_key) == 64 and api_key.isalnum()

class SecurityMiddleware:
    """安全中介軟體"""

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.security = HTTPBearer(auto_error=False)

    def get_client_id(self, request: Request) -> str:
        """取得客戶端 ID（用於速率限制）"""
        # 優先使用 X-Forwarded-For，否則使用 client IP
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"
        return client_ip

    def check_rate_limit(self, request: Request, endpoint_type: str = "default") -> bool:
        """檢查速率限制"""
        client_id = self.get_client_id(request)
        return self.rate_limiter.is_allowed(client_id, endpoint_type)

    async def verify_auth(self, request: Request) -> Optional[TokenData]:
        """驗證認證（JWT 或 API 金鑰）"""
        # 檢查 Authorization header
        credentials: HTTPAuthorizationCredentials = await self.security(request)

        if not credentials:
            return None

        token = credentials.credentials

        # 嘗試 JWT 驗證
        try:
            return JWTManager.verify_token(token)
        except HTTPException:
            pass

        # 嘗試 API 金鑰驗證
        if APIKeyManager.validate_api_key(token):
            return TokenData(
                user_id="api_user",
                username="api_user",
                scopes=["api_access"]
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證憑證",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 全域安全管理器實例
security_manager = SecurityMiddleware()

def require_auth():
    """需要認證的依賴項"""
    async def auth_dependency(request: Request):
        return await security_manager.verify_auth(request)
    return auth_dependency

def check_rate_limit(endpoint_type: str = "default"):
    """檢查速率限制的依賴項"""
    def rate_limit_dependency(request: Request):
        if not security_manager.check_rate_limit(request, endpoint_type):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="請求過於頻繁，請稍後再試"
            )
        return True
    return rate_limit_dependency