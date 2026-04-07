"""Pydantic 数据模型定义"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── 通用 ──

class SourceType(str, Enum):
    PAPER = "paper"
    ARTICLE = "article"
    WEB = "web"
    NOTE = "note"


class OperationType(str, Enum):
    INGEST = "ingest"
    QUERY = "query"
    DEPOSIT = "deposit"
    LINT = "lint"
    PAPER_INGEST = "paper_ingest"
    EXPANSION = "expansion"


# ── Wiki 页面 ──

class WikiPage(BaseModel):
    slug: str
    title: str
    content: str
    backlinks: list[str] = Field(default_factory=list)
    outlinks: list[str] = Field(default_factory=list)
    category: str = ""  # concept / paper / entity / source
    updated_at: str = ""


class WikiPageSummary(BaseModel):
    slug: str
    title: str
    summary: str = ""
    category: str = ""


class WikiPageCreate(BaseModel):
    slug: str
    title: str
    content: str
    category: str = ""


class WikiPageUpdate(BaseModel):
    content: str
    title: str | None = None


# ── 图谱 ──

class GraphNode(BaseModel):
    id: str  # slug
    label: str  # title
    category: str = ""
    size: int = 1  # 连接数


class GraphEdge(BaseModel):
    source: str
    target: str


class GraphData(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


# ── 摄入 ──

class IngestRequest(BaseModel):
    content: str = ""  # 文本内容或 URL
    source_type: SourceType = SourceType.NOTE
    url: str = ""  # 如果是 URL 摄入
    title: str = ""  # 可选标题


class IngestResponse(BaseModel):
    success: bool
    pages_created: list[str] = Field(default_factory=list)
    pages_updated: list[str] = Field(default_factory=list)
    message: str = ""


# ── 查询 ──

class QueryRequest(BaseModel):
    question: str
    provider: str | None = None  # 可选指定 LLM 提供商


class QueryResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    can_deposit: bool = True


# ── 存入 ──

class DepositRequest(BaseModel):
    content: str
    title: str
    slug: str = ""  # 如果为空则从 title 自动生成


class DepositResponse(BaseModel):
    success: bool
    slug: str
    message: str = ""


# ── 健康检查 ──

class LintIssue(BaseModel):
    category: str
    severity: str  # 高 / 中 / 低
    pages: list[str] = Field(default_factory=list)
    description: str
    suggestion: str = ""


class LintReport(BaseModel):
    issues: list[LintIssue] = Field(default_factory=list)
    total_pages: int = 0
    healthy_pages: int = 0
    timestamp: str = ""


# ── 论文 ──

class PaperSearchRequest(BaseModel):
    query: str
    limit: int = 20


class PaperInfo(BaseModel):
    paper_id: str = ""
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    venue: str = ""
    citation_count: int = 0
    abstract: str = ""
    open_access_url: str = ""
    doi: str = ""
    in_wiki: bool = False  # 是否已在 Wiki 中


class PaperSearchResponse(BaseModel):
    papers: list[PaperInfo] = Field(default_factory=list)
    total: int = 0


class PaperExpandRequest(BaseModel):
    paper_id: str = ""  # Semantic Scholar paper ID
    topic: str = ""  # 或者按主题拓展
    limit: int = 20


class PaperDownloadRequest(BaseModel):
    papers: list[PaperInfo]


class PaperDownloadResponse(BaseModel):
    downloaded: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)
    message: str = ""


# ── 网络 ──

class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 10


class WebSearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""


class WebSearchResponse(BaseModel):
    results: list[WebSearchResult] = Field(default_factory=list)


class WebFetchRequest(BaseModel):
    url: str


class WebFetchResponse(BaseModel):
    title: str = ""
    content: str = ""
    url: str = ""


# ── 日志 ──

class LogEntry(BaseModel):
    timestamp: str
    operation: str
    details: str
    affected_pages: list[str] = Field(default_factory=list)


# ── 进度 ──

class ProgressUpdate(BaseModel):
    task_id: str
    status: str  # "running" | "completed" | "error"
    progress: float = 0.0  # 0.0 - 1.0
    message: str = ""


# ── 原始资料 ──

class RawFileInfo(BaseModel):
    path: str
    name: str
    type: str  # papers / articles / web / notes
    size: int = 0
    modified: str = ""
