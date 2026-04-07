"""查询路由 — 基于 Wiki 知识库的问答"""

from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import QueryRequest, QueryResponse
from ..services.query_service import QueryService

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("", summary="查询 Wiki")
async def query_wiki(body: QueryRequest) -> QueryResponse:
    """根据用户问题查询 Wiki 知识库并生成回答"""
    svc = QueryService()
    try:
        return await svc.query(body.question, provider=body.provider)
    except Exception as e:
        return QueryResponse(
            answer=f"查询失败: {e}",
            sources=[],
            can_deposit=False,
        )
