"""日志路由 — 查看操作日志"""

from __future__ import annotations

from fastapi import APIRouter

from ..services.wiki_manager import WikiManager

router = APIRouter(prefix="/api/log", tags=["log"])


@router.get("", summary="获取操作日志")
async def get_log(limit: int = 100) -> dict:
    """获取最近的操作日志条目

    参数:
        limit: 返回的最大条目数，默认 100
    """
    wiki = WikiManager()
    content = wiki.read_log(limit=limit)
    return {"content": content}
