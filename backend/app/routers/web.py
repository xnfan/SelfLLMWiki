"""网络搜索和抓取路由 — 网络搜索与 URL 内容抓取"""

from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import (
    WebFetchRequest,
    WebFetchResponse,
    WebSearchRequest,
    WebSearchResponse,
)
from ..services.web_search import search_duckduckgo
from ..services.html_converter import convert_url_to_markdown

router = APIRouter(prefix="/api/web", tags=["web"])


@router.post("/search", summary="网络搜索")
async def web_search(body: WebSearchRequest) -> WebSearchResponse:
    """执行网络搜索并返回结果"""
    try:
        results = search_duckduckgo(body.query, max_results=body.max_results)
        return WebSearchResponse(results=results)
    except Exception as e:
        return WebSearchResponse(results=[])


@router.post("/fetch", summary="抓取 URL")
async def web_fetch(body: WebFetchRequest) -> WebFetchResponse:
    """抓取指定 URL 的内容并转换为 Markdown"""
    try:
        title, content = convert_url_to_markdown(body.url)
        return WebFetchResponse(title=title, content=content, url=body.url)
    except Exception as e:
        return WebFetchResponse(
            title="",
            content=f"抓取失败: {e}",
            url=body.url,
        )
