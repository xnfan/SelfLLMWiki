"""HTML / URL -> Markdown 转换服务

使用 httpx 下载网页（解决 SSL 和 UA 问题），再用 trafilatura 提取正文。
对知乎等强反爬站点提供明确的错误提示。
"""

from __future__ import annotations

import logging
import re

import httpx

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


# 需要特殊处理的域名
_JS_RENDERED_DOMAINS = [
    "zhuanlan.zhihu.com",
    "www.zhihu.com",
    "zhihu.com",
    "mp.weixin.qq.com",  # 微信公众号
    "juejin.cn",         # 掘金
]

# 浏览器风格 HTTP 头
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def _is_js_rendered_site(url: str) -> bool:
    """检查 URL 是否属于需要 JS 渲染的站点"""
    for domain in _JS_RENDERED_DOMAINS:
        if domain in url:
            return True
    return False


def _fetch_html(url: str) -> str:
    """使用 httpx 下载网页 HTML

    解决 trafilatura 默认 fetch_url 的 SSL 证书和 User-Agent 问题。
    """
    try:
        with httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers=_BROWSER_HEADERS,
            verify=False,  # 兼容有 SSL 证书问题的环境
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text
    except httpx.HTTPStatusError as e:
        logger.warning("HTTP %d 下载 URL: %s", e.response.status_code, url)
        return ""
    except Exception as e:
        logger.warning("下载 URL 失败 %s: %s", url, e)
        return ""


def convert_url_to_markdown(url: str) -> tuple[str, str]:
    """抓取 URL 页面并提取正文内容，返回 (title, markdown_content)。

    流程：httpx 下载 HTML → trafilatura 提取正文。
    对 JS 渲染的站点返回明确的错误提示。
    """
    if not _HAS_TRAFILATURA:
        raise ImportError("需要安装 trafilatura 库：pip install trafilatura")

    # 检查是否为 JS 渲染站点
    if _is_js_rendered_site(url):
        logger.warning("JS 渲染站点，尝试抓取但可能失败: %s", url)

    # 使用 httpx 下载 HTML
    html = _fetch_html(url)
    if not html:
        if _is_js_rendered_site(url):
            logger.warning(
                "无法抓取 JS 渲染页面: %s。请手动复制页面内容后使用文本摄入。", url
            )
        return ("", "")

    # 检查是否为反爬验证页面
    if len(html) < 2000 and ("验证" in html or "安全验证" in html or "error" in html.lower()):
        logger.warning("页面返回了反爬验证: %s", url)
        return ("", "")

    # 使用 trafilatura 从 HTML 提取正文
    content = trafilatura.extract(
        html,
        output_format="txt",
        include_links=True,
        include_tables=True,
    )
    if not content:
        logger.warning("无法从 URL 提取正文: %s", url)
        return ("", "")

    # 提取标题
    metadata = trafilatura.extract_metadata(html)
    title = ""
    if metadata and metadata.title:
        title = metadata.title

    return (title, content)


def convert_html_to_markdown(html: str) -> str:
    """将 HTML 字符串转换为 Markdown。"""
    if not _HAS_MARKDOWNIFY:
        raise ImportError("需要安装 markdownify 库：pip install markdownify")

    return md(html, heading_style="ATX", strip=["img", "script", "style"])
