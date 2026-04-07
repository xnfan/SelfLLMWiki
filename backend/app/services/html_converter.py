"""HTML / URL -> Markdown 转换服务"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ── 可选依赖 ──

try:
    import trafilatura
    _HAS_TRAFILATURA = True
except ImportError:
    trafilatura = None  # type: ignore[assignment]
    _HAS_TRAFILATURA = False

try:
    from markdownify import markdownify as md
    _HAS_MARKDOWNIFY = True
except ImportError:
    md = None  # type: ignore[assignment]
    _HAS_MARKDOWNIFY = False


def convert_url_to_markdown(url: str) -> tuple[str, str]:
    """抓取 URL 页面并提取正文内容，返回 (title, markdown_content)。

    使用 trafilatura 库完成网页下载与正文提取。
    """
    if not _HAS_TRAFILATURA:
        raise ImportError(
            "需要安装 trafilatura 库：pip install trafilatura"
        )

    # 下载页面
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        logger.warning("无法下载 URL: %s", url)
        return ("", "")

    # 提取正文（Markdown 格式输出）
    content = trafilatura.extract(
        downloaded,
        output_format="txt",
        include_links=True,
        include_tables=True,
    )
    if not content:
        logger.warning("无法从 URL 提取正文: %s", url)
        return ("", "")

    # 提取标题
    metadata = trafilatura.extract_metadata(downloaded)
    title = ""
    if metadata and metadata.title:
        title = metadata.title

    return (title, content)


def convert_html_to_markdown(html: str) -> str:
    """将 HTML 字符串转换为 Markdown。

    使用 markdownify 库完成转换。
    """
    if not _HAS_MARKDOWNIFY:
        raise ImportError(
            "需要安装 markdownify 库：pip install markdownify"
        )

    return md(html, heading_style="ATX", strip=["img", "script", "style"])
