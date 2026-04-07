"""摄入路由 — 文本/URL/论文 PDF 摄入"""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException

from ..models.schemas import IngestRequest, IngestResponse
from ..services.ingest_service import IngestService
from ..services.paper_pipeline import PaperPipeline

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("", summary="摄入文本或 URL")
async def ingest_text(body: IngestRequest) -> IngestResponse:
    """摄入文本内容或 URL，提取知识并写入 Wiki"""
    svc = IngestService()
    try:
        if body.url:
            return await svc.ingest_url(body.url)
        elif body.content:
            return await svc.ingest_text(
                content=body.content,
                source_type=body.source_type.value,
                title=body.title,
            )
        else:
            raise HTTPException(status_code=400, detail="请提供 content 或 url")
    except Exception as e:
        return IngestResponse(success=False, message=f"摄入失败: {e}")


@router.post("/paper", summary="摄入论文 PDF")
async def ingest_paper(file: UploadFile = File(...)) -> IngestResponse:
    """上传并摄入论文 PDF，解析内容并写入 Wiki"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="请上传文件")

    pipeline = PaperPipeline()
    try:
        data = await file.read()
        return await pipeline.process_paper_from_bytes(data, file.filename)
    except Exception as e:
        return IngestResponse(success=False, message=f"论文处理失败: {e}")
