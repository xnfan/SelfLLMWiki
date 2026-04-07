"""摄入服务 — 将文本/URL 内容处理后写入 Wiki"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from ..config import get_config
from ..models.schemas import IngestResponse
from .html_converter import convert_url_to_markdown
from .llm import get_llm
from .wiki_manager import WikiManager

logger = logging.getLogger(__name__)

# 提示词模板目录
_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
    """从 backend/app/prompts/{name}.md 读取提示词模板。

    模板中使用 {xxx} 占位符，调用方通过 str.format() 替换。
    """
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"提示词模板不存在: {path}")
    return path.read_text(encoding="utf-8")


# ── 解析 LLM 返回内容的正则 ──

# 匹配 JSON 块（可能被 ```json ... ``` 包裹）
_JSON_RE = re.compile(r"```json\s*\n(.*?)\n\s*```", re.DOTALL)
# 匹配页面内容块
_PAGE_RE = re.compile(
    r"---PAGE:\s*(\S+)\s*---\s*\n(.*?)\n\s*---END PAGE---",
    re.DOTALL,
)


def _extract_json(text: str) -> dict:
    """从 LLM 输出中提取 JSON 对象"""
    # 先尝试匹配 ```json ... ```
    m = _JSON_RE.search(text)
    if m:
        return json.loads(m.group(1))
    # 尝试直接解析（找第一个 { 到最后一个 }）
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start : end + 1])
    return {}


def _extract_pages(text: str) -> dict[str, str]:
    """从 LLM 输出中提取页面内容块

    返回 {slug: markdown_content}
    """
    pages: dict[str, str] = {}
    for m in _PAGE_RE.finditer(text):
        slug = m.group(1).strip()
        content = m.group(2).strip()
        pages[slug] = content
    return pages


class IngestService:
    """摄入服务：将外部内容（文本、URL）处理后写入 Wiki"""

    def __init__(self) -> None:
        self.wiki = WikiManager()

    async def ingest_text(
        self,
        content: str,
        source_type: str,
        title: str = "",
    ) -> IngestResponse:
        """摄入纯文本内容

        Parameters
        ----------
        content : str
            原始文本内容
        source_type : str
            来源类型（article / web / note 等）
        title : str
            可选标题

        Returns
        -------
        IngestResponse
            摄入结果
        """
        try:
            # 1. 保存原始资料到 raw/
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{title or 'untitled'}.md"
            self.wiki.save_raw(content, source_type, filename)

            # 2. 读取当前 wiki 索引
            index_content = self.wiki.read_index()

            # 3. 加载提示词并调用 LLM
            prompt_template = load_prompt("ingest")
            user_prompt = prompt_template.format(
                index_content=index_content or "（索引为空，这是一个全新的 Wiki）",
                source_content=content,
                source_type=source_type,
            )
            system_prompt = ""  # 提示词模板本身包含角色设定

            llm = get_llm()
            cfg = get_config()
            llm_response = await llm.complete(
                system=system_prompt,
                user=user_prompt,
                max_tokens=cfg.llm.get_provider().max_tokens,
                temperature=cfg.llm.get_provider().temperature,
            )

            # 4. 解析 LLM 返回的 JSON 和页面内容
            result_json = _extract_json(llm_response)
            page_contents = _extract_pages(llm_response)

            pages_created: list[str] = []
            pages_updated: list[str] = []

            # 5. 写入 wiki 页面
            for page_info in result_json.get("pages_created", []):
                slug = page_info.get("slug", "")
                page_title = page_info.get("title", "")
                if slug and slug in page_contents:
                    self.wiki.write_page(slug, page_contents[slug], page_title)
                    pages_created.append(slug)

            for page_info in result_json.get("pages_updated", []):
                slug = page_info.get("slug", "")
                if slug and slug in page_contents:
                    self.wiki.write_page(slug, page_contents[slug])
                    pages_updated.append(slug)

            # 6. 更新 index.md
            self.wiki.update_index()

            # 7. 记录日志
            all_affected = pages_created + pages_updated
            self.wiki.append_log(
                operation="ingest",
                details=f"摄入 {source_type} 内容，标题: {title or '无'}",
                affected_pages=all_affected,
            )

            return IngestResponse(
                success=True,
                pages_created=pages_created,
                pages_updated=pages_updated,
                message=f"成功摄入内容，创建 {len(pages_created)} 个页面，更新 {len(pages_updated)} 个页面",
            )

        except Exception as exc:
            logger.exception("摄入文本失败")
            return IngestResponse(
                success=False,
                message=f"摄入失败: {exc}",
            )

    async def ingest_url(self, url: str) -> IngestResponse:
        """摄入 URL 内容

        Parameters
        ----------
        url : str
            要摄入的网页 URL

        Returns
        -------
        IngestResponse
            摄入结果
        """
        try:
            # 抓取 URL 内容
            title, content = convert_url_to_markdown(url)
            if not content:
                return IngestResponse(
                    success=False,
                    message=f"无法从 URL 提取内容: {url}",
                )

            # 在内容头部添加来源信息
            source_header = f"来源 URL: {url}\n抓取时间: {datetime.now().isoformat()}\n\n"
            full_content = source_header + content

            return await self.ingest_text(
                content=full_content,
                source_type="web",
                title=title or url,
            )

        except ImportError as exc:
            return IngestResponse(success=False, message=str(exc))
        except Exception as exc:
            logger.exception("摄入 URL 失败: %s", url)
            return IngestResponse(
                success=False,
                message=f"摄入 URL 失败: {exc}",
            )
