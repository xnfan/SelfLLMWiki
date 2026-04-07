"""PDF -> Markdown 转换服务"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── 可选依赖检测 ──

try:
    import marker  # noqa: F401
    _HAS_MARKER = True
except ImportError:
    _HAS_MARKER = False

try:
    import pymupdf4llm  # noqa: F401
    _HAS_PYMUPDF4LLM = True
except ImportError:
    _HAS_PYMUPDF4LLM = False


def convert_pdf_to_markdown(pdf_path: Path, use_marker: bool = True) -> str:
    """将 PDF 文件转换为 Markdown 文本。

    Parameters
    ----------
    pdf_path : Path
        PDF 文件路径
    use_marker : bool
        是否优先使用 marker 库（默认 True）。
        如果 marker 未安装则自动降级为 pymupdf4llm。

    Returns
    -------
    str
        转换后的 Markdown 文本。如果两个库都未安装，返回错误信息。
    """
    if not pdf_path.exists():
        return f"[错误] PDF 文件不存在: {pdf_path}"

    # 优先尝试 marker
    if use_marker and _HAS_MARKER:
        return _convert_with_marker(pdf_path)

    # 降级到 pymupdf4llm
    if _HAS_PYMUPDF4LLM:
        return _convert_with_pymupdf4llm(pdf_path)

    # 如果用户要求 marker 但未安装，再检查 pymupdf4llm
    if use_marker and not _HAS_MARKER and not _HAS_PYMUPDF4LLM:
        return (
            "[错误] PDF 转换库未安装。请安装以下任一库：\n"
            "  - marker（推荐，支持 OCR 和高质量转换）：pip install marker-pdf\n"
            "  - pymupdf4llm（轻量级备选）：pip install pymupdf4llm\n"
        )

    return (
        "[错误] PDF 转换库未安装。请安装：pip install pymupdf4llm"
    )


def _convert_with_marker(pdf_path: Path) -> str:
    """使用 marker 库转换 PDF"""
    try:
        from marker.converters.pdf import PdfConverter
        from marker.models import create_model_dict

        models = create_model_dict()
        converter = PdfConverter(artifact_dict=models)
        rendered = converter(str(pdf_path))
        # marker 返回的 rendered 对象包含 markdown 属性
        if hasattr(rendered, "markdown"):
            return rendered.markdown
        # 兼容不同版本
        return str(rendered)
    except Exception:
        logger.exception("marker 转换 PDF 失败: %s", pdf_path)
        # 尝试降级
        if _HAS_PYMUPDF4LLM:
            logger.info("降级到 pymupdf4llm 转换")
            return _convert_with_pymupdf4llm(pdf_path)
        return f"[错误] marker 转换 PDF 失败: {pdf_path}"


def _convert_with_pymupdf4llm(pdf_path: Path) -> str:
    """使用 pymupdf4llm 库转换 PDF"""
    try:
        import pymupdf4llm
        return pymupdf4llm.to_markdown(str(pdf_path))
    except Exception:
        logger.exception("pymupdf4llm 转换 PDF 失败: %s", pdf_path)
        return f"[错误] pymupdf4llm 转换 PDF 失败: {pdf_path}"
