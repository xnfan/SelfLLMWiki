"""查询服务 — 基于 Wiki 内容回答用户问题"""

from __future__ import annotations

import logging
import re

from ..config import get_config
from ..models.schemas import QueryResponse
from .ingest_service import load_prompt
from .llm import get_llm
from .wiki_manager import WikiManager

logger = logging.getLogger(__name__)

# 简单的中英文分词（按空格、标点拆分）
_WORD_SPLIT_RE = re.compile(r"[\s,，。！？；：、\.\!\?\;\:]+")


def _extract_keywords(text: str) -> list[str]:
    """从文本中提取关键词（简单分词）"""
    words = _WORD_SPLIT_RE.split(text.strip())
    # 过滤过短的词
    return [w for w in words if len(w) >= 2]


def _score_page(keywords: list[str], title: str, summary: str) -> int:
    """计算页面与关键词的匹配分数"""
    score = 0
    text = (title + " " + summary).lower()
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in text:
            score += 1
            # 标题匹配加分
            if kw_lower in title.lower():
                score += 2
    return score


class QueryService:
    """查询服务：基于 Wiki 知识库回答用户问题"""

    def __init__(self) -> None:
        self.wiki = WikiManager()

    async def query(
        self,
        question: str,
        provider: str | None = None,
    ) -> QueryResponse:
        """回答用户问题

        Parameters
        ----------
        question : str
            用户提出的问题
        provider : str | None
            可选指定 LLM 提供商名称

        Returns
        -------
        QueryResponse
            包含回答和来源页面的响应
        """
        try:
            # 1. 读取 index.md
            index_content = self.wiki.read_index()

            # 2. 根据问题找到相关页面（关键词匹配）
            keywords = _extract_keywords(question)
            pages_summary = self.wiki.list_pages()

            # 计算每个页面的相关性分数
            scored_pages = []
            for page in pages_summary:
                score = _score_page(keywords, page.title, page.summary)
                if score > 0:
                    scored_pages.append((score, page))

            # 按分数降序排列，取前 10 个
            scored_pages.sort(key=lambda x: x[0], reverse=True)
            relevant_page_summaries = scored_pages[:10]

            # 3. 读取相关页面内容
            relevant_contents: list[str] = []
            source_slugs: list[str] = []

            for _score, page_summary in relevant_page_summaries:
                page = self.wiki.read_page(page_summary.slug)
                if page:
                    relevant_contents.append(
                        f"## [[{page.slug}]] — {page.title}\n\n{page.content}"
                    )
                    source_slugs.append(page.slug)

            # 如果没有找到相关页面，仍然用索引作为上下文
            relevant_pages_text = "\n\n---\n\n".join(relevant_contents) if relevant_contents else "（未找到直接相关的页面）"

            # 4. 调用 LLM 用 query 提示词回答
            prompt_template = load_prompt("query")
            user_prompt = prompt_template.format(
                index_content=index_content or "（索引为空）",
                relevant_pages=relevant_pages_text,
                question=question,
            )

            llm = get_llm(provider)
            cfg = get_config()
            provider_cfg = cfg.llm.get_provider(provider)
            answer = await llm.complete(
                system="",
                user=user_prompt,
                max_tokens=provider_cfg.max_tokens,
                temperature=provider_cfg.temperature,
            )

            # 5. 记录日志
            self.wiki.append_log(
                operation="query",
                details=f"查询: {question[:80]}",
                affected_pages=source_slugs,
            )

            return QueryResponse(
                answer=answer,
                sources=source_slugs,
                can_deposit=True,
            )

        except Exception as exc:
            logger.exception("查询失败: %s", question)
            return QueryResponse(
                answer=f"查询出错: {exc}",
                sources=[],
                can_deposit=False,
            )
