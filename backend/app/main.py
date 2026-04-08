"""SelfLLMWiki FastAPI 应用入口"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import get_config
from .routers import wiki, raw, log, ingest, query, deposit, lint, papers, web

logger = logging.getLogger(__name__)

# 创建限流器：每分钟最多 60 个请求
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# WebSocket 连接管理（进度通知）
ws_connections: set[WebSocket] = set()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理：启动时初始化配置和数据目录"""
    cfg = get_config()
    # 确保数据目录存在
    cfg.data.wiki_path.mkdir(parents=True, exist_ok=True)
    cfg.data.pages_path.mkdir(parents=True, exist_ok=True)
    cfg.data.raw_path.mkdir(parents=True, exist_ok=True)
    cfg.data.assets_path.mkdir(parents=True, exist_ok=True)
    logger.info("SelfLLMWiki 启动完成，数据目录: %s", cfg.data.root_path)
    yield
    # 关闭时清理
    logger.info("SelfLLMWiki 正在关闭...")


app = FastAPI(
    title="SelfLLMWiki",
    description="自托管 LLM Wiki 知识库系统",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置限流器
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 配置 CORS（允许 Vue 开发服务器）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有路由
app.include_router(wiki.router)
app.include_router(raw.router)
app.include_router(log.router)
app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(deposit.router)
app.include_router(lint.router)
app.include_router(papers.router)
app.include_router(web.router)


@app.get("/")
async def root():
    """根路径欢迎消息"""
    return {
        "message": "欢迎使用 SelfLLMWiki — 自托管 LLM Wiki 知识库系统",
        "docs": "/docs",
        "version": "0.1.0",
    }


@app.get("/health", summary="健康检查")
async def health_check():
    """健康检查端点，用于容器化部署监控"""
    try:
        cfg = get_config()
        # 检查关键目录是否可访问
        checks = {
            "wiki_dir": cfg.data.wiki_path.exists(),
            "pages_dir": cfg.data.pages_path.exists(),
            "raw_dir": cfg.data.raw_path.exists(),
            "assets_dir": cfg.data.assets_path.exists(),
        }

        all_healthy = all(checks.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "checks": checks,
            "version": "0.1.0",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "version": "0.1.0",
        }


@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket 端点：推送任务进度通知"""
    await websocket.accept()
    ws_connections.add(websocket)
    try:
        while True:
            # 保持连接活跃，等待客户端消息（如 ping）
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_connections.discard(websocket)


async def broadcast_progress(message: dict) -> None:
    """向所有已连接的 WebSocket 客户端广播进度消息"""
    disconnected: list[WebSocket] = []
    for ws in ws_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        ws_connections.discard(ws)
