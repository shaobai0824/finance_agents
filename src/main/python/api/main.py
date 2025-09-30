"""
FastAPI 主應用程式

實作 Linus 哲學：
1. 簡潔執念：清晰的 API 結構，避免過度複雜
2. Never break userspace：穩定的 API 端點，向後兼容
3. 實用主義：專注解決實際的理財諮詢需求
4. 好品味：統一的錯誤處理和回應格式
"""

import asyncio
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

# 載入環境變數
from dotenv import load_dotenv
load_dotenv()

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from ..workflow.finance_workflow_llm import FinanceWorkflowLLM
from ..rag import ChromaVectorStore, KnowledgeRetriever
from ..rag.enhanced_vector_store import EnhancedVectorStore
from ..memory import ConversationMemory, MessageRole
from .models import (ErrorResponse, HealthCheckResponse, QueryRequest,
                     QueryResponse, SessionInfo, WorkflowStatus)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全域變數（在生產環境中應該使用依賴注入）
finance_workflow = None
vector_store = None
knowledge_retriever = None
active_sessions: Dict[str, Dict[str, Any]] = {}
# 會話記憶管理
session_memories: Dict[str, Any] = {}  # session_id -> ConversationMemory


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理
    
    Linus 哲學：簡潔的初始化
    - 明確的初始化順序
    - 容錯處理
    """
    global finance_workflow, vector_store, knowledge_retriever
    
    # 啟動事件
    try:
        logger.info("Starting Finance Agents API...")

        # 初始化增強型向量存儲 (文章感知RAG)
        logger.info("Initializing Enhanced Vector Store with semantic chunking...")
        vector_store = EnhancedVectorStore(
            collection_name="finance_knowledge_enhanced",
            enable_semantic_chunking=True,
            fallback_to_legacy=True
        )

        # 初始化知識檢索器
        logger.info("Initializing knowledge retriever...")
        knowledge_retriever = KnowledgeRetriever(vector_store)

        # 初始化理財工作流程
        logger.info("Initializing finance workflow...")
        finance_workflow = FinanceWorkflowLLM()

        logger.info("Finance Agents API started successfully!")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # 關閉事件
    logger.info("Shutting down Finance Agents API...")


# 建立 FastAPI 應用
app = FastAPI(
    title="Finance Agents API",
    description="多代理人理財諮詢服務 API - 基於 LangGraph + OpenAI + ChromaDB",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全域變數（在生產環境中應該使用依賴注入）
active_sessions: Dict[str, Dict[str, Any]] = {}


# 錯誤處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 例外處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=f"HTTP_{exc.status_code}",
            error_message=str(exc.detail),
            details={"path": str(request.url)}
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """一般例外處理器"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            error_message="內部伺服器錯誤",
            details={"path": str(request.url)}
        ).dict()
    )


# API 路由
@app.get("/", response_model=Dict[str, str])
async def root():
    """根端點"""
    return {
        "service": "Finance Agents API",
        "version": "1.0.0",
        "description": "多代理人理財諮詢服務",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """健康檢查端點

    Linus 哲學：實用主義
    - 檢查所有關鍵服務的狀態
    - 提供足夠的資訊用於監控
    """
    try:
        services = {}

        # 檢查向量存儲狀態
        try:
            if vector_store:
                collection_info = vector_store.get_collection_info()
                services["vector_store"] = "healthy"
            else:
                services["vector_store"] = "not_initialized"
        except Exception as e:
            services["vector_store"] = f"error: {str(e)}"

        # 檢查知識檢索器狀態
        try:
            if knowledge_retriever:
                services["knowledge_retriever"] = "healthy"
            else:
                services["knowledge_retriever"] = "not_initialized"
        except Exception as e:
            services["knowledge_retriever"] = f"error: {str(e)}"

        # 檢查工作流程狀態
        try:
            if finance_workflow:
                services["workflow"] = "healthy"
            else:
                services["workflow"] = "not_initialized"
        except Exception as e:
            services["workflow"] = f"error: {str(e)}"

        # 判斷整體狀態
        overall_status = "healthy" if all(
            status == "healthy" for status in services.values()
        ) else "degraded"

        return HealthCheckResponse(
            status=overall_status,
            version="1.0.0",
            services=services
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            version="1.0.0",
            services={"error": str(e)}
        )


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """處理理財諮詢查詢

    Linus 哲學：好品味的 API 設計
    - 清晰的輸入驗證
    - 結構化的錯誤處理
    - 完整的回應資訊
    - 對話記憶管理
    """
    start_time = time.time()
    session_id = request.session_id or str(uuid.uuid4())

    try:
        logger.info(f"Processing query for session: {session_id}")

        # 檢查服務是否就緒
        if not finance_workflow:
            raise HTTPException(
                status_code=503,
                detail="理財諮詢服務尚未就緒，請稍後再試"
            )

        # 管理對話記憶
        if session_id not in session_memories:
            # 首次查詢：建立新的 ConversationMemory
            session_memories[session_id] = ConversationMemory(
                session_id=session_id,
                max_turns=10,
                max_context_tokens=4000
            )
            logger.info(f"Created new conversation memory for session: {session_id}")

        memory = session_memories[session_id]

        # 從前端歷史恢復（如果有）
        if request.conversation_history:
            # 清空現有記憶並從前端歷史重建
            memory.clear()
            for hist_item in request.conversation_history:
                role = MessageRole(hist_item.role)
                memory.add_message(
                    role=role,
                    content=hist_item.content
                )
            logger.info(f"Restored {len(request.conversation_history)} messages from frontend")

        # 添加當前使用者查詢到記憶
        memory.add_message(
            role=MessageRole.USER,
            content=request.query
        )

        # 獲取格式化的對話歷史給 LLM
        conversation_history = memory.get_context_for_llm(
            include_system_prompt=False  # system prompt 由各 agent 自己加
        )

        # 更新會話資訊
        active_sessions[session_id] = {
            "created_at": active_sessions.get(session_id, {}).get("created_at", datetime.now()),
            "last_activity": datetime.now(),
            "query_count": active_sessions.get(session_id, {}).get("query_count", 0) + 1,
            "status": "processing"
        }

        # 執行理財諮詢工作流程（傳入對話歷史）
        workflow_result = await finance_workflow.run(
            user_query=request.query,
            user_profile=request.user_profile,
            session_id=session_id,
            conversation_history=conversation_history
        )

        # 更新會話狀態
        active_sessions[session_id]["status"] = "completed"
        active_sessions[session_id]["last_activity"] = datetime.now()

        # 儲存 AI 回應到記憶
        final_response_text = workflow_result.get("final_response", "無法生成回應")
        memory.add_message(
            role=MessageRole.ASSISTANT,
            content=final_response_text,
            confidence=workflow_result.get("confidence_score", 0.0),
            sources=workflow_result.get("response_sources", [])
        )
        logger.info(f"Saved AI response to memory, total turns: {memory.total_turns}")

        # 轉換專家回應格式
        expert_responses = []
        for expert_type, response_data in workflow_result["expert_responses"].items():
            expert_responses.append({
                "expert_type": expert_type,
                "content": response_data["content"],
                "confidence": response_data["confidence"],
                "sources": workflow_result["expert_sources"].get(expert_type, []),
                "metadata": response_data["metadata"]
            })

        # 計算處理時間
        processing_time = time.time() - start_time

        # 建立回應
        response = QueryResponse(
            session_id=session_id,
            query=request.query,
            final_response=final_response_text,
            confidence_score=workflow_result.get("confidence_score", 0.0),
            expert_responses=expert_responses,
            sources=workflow_result.get("response_sources", []),
            processing_time=processing_time,
            status=workflow_result.get("status", "failed")
        )

        logger.info(f"Query processed successfully in {processing_time:.2f}s")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}")

        # 更新會話狀態
        if session_id in active_sessions:
            active_sessions[session_id]["status"] = "failed"
            active_sessions[session_id]["last_activity"] = datetime.now()

        raise HTTPException(
            status_code=500,
            detail=f"查詢處理失敗：{str(e)}"
        )


@app.post("/query/stream")
async def process_query_stream(request: QueryRequest):
    """處理理財諮詢查詢（流式回應）

    使用 Server-Sent Events (SSE) 逐塊返回回應
    提供更好的用戶體驗，減少感知延遲
    """
    session_id = request.session_id or str(uuid.uuid4())

    async def event_generator():
        """SSE 事件生成器"""
        try:
            logger.info(f"Starting streaming query for session: {session_id}")

            # 檢查服務是否就緒
            if not finance_workflow:
                yield f"data: {json.dumps({'error': '理財諮詢服務尚未就緒'})}\n\n"
                return

            # 管理對話記憶
            if session_id not in session_memories:
                session_memories[session_id] = ConversationMemory(
                    session_id=session_id,
                    max_turns=10,
                    max_context_tokens=4000
                )
                logger.info(f"Created new conversation memory for session: {session_id}")

            memory = session_memories[session_id]

            # 從前端歷史恢復
            if request.conversation_history:
                memory.clear()
                for hist_item in request.conversation_history:
                    role = MessageRole(hist_item.role)
                    memory.add_message(role=role, content=hist_item.content)
                logger.info(f"Restored {len(request.conversation_history)} messages from frontend")

            # 添加當前使用者查詢
            memory.add_message(role=MessageRole.USER, content=request.query)

            # 取得對話歷史
            conversation_history = memory.get_context_for_llm(include_system_prompt=False)

            # 發送開始事件
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"

            # 執行工作流程（使用流式模式）
            # 注意：需要修改 workflow 以支援流式
            from ..workflow.finance_workflow_llm import FinanceWorkflowLLM

            # 暫時使用普通模式，後續修改 workflow
            workflow_result = await finance_workflow.run(
                user_query=request.query,
                user_profile=request.user_profile,
                session_id=session_id,
                conversation_history=conversation_history,
                stream=True  # 啟用流式模式
            )

            # 檢查是否為 async generator（流式）
            if hasattr(workflow_result, '__aiter__'):
                # 流式模式：逐塊發送
                full_content = ""
                async for chunk in workflow_result:
                    if isinstance(chunk, dict) and 'content' in chunk:
                        content_piece = chunk['content']
                        full_content += content_piece
                        yield f"data: {json.dumps({'type': 'content', 'content': content_piece})}\n\n"
                    elif isinstance(chunk, str):
                        full_content += chunk
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

                # 保存完整回應到記憶
                memory.add_message(
                    role=MessageRole.ASSISTANT,
                    content=full_content,
                    confidence=0.5
                )

                # 發送完成事件
                yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
            else:
                # 降級到普通模式：一次性發送
                final_response = workflow_result.get("final_response", "")
                yield f"data: {json.dumps({'type': 'content', 'content': final_response})}\n\n"

                # 保存到記憶
                memory.add_message(
                    role=MessageRole.ASSISTANT,
                    content=final_response,
                    confidence=workflow_result.get("confidence_score", 0.0)
                )

                yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"

            logger.info(f"Streaming query completed for session: {session_id}")

        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    import json
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 nginx buffering
        }
    )


@app.get("/session/{session_id}/status", response_model=WorkflowStatus)
async def get_session_status(session_id: str):
    """取得會話狀態

    支援 HITL (Human-in-the-Loop) 機制的長時間處理查詢
    """
    if session_id not in active_sessions:
        raise HTTPException(
            status_code=404,
            detail="找不到指定的會話"
        )

    session_data = active_sessions[session_id]

    return WorkflowStatus(
        session_id=session_id,
        status=session_data.get("status", "unknown"),
        current_step=session_data.get("current_step", "completed"),
        progress=1.0 if session_data.get("status") == "completed" else 0.5,
        estimated_completion=None,
        error_messages=session_data.get("error_messages", [])
    )


@app.get("/session/{session_id}/info", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """取得會話詳細資訊"""
    if session_id not in active_sessions:
        raise HTTPException(
            status_code=404,
            detail="找不到指定的會話"
        )

    session_data = active_sessions[session_id]

    return SessionInfo(
        session_id=session_id,
        created_at=session_data["created_at"],
        last_activity=session_data["last_activity"],
        query_count=session_data["query_count"],
        status=session_data["status"]
    )


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """刪除會話資料"""
    deleted = False

    if session_id in active_sessions:
        del active_sessions[session_id]
        deleted = True

    if session_id in session_memories:
        del session_memories[session_id]
        deleted = True

    if deleted:
        return {"message": f"會話 {session_id} 已刪除"}
    else:
        raise HTTPException(
            status_code=404,
            detail="找不到指定的會話"
        )


@app.get("/stats")
async def get_system_stats():
    """取得系統統計資訊"""
    try:
        stats = {
            "active_sessions": len(active_sessions),
            "total_queries": sum(
                session.get("query_count", 0)
                for session in active_sessions.values()
            ),
            "system_status": "operational"
        }

        # 添加向量存儲統計
        if vector_store:
            collection_info = vector_store.get_collection_info()
            stats["vector_store"] = {
                "document_count": collection_info.get("document_count", 0),
                "collection_name": collection_info.get("name")
            }

        # 添加檢索器統計
        if knowledge_retriever:
            retriever_stats = knowledge_retriever.get_retriever_stats()
            stats["knowledge_retriever"] = retriever_stats

        return stats

    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    # 開發模式啟動
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )