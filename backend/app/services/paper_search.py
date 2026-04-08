"""统一论文搜索服务 — 支持多源自动切换"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import httpx

from ..config import get_config
from ..models.schemas import PaperInfo

logger = logging.getLogger(__name__)

# ── arXiv 支持 ──

ARXIV_API_URL = "https://export.arxiv.org/api/query"


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


async def _search_arxiv(query: str, limit: int = 20) -> list[PaperInfo]:
    """搜索 arXiv"""
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(limit, 50),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(ARXIV_API_URL, params=params)
            resp.raise_for_status()

            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            papers: list[PaperInfo] = []
            for entry in root.findall("atom:entry", ns):
                entry_dict: dict[str, Any] = {}

                title_elem = entry.find("atom:title", ns)
                entry_dict["title"] = title_elem.text if title_elem is not None else ""

                summary_elem = entry.find("atom:summary", ns)
                entry_dict["summary"] = summary_elem.text if summary_elem is not None else ""

                published_elem = entry.find("atom:published", ns)
                entry_dict["published"] = published_elem.text if published_elem is not None else ""

                id_elem = entry.find("atom:id", ns)
                entry_dict["id"] = id_elem.text if id_elem is not None else ""

                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None:
                        authors.append({"name": name_elem.text or ""})
                entry_dict["author"] = authors

                links = []
                for link in entry.findall("atom:link", ns):
                    links.append(dict(link.attrib))
                entry_dict["link"] = links

                categories = []
                for cat in entry.findall("atom:category", ns):
                    categories.append(dict(cat.attrib))
                entry_dict["category"] = categories

                paper = _parse_arxiv_entry(entry_dict)
                if paper.title:
                    papers.append(paper)

            logger.info(f"arXiv 搜索 '{query}' 返回 {len(papers)} 篇")
            return papers

    except Exception as e:
        logger.warning(f"arXiv 搜索失败: {e}")
        return []


# ── Semantic Scholar 支持 ──

try:
    from semanticscholar import SemanticScholar
    _HAS_SS = True
except ImportError:
    SemanticScholar = None  # type: ignore
    _HAS_SS = False

_SS_FIELDS = [
    "paperId", "title", "authors", "year", "venue",
    "citationCount", "abstract", "openAccessPdf", "externalIds",
]


def _ss_paper_to_info(paper: Any) -> PaperInfo:
    """转换 Semantic Scholar 论文对象"""
    if not isinstance(paper, dict):
        paper = paper.__dict__ if hasattr(paper, "__dict__") else {}

    authors_raw = paper.get("authors") or []
    authors = []
    for a in authors_raw:
        if isinstance(a, dict):
            authors.append(a.get("name", ""))
        elif hasattr(a, "name"):
            authors.append(a.name)
        else:
            authors.append(str(a))

    open_access_url = ""
    oap = paper.get("openAccessPdf")
    if isinstance(oap, dict):
        open_access_url = oap.get("url", "")
    elif hasattr(oap, "url"):
        open_access_url = oap.url or ""

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
    """搜索 Semantic Scholar"""
    if not _HAS_SS:
        return []

    try:
        sch = SemanticScholar()
        results = sch.search_paper(query, limit=limit, fields=_SS_FIELDS)
        papers = [_ss_paper_to_info(p) for p in (results or [])]
        logger.info(f"Semantic Scholar 搜索 '{query}' 返回 {len(papers)} 篇")
        return papers
    except Exception as e:
        logger.warning(f"Semantic Scholar 搜索失败: {e}")
        return []


# ── 统一接口 ──

async def search_papers(
    query: str,
    limit: int = 20,
    sources: list[str] | None = None,
) -> list[PaperInfo]:
    """搜索论文（自动多源）

    优先尝试 Semantic Scholar，如果失败或结果不足，使用 arXiv 补充。

    Parameters
    ----------
    query : str
        搜索关键词
    limit : int
        最大返回数量
    sources : list[str] | None
        指定搜索源 ["semantic_scholar", "arxiv"]，默认两者都试

    Returns
    -------
    list[PaperInfo]
        合并后的论文列表（去重）
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
            continue
        for paper in result:
            # 去重：优先使用 DOI，其次 paper_id，最后标题
            key = paper.doi or paper.paper_id or paper.title.lower()
            if key and key not in seen_ids:
                seen_ids.add(key)
                all_papers.append(paper)

    # 按年份降序排序（优先展示新论文）
    all_papers.sort(key=lambda p: p.year or 0, reverse=True)

    logger.info(f"搜索 '{query}' 共返回 {len(all_papers)} 篇（去重后）")
    return all_papers[:limit]


async def get_paper_details(paper_id: str) -> PaperInfo | None:
    """获取单篇论文详情

    自动识别 paper_id 格式（arxiv:xxx 或 Semantic Scholar ID）
    """
    if paper_id.startswith("arxiv:"):
        arxiv_id = paper_id.replace("arxiv:", "").strip()
        return await _get_arxiv_paper(arxiv_id)

    if _HAS_SS:
        try:
            sch = SemanticScholar()
            paper = sch.get_paper(paper_id, fields=_SS_FIELDS)
            return _ss_paper_to_info(paper)
        except Exception as e:
            logger.warning(f"获取论文详情失败: {e}")

    return None


async def _get_arxiv_paper(arxiv_id: str) -> PaperInfo | None:
    """获取 arXiv 单篇论文"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                ARXIV_API_URL,
                params={"id_list": arxiv_id, "max_results": 1},
            )
            resp.raise_for_status()

            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            entry = root.find("atom:entry", ns)
            if entry is None:
                return None

            entry_dict: dict[str, Any] = {
                "title": getattr(entry.find("atom:title", ns), "text", "") or "",
                "summary": getattr(entry.find("atom:summary", ns), "text", "") or "",
                "published": getattr(entry.find("atom:published", ns), "text", "") or "",
                "id": getattr(entry.find("atom:id", ns), "text", "") or "",
            }

            authors = []
            for author in entry.findall("atom:author", ns):
                name_elem = author.find("atom:name", ns)
                if name_elem is not None:
                    authors.append({"name": name_elem.text or ""})
            entry_dict["author"] = authors

            links = []
            for link in entry.findall("atom:link", ns):
                links.append(dict(link.attrib))
            entry_dict["link"] = links

            categories = []
            for cat in entry.findall("atom:category", ns):
                categories.append(dict(cat.attrib))
            entry_dict["category"] = categories

            return _parse_arxiv_entry(entry_dict)

    except Exception as e:
        logger.warning(f"获取 arXiv 论文失败: {e}")
        return None


async def get_related_papers(paper_id: str, limit: int = 20) -> list[PaperInfo]:
    """获取相关论文

    仅 Semantic Scholar 支持此功能，arXiv 不支持
    """
    if not _HAS_SS or paper_id.startswith("arxiv:"):
        return []

    try:
        sch = SemanticScholar()
        results: list[PaperInfo] = []
        refs = sch.get_paper_references(paper_id, fields=_SS_FIELDS, limit=limit)
        for ref in (refs or []):
            cited = ref.get("citedPaper") if isinstance(ref, dict) else getattr(ref, "citedPaper", None)
            if cited:
                results.append(_ss_paper_to_info(cited))
        return results[:limit]
    except Exception as e:
        logger.warning(f"获取相关论文失败: {e}")
        return []


async def get_paper_recommendations(paper_id: str, limit: int = 20) -> list[PaperInfo]:
    """获取推荐论文

    仅 Semantic Scholar 支持此功能
    """
    if not _HAS_SS or paper_id.startswith("arxiv:"):
        return []

    try:
        sch = SemanticScholar()
        recs = sch.get_recommended_papers(paper_id, limit=limit, fields=_SS_FIELDS)
        return [_ss_paper_to_info(p) for p in (recs or [])]
    except Exception as e:
        logger.warning(f"获取推荐论文失败: {e}")
        return []


async def download_paper_pdf(url: str, save_path: Path) -> bool:
    """下载论文 PDF

    支持任意 URL（Semantic Scholar 或 arXiv）
    """
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            save_path.write_bytes(resp.content)
            logger.info(f"PDF 下载成功: {url}")
            return True
    except Exception as e:
        logger.exception(f"PDF 下载失败: {url}")
        return False


async def download_arxiv_pdf(arxiv_id: str, save_path: Path) -> bool:
    """下载 arXiv PDF"""
    arxiv_id = arxiv_id.replace("arxiv:", "").strip()
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    return await download_paper_pdf(pdf_url, save_path)
