"""统一论文搜索服务 — 支持多源自动切换（纯 httpx 异步实现）

完全使用 httpx 异步 HTTP 调用，不依赖 semanticscholar 库，
避免同步阻塞事件循环导致超时。
"""

from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import httpx

from ..models.schemas import PaperInfo

logger = logging.getLogger(__name__)

# ── 常量 ──

ARXIV_API_URL = "https://export.arxiv.org/api/query"
S2_API_BASE = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = "paperId,title,authors,year,venue,citationCount,abstract,openAccessPdf,externalIds"

# 所有外部 API 调用共用的超时（秒）
_API_TIMEOUT = 15.0


# ── 通用 httpx 客户端 ──

def _make_client(timeout: float = _API_TIMEOUT) -> httpx.AsyncClient:
    """创建带合理默认值的异步 HTTP 客户端"""
    return httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "SelfLLMWiki/0.1 (academic-research)"},
    )


# ── arXiv ──

def _parse_arxiv_entry(entry: dict[str, Any]) -> PaperInfo:
    """解析 arXiv API 返回的 entry"""
    title = entry.get("title", "").replace("\n", " ").strip()

    authors = []
    author_data = entry.get("author", [])
    if not isinstance(author_data, list):
        author_data = [author_data]
    for a in author_data:
        if isinstance(a, dict):
            name = a.get("name", "")
            if name:
                authors.append(name)

    published = entry.get("published", "")
    year = None
    if published and len(published) >= 4:
        try:
            year = int(published[:4])
        except ValueError:
            pass

    summary = entry.get("summary", "").replace("\n", " ").strip()

    arxiv_id = ""
    id_url = entry.get("id", "")
    if id_url:
        parts = id_url.rstrip("/").split("/")
        if parts:
            arxiv_id = parts[-1].replace("v1", "").replace("v2", "").replace("v3", "")

    pdf_url = ""
    links = entry.get("link", [])
    if not isinstance(links, list):
        links = [links]
    for link in links:
        if isinstance(link, dict) and link.get("title") == "pdf":
            pdf_url = link.get("href", "")
            break

    categories = []
    cat_data = entry.get("category", [])
    if not isinstance(cat_data, list):
        cat_data = [cat_data]
    for c in cat_data:
        if isinstance(c, dict):
            term = c.get("term", "")
            if term:
                categories.append(term)

    venue = f"arXiv:{categories[0]}" if categories else "arXiv"

    return PaperInfo(
        paper_id=f"arxiv:{arxiv_id}",
        title=title,
        authors=authors,
        year=year,
        venue=venue,
        citation_count=0,
        abstract=summary,
        open_access_url=pdf_url,
        doi="",
        in_wiki=False,
    )


def _parse_arxiv_xml(xml_text: str) -> list[PaperInfo]:
    """解析 arXiv Atom XML 为 PaperInfo 列表"""
    root = ET.fromstring(xml_text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    papers: list[PaperInfo] = []
    for entry in root.findall("atom:entry", ns):
        entry_dict: dict[str, Any] = {}

        for field in ("title", "summary", "published", "id"):
            elem = entry.find(f"atom:{field}", ns)
            entry_dict[field] = elem.text if elem is not None else ""

        authors = []
        for author in entry.findall("atom:author", ns):
            name_elem = author.find("atom:name", ns)
            if name_elem is not None:
                authors.append({"name": name_elem.text or ""})
        entry_dict["author"] = authors

        entry_dict["link"] = [dict(l.attrib) for l in entry.findall("atom:link", ns)]
        entry_dict["category"] = [dict(c.attrib) for c in entry.findall("atom:category", ns)]

        paper = _parse_arxiv_entry(entry_dict)
        if paper.title:
            papers.append(paper)

    return papers


async def _search_arxiv(query: str, limit: int = 20) -> list[PaperInfo]:
    """搜索 arXiv（纯异步）"""
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(limit, 50),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        async with _make_client(timeout=_API_TIMEOUT) as client:
            resp = await client.get(ARXIV_API_URL, params=params)
            resp.raise_for_status()
            papers = _parse_arxiv_xml(resp.text)
            logger.info("arXiv 搜索 '%s' 返回 %d 篇", query, len(papers))
            return papers
    except Exception as e:
        logger.warning("arXiv 搜索失败: %s", e)
        return []


# ── Semantic Scholar（纯 httpx 异步调用）──

def _s2_paper_to_info(paper: dict[str, Any]) -> PaperInfo:
    """将 Semantic Scholar REST API 返回的 dict 转为 PaperInfo"""
    authors_raw = paper.get("authors") or []
    authors = [a.get("name", "") for a in authors_raw if isinstance(a, dict)]

    open_access_url = ""
    oap = paper.get("openAccessPdf")
    if isinstance(oap, dict):
        open_access_url = oap.get("url", "")

    doi = ""
    ext_ids = paper.get("externalIds") or {}
    if isinstance(ext_ids, dict):
        doi = ext_ids.get("DOI", "")

    return PaperInfo(
        paper_id=paper.get("paperId", "") or "",
        title=paper.get("title", "") or "",
        authors=authors,
        year=paper.get("year"),
        venue=paper.get("venue", "") or "",
        citation_count=paper.get("citationCount", 0) or 0,
        abstract=paper.get("abstract", "") or "",
        open_access_url=open_access_url,
        doi=doi,
        in_wiki=False,
    )


async def _search_semantic_scholar(query: str, limit: int = 20) -> list[PaperInfo]:
    """搜索 Semantic Scholar（纯异步 httpx，带严格超时）"""
    url = f"{S2_API_BASE}/paper/search"
    params = {"query": query, "limit": min(limit, 100), "fields": S2_FIELDS}

    try:
        async with _make_client(timeout=_API_TIMEOUT) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                logger.warning("Semantic Scholar 限流 (429)，跳过")
                return []
            resp.raise_for_status()
            data = resp.json()
            papers = [_s2_paper_to_info(p) for p in (data.get("data") or [])]
            logger.info("Semantic Scholar 搜索 '%s' 返回 %d 篇", query, len(papers))
            return papers
    except httpx.TimeoutException:
        logger.warning("Semantic Scholar 搜索超时 (%.0fs)", _API_TIMEOUT)
        return []
    except Exception as e:
        logger.warning("Semantic Scholar 搜索失败: %s", e)
        return []


# ── 统一接口 ──

async def search_papers(
    query: str,
    limit: int = 20,
    sources: list[str] | None = None,
) -> list[PaperInfo]:
    """搜索论文（自动多源，并行请求）

    优先并行请求 Semantic Scholar 和 arXiv，合并结果。

    Parameters
    ----------
    query : str
        搜索关键词
    limit : int
        最大返回数量
    sources : list[str] | None
        指定搜索源 ["semantic_scholar", "arxiv"]，默认两者都试
    """
    if sources is None:
        sources = ["semantic_scholar", "arxiv"]

    all_papers: list[PaperInfo] = []
    seen_ids: set[str] = set()

    # 并行搜索所有指定源
    tasks = []
    if "semantic_scholar" in sources:
        tasks.append(_search_semantic_scholar(query, limit))
    if "arxiv" in sources:
        tasks.append(_search_arxiv(query, limit))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            logger.warning("搜索源异常: %s", result)
            continue
        for paper in result:
            key = paper.doi or paper.paper_id or paper.title.lower()
            if key and key not in seen_ids:
                seen_ids.add(key)
                all_papers.append(paper)

    # 按年份降序排序
    all_papers.sort(key=lambda p: p.year or 0, reverse=True)
    logger.info("搜索 '%s' 共返回 %d 篇（去重后）", query, len(all_papers))
    return all_papers[:limit]


async def get_paper_details(paper_id: str) -> PaperInfo | None:
    """获取单篇论文详情"""
    if paper_id.startswith("arxiv:"):
        arxiv_id = paper_id.replace("arxiv:", "").strip()
        return await _get_arxiv_paper(arxiv_id)

    # Semantic Scholar
    url = f"{S2_API_BASE}/paper/{paper_id}"
    params = {"fields": S2_FIELDS}
    try:
        async with _make_client() as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return _s2_paper_to_info(resp.json())
    except Exception as e:
        logger.warning("获取论文详情失败: %s", e)
        return None


async def _get_arxiv_paper(arxiv_id: str) -> PaperInfo | None:
    """获取 arXiv 单篇论文"""
    try:
        async with _make_client() as client:
            resp = await client.get(ARXIV_API_URL, params={"id_list": arxiv_id, "max_results": 1})
            resp.raise_for_status()
            papers = _parse_arxiv_xml(resp.text)
            return papers[0] if papers else None
    except Exception as e:
        logger.warning("获取 arXiv 论文失败: %s", e)
        return None


async def get_related_papers(paper_id: str, limit: int = 20) -> list[PaperInfo]:
    """获取相关论文（引用的论文）"""
    if paper_id.startswith("arxiv:"):
        return []

    url = f"{S2_API_BASE}/paper/{paper_id}/references"
    params = {"fields": S2_FIELDS, "limit": min(limit, 100)}
    try:
        async with _make_client() as client:
            resp = await client.get(url, params=params)
            if resp.status_code in (404, 429):
                return []
            resp.raise_for_status()
            data = resp.json().get("data") or []
            results = []
            for ref in data:
                cited = ref.get("citedPaper")
                if cited and cited.get("title"):
                    results.append(_s2_paper_to_info(cited))
            return results[:limit]
    except Exception as e:
        logger.warning("获取相关论文失败: %s", e)
        return []


async def get_paper_recommendations(paper_id: str, limit: int = 20) -> list[PaperInfo]:
    """获取推荐论文"""
    if paper_id.startswith("arxiv:"):
        return []

    url = f"{S2_API_BASE}/paper/{paper_id}/citations"
    params = {"fields": S2_FIELDS, "limit": min(limit, 100)}
    try:
        async with _make_client() as client:
            resp = await client.get(url, params=params)
            if resp.status_code in (404, 429):
                return []
            resp.raise_for_status()
            data = resp.json().get("data") or []
            results = []
            for cit in data:
                citing = cit.get("citingPaper")
                if citing and citing.get("title"):
                    results.append(_s2_paper_to_info(citing))
            return results[:limit]
    except Exception as e:
        logger.warning("获取推荐论文失败: %s", e)
        return []


async def download_paper_pdf(url: str, save_path: Path) -> bool:
    """下载论文 PDF"""
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        async with _make_client(timeout=60.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            save_path.write_bytes(resp.content)
            logger.info("PDF 下载成功: %s", url)
            return True
    except Exception as e:
        logger.warning("PDF 下载失败 %s: %s", url, e)
        return False


async def download_arxiv_pdf(arxiv_id: str, save_path: Path) -> bool:
    """下载 arXiv PDF"""
    arxiv_id = arxiv_id.replace("arxiv:", "").strip()
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    return await download_paper_pdf(pdf_url, save_path)
