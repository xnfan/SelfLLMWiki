"""原始资料路由 — 浏览和读取 data/raw/ 下的文件"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..config import get_config
from ..models.schemas import RawFileInfo

router = APIRouter(prefix="/api/raw", tags=["raw"])


@router.get("/", summary="列出原始资料")
async def list_raw_files() -> list[RawFileInfo]:
    """遍历 data/raw/ 下的所有文件，返回文件信息列表"""
    cfg = get_config()
    raw_path = cfg.data.raw_path
    if not raw_path.exists():
        return []

    files: list[RawFileInfo] = []
    for f in sorted(raw_path.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(raw_path)
        # 第一层目录名作为类型（papers / articles / web / notes）
        parts = rel.parts
        file_type = parts[0] if len(parts) > 1 else "other"
        stat = f.stat()
        files.append(RawFileInfo(
            path=str(rel).replace("\\", "/"),
            name=f.name,
            type=file_type,
            size=stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        ))
    return files


@router.get("/{path:path}", summary="获取原始资料内容")
async def get_raw_file(path: str) -> dict:
    """读取指定原始资料的文本内容"""
    cfg = get_config()
    raw_path = cfg.data.raw_path
    file_path = raw_path / path

    # 安全检查：防止路径遍历
    try:
        file_path.resolve().relative_to(raw_path.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="禁止访问该路径")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"文件 '{path}' 不存在")

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="该文件不是文本文件，无法读取")

    return {
        "path": path,
        "name": file_path.name,
        "content": content,
    }
