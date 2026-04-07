"""Wiki 文件管理器 — 读写/链接 Wiki 页面，更新索引"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from ..config import get_config
from ..models.schemas import WikiPage, WikiPageSummary

# [[wikilink]] 正则：匹配 [[slug]] 或 [[slug|显示文本]]
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


class WikiManager:
    """管理 wiki/ 目录下的所有 Markdown 页面"""

    def __init__(self) -> None:
        cfg = get_config().data
        self.wiki_path = cfg.wiki_path
        self.pages_path = cfg.pages_path
        self.index_path = cfg.index_path
        self.log_path = cfg.log_path
        self.overview_path = cfg.overview_path
        # 确保目录存在
        self.pages_path.mkdir(parents=True, exist_ok=True)

    # ── 读写页面 ──

    def read_page(self, slug: str) -> WikiPage | None:
        """读取指定 slug 的页面"""
        path = self.pages_path / f"{slug}.md"
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8")
        title = self._extract_title(content)
        outlinks = self.extract_links(content)
        backlinks = self.get_backlinks(slug)
        category = self._guess_category(content, slug)
        stat = path.stat()
        return WikiPage(
            slug=slug,
            title=title,
            content=content,
            backlinks=backlinks,
            outlinks=outlinks,
            category=category,
            updated_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        )

    def write_page(self, slug: str, content: str, title: str = "") -> None:
        """写入页面（创建或覆盖）"""
        path = self.pages_path / f"{slug}.md"
        if title and not content.startswith(f"# {title}"):
            content = f"# {title}\n\n{content}"
        path.write_text(content, encoding="utf-8")

    def delete_page(self, slug: str) -> bool:
        """删除页面"""
        path = self.pages_path / f"{slug}.md"
        if path.exists():
            path.unlink()
            return True
        return False

    def list_pages(self) -> list[WikiPageSummary]:
        """列出所有页面的摘要"""
        pages: list[WikiPageSummary] = []
        for f in sorted(self.pages_path.glob("*.md")):
            content = f.read_text(encoding="utf-8")
            slug = f.stem
            title = self._extract_title(content)
            summary = self._extract_summary(content)
            category = self._guess_category(content, slug)
            pages.append(WikiPageSummary(
                slug=slug, title=title, summary=summary, category=category
            ))
        return pages

    def page_exists(self, slug: str) -> bool:
        """检查页面是否存在"""
        return (self.pages_path / f"{slug}.md").exists()

    # ── 链接管理 ──

    @staticmethod
    def extract_links(content: str) -> list[str]:
        """从内容中提取所有 [[wikilinks]] 的 slug"""
        return list(dict.fromkeys(WIKILINK_RE.findall(content)))

    def get_backlinks(self, slug: str) -> list[str]:
        """获取链接到指定 slug 的所有页面"""
        backlinks: list[str] = []
        for f in self.pages_path.glob("*.md"):
            if f.stem == slug:
                continue
            content = f.read_text(encoding="utf-8")
            if slug in self.extract_links(content):
                backlinks.append(f.stem)
        return backlinks

    def get_all_links(self) -> dict[str, list[str]]:
        """获取所有页面的出链映射 {slug: [target_slugs]}"""
        links: dict[str, list[str]] = {}
        for f in self.pages_path.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            links[f.stem] = self.extract_links(content)
        return links

    # ── 索引管理 ──

    def read_index(self) -> str:
        """读取 index.md"""
        if self.index_path.exists():
            return self.index_path.read_text(encoding="utf-8")
        return ""

    def update_index(self) -> None:
        """从所有页面重新生成 index.md"""
        pages = self.list_pages()
        categories: dict[str, list[WikiPageSummary]] = {}
        for p in pages:
            cat = p.category or "其他"
            categories.setdefault(cat, []).append(p)

        lines = ["# Wiki 索引\n"]
        lines.append("> 本文件是 Wiki 知识库的主索引，由 LLM 自动维护。\n")
        lines.append(f"> 共 {len(pages)} 个页面，最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        cat_names = {"paper": "论文", "concept": "概念", "entity": "实体", "source": "来源摘要"}
        for cat_key in ["concept", "paper", "entity", "source"]:
            cat_label = cat_names.get(cat_key, cat_key)
            items = categories.pop(cat_key, [])
            lines.append(f"\n## {cat_label}\n")
            if items:
                for p in items:
                    lines.append(f"- [[{p.slug}]] — {p.summary}")
            else:
                lines.append(f"_（尚无{cat_label}页面）_")

        # 剩余分类
        for cat_key, items in categories.items():
            lines.append(f"\n## {cat_key}\n")
            for p in items:
                lines.append(f"- [[{p.slug}]] — {p.summary}")

        self.index_path.write_text("\n".join(lines), encoding="utf-8")

    # ── 日志 ──

    def append_log(self, operation: str, details: str, affected_pages: list[str] | None = None) -> None:
        """向 log.md 追加一条记录"""
        pages_str = ", ".join(affected_pages) if affected_pages else "-"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"| {timestamp} | {operation} | {details} | {pages_str} |\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def read_log(self, limit: int = 100) -> str:
        """读取日志（最近 N 条）"""
        if not self.log_path.exists():
            return ""
        lines = self.log_path.read_text(encoding="utf-8").splitlines()
        # 表头 + 分隔行 + 最近的条目
        header = lines[:3] if len(lines) >= 3 else lines
        entries = lines[3:]
        recent = entries[-limit:] if len(entries) > limit else entries
        return "\n".join(header + recent)

    # ── 总览 ──

    def read_overview(self) -> str:
        """读取 overview.md"""
        if self.overview_path.exists():
            return self.overview_path.read_text(encoding="utf-8")
        return ""

    def write_overview(self, content: str) -> None:
        """更新 overview.md"""
        self.overview_path.write_text(content, encoding="utf-8")

    # ── 原始资料管理 ──

    def save_raw(self, content: str, source_type: str, filename: str) -> Path:
        """保存原始资料到 raw/ 目录"""
        cfg = get_config().data
        raw_dir = cfg.raw_path / source_type
        raw_dir.mkdir(parents=True, exist_ok=True)
        path = raw_dir / filename
        path.write_text(content, encoding="utf-8")
        return path

    def save_asset(self, data: bytes, filename: str) -> Path:
        """保存二进制资产到 assets/ 目录"""
        cfg = get_config().data
        cfg.assets_path.mkdir(parents=True, exist_ok=True)
        path = cfg.assets_path / filename
        path.write_bytes(data)
        return path

    # ── 内部工具 ──

    @staticmethod
    def _extract_title(content: str) -> str:
        """从 Markdown 内容提取 H1 标题"""
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("# ") and not line.startswith("## "):
                return line[2:].strip()
        return "无标题"

    @staticmethod
    def _extract_summary(content: str, max_len: int = 120) -> str:
        """从内容提取摘要（第一段非标题文本）"""
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(">") or line.startswith("|"):
                continue
            if line.startswith("- **") or line.startswith("_（"):
                continue
            return line[:max_len]
        return ""

    @staticmethod
    def _guess_category(content: str, slug: str) -> str:
        """根据内容和 slug 猜测页面类别"""
        content_lower = content.lower()
        if "## 元数据" in content and ("## 背景与问题" in content or "## 方法论" in content):
            return "paper"
        if "## metadata" in content_lower and "## background" in content_lower:
            return "paper"
        if slug.startswith("paper-") or slug.startswith("论文-"):
            return "paper"
        if "## 来源" in content or "[来源:" in content:
            return "source"
        return "concept"


def slugify(text: str) -> str:
    """将文本转换为 slug 格式"""
    # 保留中文字符、英文字母、数字
    text = text.lower().strip()
    text = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")
