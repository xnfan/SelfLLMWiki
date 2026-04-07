"""Wiki 健康检查服务 — 检测孤立页面、缺失链接、矛盾等问题"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from ..config import get_config
from ..models.schemas import LintIssue, LintReport
from .ingest_service import load_prompt
from .llm import get_llm
from .wiki_manager import WikiManager

logger = logging.getLogger(__name__)

# 匹配 JSON 数组（可能被 ```json ... ``` 包裹）
_JSON_ARRAY_RE = re.compile(r"```json\s*\n(\[.*?\])\s*\n```", re.DOTALL)


def _extract_json_array(text: str) -> list[dict]:
    """从 LLM 输出中提取 JSON 数组"""
    # 先尝试匹配 ```json ... ```
    m = _JSON_ARRAY_RE.search(text)
    if m:
        return json.loads(m.group(1))
    # 尝试直接解析（找第一个 [ 到最后一个 ]）
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return []


class LintService:
    """Wiki 健康检查服务"""

    def __init__(self) -> None:
        self.wiki = WikiManager()

    async def lint(self) -> LintReport:
        """执行完整的 Wiki 健康检查

        Returns
        -------
        LintReport
            检查报告，包含所有发现的问题
        """
        issues: list[LintIssue] = []

        # 获取所有页面和链接信息
        pages = self.wiki.list_pages()
        all_slugs = {p.slug for p in pages}
        all_links = self.wiki.get_all_links()  # {slug: [target_slugs]}

        total_pages = len(pages)
        if total_pages == 0:
            return LintReport(
                issues=[],
                total_pages=0,
                healthy_pages=0,
                timestamp=datetime.now().isoformat(),
            )

        # ── 1. 检查孤立页面（没有入链的页面）──
        # 构建入链映射
        inlink_count: dict[str, int] = {slug: 0 for slug in all_slugs}
        for _source, targets in all_links.items():
            for target in targets:
                if target in inlink_count:
                    inlink_count[target] += 1

        orphan_pages = [slug for slug, count in inlink_count.items() if count == 0]
        if orphan_pages:
            issues.append(LintIssue(
                category="孤立页面",
                severity="中",
                pages=orphan_pages,
                description=f"发现 {len(orphan_pages)} 个孤立页面（没有其他页面链接到它们）",
                suggestion="考虑在相关页面中添加指向这些页面的 [[wikilinks]]",
            ))

        # ── 2. 检查缺失页面（链接到不存在的页面）──
        missing_targets: dict[str, list[str]] = {}  # {missing_slug: [source_slugs]}
        for source, targets in all_links.items():
            for target in targets:
                if target not in all_slugs:
                    missing_targets.setdefault(target, []).append(source)

        if missing_targets:
            for missing_slug, sources in missing_targets.items():
                issues.append(LintIssue(
                    category="缺失页面",
                    severity="高",
                    pages=sources,
                    description=f"页面 [[{missing_slug}]] 不存在，但被 {len(sources)} 个页面引用",
                    suggestion=f"创建页面 '{missing_slug}' 或修正链接",
                ))

        # ── 3. 调用 LLM 做深度分析 ──
        try:
            llm_issues = await self._llm_analysis(pages)
            issues.extend(llm_issues)
        except Exception:
            logger.exception("LLM 深度分析失败，仅返回静态检查结果")

        # ── 4. 计算健康页面数 ──
        problematic_pages = set()
        for issue in issues:
            problematic_pages.update(issue.pages)
        healthy_pages = total_pages - len(problematic_pages & all_slugs)

        return LintReport(
            issues=issues,
            total_pages=total_pages,
            healthy_pages=max(healthy_pages, 0),
            timestamp=datetime.now().isoformat(),
        )

    async def _llm_analysis(self, pages: list) -> list[LintIssue]:
        """使用 LLM 对 Wiki 内容进行深度分析"""
        # 构建页面摘要文本
        pages_summary_lines = []
        for p in pages:
            pages_summary_lines.append(
                f"- [[{p.slug}]] ({p.category}): {p.title} — {p.summary}"
            )
        pages_summary = "\n".join(pages_summary_lines)

        index_content = self.wiki.read_index()

        # 加载提示词并调用 LLM
        prompt_template = load_prompt("lint")
        user_prompt = prompt_template.format(
            index_content=index_content or "（索引为空）",
            pages_summary=pages_summary or "（无页面）",
        )

        llm = get_llm()
        cfg = get_config()
        provider_cfg = cfg.llm.get_provider()
        response = await llm.complete(
            system="",
            user=user_prompt,
            max_tokens=provider_cfg.max_tokens,
            temperature=provider_cfg.temperature,
        )

        # 解析 LLM 返回的 JSON 数组
        raw_issues = _extract_json_array(response)
        llm_issues: list[LintIssue] = []
        for item in raw_issues:
            if isinstance(item, dict):
                try:
                    llm_issues.append(LintIssue(
                        category=item.get("category", "其他"),
                        severity=item.get("severity", "低"),
                        pages=item.get("pages", []),
                        description=item.get("description", ""),
                        suggestion=item.get("suggestion", ""),
                    ))
                except Exception:
                    logger.warning("无法解析 LLM 返回的 lint issue: %s", item)

        return llm_issues
