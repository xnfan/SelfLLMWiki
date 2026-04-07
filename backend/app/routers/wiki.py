"""Wiki CRUD 路由 — 页面管理与图谱查询"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config import get_config
from ..models.schemas import (
    GraphData,
    WikiPage,
    WikiPageCreate,
    WikiPageSummary,
    WikiPageUpdate,
)
from ..services.graph_builder import GraphBuilder
from ..services.wiki_manager import WikiManager, slugify

router = APIRouter(prefix="/api/wiki", tags=["wiki"])


def _get_wiki() -> WikiManager:
    """获取 WikiManager 实例"""
    return WikiManager()


def _get_graph() -> GraphBuilder:
    """获取 GraphBuilder 实例"""
    return GraphBuilder(_get_wiki())


# ── 页面 CRUD ──


@router.get("/pages", summary="列出所有页面")
async def list_pages() -> list[WikiPageSummary]:
    """获取所有 Wiki 页面的摘要列表"""
    wiki = _get_wiki()
    return wiki.list_pages()


@router.get("/pages/{slug}", summary="获取页面")
async def get_page(slug: str) -> WikiPage:
    """根据 slug 获取指定页面的完整内容"""
    wiki = _get_wiki()
    page = wiki.read_page(slug)
    if page is None:
        raise HTTPException(status_code=404, detail=f"页面 '{slug}' 不存在")
    return page


@router.post("/pages", summary="创建页面", status_code=201)
async def create_page(body: WikiPageCreate) -> WikiPage:
    """创建新的 Wiki 页面"""
    wiki = _get_wiki()
    if wiki.page_exists(body.slug):
        raise HTTPException(status_code=409, detail=f"页面 '{body.slug}' 已存在")
    wiki.write_page(body.slug, body.content, title=body.title)
    wiki.append_log("创建页面", f"创建了页面 {body.slug}", [body.slug])
    wiki.update_index()
    page = wiki.read_page(body.slug)
    if page is None:
        raise HTTPException(status_code=500, detail="页面创建失败")
    return page


@router.put("/pages/{slug}", summary="更新页面")
async def update_page(slug: str, body: WikiPageUpdate) -> WikiPage:
    """更新指定页面的内容"""
    wiki = _get_wiki()
    if not wiki.page_exists(slug):
        raise HTTPException(status_code=404, detail=f"页面 '{slug}' 不存在")
    wiki.write_page(slug, body.content, title=body.title or "")
    wiki.append_log("更新页面", f"更新了页面 {slug}", [slug])
    wiki.update_index()
    page = wiki.read_page(slug)
    if page is None:
        raise HTTPException(status_code=500, detail="页面读取失败")
    return page


@router.delete("/pages/{slug}", summary="删除页面")
async def delete_page(slug: str) -> dict:
    """删除指定页面"""
    wiki = _get_wiki()
    if not wiki.delete_page(slug):
        raise HTTPException(status_code=404, detail=f"页面 '{slug}' 不存在")
    wiki.append_log("删除页面", f"删除了页面 {slug}", [slug])
    wiki.update_index()
    return {"success": True, "message": f"页面 '{slug}' 已删除"}


# ── 图谱 ──


@router.get("/graph", summary="获取图谱数据")
async def get_graph() -> GraphData:
    """获取完整的知识图谱数据"""
    builder = _get_graph()
    return builder.build()


@router.get("/graph/{slug}", summary="获取邻居子图")
async def get_graph_neighbors(slug: str, depth: int = 1) -> GraphData:
    """获取指定节点的邻居子图"""
    builder = _get_graph()
    return builder.get_neighbors(slug, depth=depth)


# ── 索引 ──


@router.get("/index", summary="获取索引")
async def get_index() -> dict:
    """获取 index.md 的内容"""
    wiki = _get_wiki()
    content = wiki.read_index()
    return {"content": content}
