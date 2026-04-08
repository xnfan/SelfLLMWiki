"""HTML / URL -> Markdown 转换服务"""

from __future__ import annotations

import logging
import re

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

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    httpx = None  # type: ignore[assignment]
    _HAS_HTTPX = False


# 知乎文章 API 端点
ZHIHU_API_PATTERN = re.compile(r"https?://zhuanlan\.zhihu\.com/p/(\d+)")


def _extract_zhihu_article_id(url: str) -> str | None:
    """从知乎专栏 URL 提取文章 ID"""
    match = ZHIHU_API_PATTERN.match(url)
    if match:
        return match.group(1)
    return None


def _fetch_zhihu_article(article_id: str) -> tuple[str, str]:
    """使用知乎 API 获取文章内容"""
    if not _HAS_HTTPX:
        return ("", "")

    try:
        import json
        api_url = f"https://www.zhihu.com/api/v4/articles/{article_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        import httpx
        with httpx.Client(timeout=30.0, headers=headers) as client:
            resp = client.get(api_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            title = data.get("title", "")
            content_html = data.get("content", "")

            # 将 HTML 转换为 Markdown
            if content_html and _HAS_MARKDOWNIFY:
                content = md(content_html, heading_style="ATX", strip=["script", "style"])
            else:
                # 简单清理 HTML 标签
                content = re.sub(r"<[^>]+>", "", content_html)

            return (title, content.strip())

    except Exception as e:
        logger.warning(f"知乎 API 获取失败: {e}")
        return ("", "")


def convert_url_to_markdown(url: str) -> tuple[str, str]:
    """抓取 URL 页面并提取正文内容，返回 (title, markdown_content)。

    使用 trafilatura 库完成网页下载与正文提取。
    对特殊网站（如知乎）使用专门的 API。
    """
    if not _HAS_TRAFILATURA:
        raise ImportError(
            "需要安装 trafilatura 库：pip install trafilatura"
        )

    # 特殊处理知乎专栏文章
    zhihu_id = _extract_zhihu_article_id(url)
    if zhihu_id:
        logger.info(f"检测到知乎文章，使用 API 获取: {url}")
        title, content = _fetch_zhihu_article(zhihu_id)
        if content:
            return (title, content)
        logger.warning(f"知乎 API 获取失败，尝试通用方法: {url}")

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
