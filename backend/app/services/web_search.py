"""网络搜索服务 — 封装 DuckDuckGo 搜索"""

from __future__ import annotations

import logging

from ..models.schemas import WebSearchResult

logger = logging.getLogger(__name__)

# ── 可选依赖 ──

try:
    from duckduckgo_search import DDGS
    _HAS_DDGS = True
except ImportError:
    DDGS = None  # type: ignore[assignment, misc]
    _HAS_DDGS = False


def search_duckduckgo(query: str, max_results: int = 10) -> list[WebSearchResult]:
    """使用 DuckDuckGo 搜索并返回结果列表。

    Parameters
    ----------
    query : str
        搜索关键词
    max_results : int
        最大返回结果数，默认 10

    Returns
    -------
    list[WebSearchResult]
        搜索结果列表
    """
    if not _HAS_DDGS:
        raise ImportError(
            "需要安装 duckduckgo-search 库：pip install duckduckgo-search"
        )

    results: list[WebSearchResult] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(WebSearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                ))
    except Exception:
        logger.exception("DuckDuckGo 搜索出错: query=%s", query)

    return results
