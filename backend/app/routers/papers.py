"""论文路由 — 论文搜索、拓展与下载（支持多源：Semantic Scholar + arXiv）"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter

from ..models.schemas import (
    PaperDownloadRequest,
    PaperDownloadResponse,
    PaperExpandRequest,
    PaperSearchRequest,
    PaperSearchResponse,
)
from ..services.paper_search import (
    search_papers,
    get_related_papers,
    get_paper_recommendations,
    download_paper_pdf,
    download_arxiv_pdf,
)
from ..services.paper_pipeline import PaperPipeline
from ..config import get_config

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("/search", summary="搜索论文")
async def api_search_papers(body: PaperSearchRequest) -> PaperSearchResponse:
    """搜索学术论文（自动使用 Semantic Scholar + arXiv 多源）"""
    try:
        papers = await search_papers(body.query, limit=body.limit)
        return PaperSearchResponse(papers=papers, total=len(papers))
    except Exception as e:
        return PaperSearchResponse(papers=[], total=0)


@router.post("/expand", summary="拓展论文")
async def api_expand_papers(body: PaperExpandRequest) -> PaperSearchResponse:
    """根据已有论文或主题拓展相关论文"""
    try:
        papers = []
        if body.paper_id:
            # arXiv 论文不支持拓展功能
            if body.paper_id.startswith("arxiv:"):
                # 对于 arXiv 论文，使用标题作为主题重新搜索
                paper = await get_related_papers(body.paper_id, limit=1)
                topic = paper[0].title if paper else ""
                if topic:
                    papers = await search_papers(topic, limit=body.limit)
            else:
                related = await get_related_papers(body.paper_id, limit=body.limit)
                recommended = await get_paper_recommendations(body.paper_id, limit=body.limit)
                # 合并去重
                seen = set()
                for p in related + recommended:
                    if p.paper_id not in seen:
                        seen.add(p.paper_id)
                        papers.append(p)
        elif body.topic:
            papers = await search_papers(body.topic, limit=body.limit)
        return PaperSearchResponse(papers=papers, total=len(papers))
    except Exception as e:
        return PaperSearchResponse(papers=[], total=0)


async def _download_single_paper(
    paper, pipeline: PaperPipeline, assets_path
) -> tuple[str, bool, str]:
    """下载并处理单篇论文

    Returns
    -------
    tuple[str, bool, str]
        (标题, 是否成功, 错误信息)
    """
    filename = f"{paper.paper_id or paper.title[:30]}.pdf"
    save_path = assets_path / filename

    try:
        success = False

        # 优先使用 open_access_url
        if paper.open_access_url:
            success = await download_paper_pdf(paper.open_access_url, save_path)

        # 如果是 arXiv 论文且上面失败，尝试直接下载
        if not success and paper.paper_id and paper.paper_id.startswith("arxiv:"):
            success = await download_arxiv_pdf(paper.paper_id, save_path)

        if success:
            result = await pipeline.process_paper(save_path, title=paper.title)
            if result.success:
                return (paper.title, True, "")
            else:
                return (paper.title, False, result.message)
        else:
            return (paper.title, False, "下载失败")
    except Exception as e:
        return (paper.title, False, str(e))


@router.post("/download", summary="下载并摄入论文")
async def api_download_papers(body: PaperDownloadRequest) -> PaperDownloadResponse:
    """批量下载论文 PDF 并通过管线处理（并发执行，最多3个并发）"""
    cfg = get_config().data
    pipeline = PaperPipeline()
    downloaded: list[str] = []
    failed: list[str] = []

    # 使用信号量限制并发数
    semaphore = asyncio.Semaphore(3)

    async def download_with_limit(paper):
        async with semaphore:
            return await _download_single_paper(paper, pipeline, cfg.assets_path)

    # 并发执行所有下载任务
    results = await asyncio.gather(
        *[download_with_limit(paper) for paper in body.papers],
        return_exceptions=True
    )

    # 处理结果
    for result in results:
        if isinstance(result, Exception):
            failed.append(f"未知错误: {result}")
            continue
        title, success, error_msg = result
        if success:
            downloaded.append(title)
        else:
            failed.append(f"{title}: {error_msg}")

    return PaperDownloadResponse(
        downloaded=downloaded,
        failed=failed,
        message=f"成功下载并处理 {len(downloaded)} 篇，失败 {len(failed)} 篇",
    )
