"""SelfLLMWiki 配置管理模块"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class LLMProviderConfig(BaseModel):
    """单个 LLM 提供商配置"""
    name: str
    format: str = "openai"  # "openai" | "anthropic"
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    max_tokens: int = 8192
    temperature: float = 0.3


class LLMConfig(BaseModel):
    """LLM 配置"""
    providers: list[LLMProviderConfig] = Field(default_factory=list)
    default: str = "local-ollama"

    def get_provider(self, name: str | None = None) -> LLMProviderConfig:
        """获取指定名称的提供商，或默认提供商"""
        target = name or self.default
        for p in self.providers:
            if p.name == target:
                return p
        if self.providers:
            return self.providers[0]
        raise ValueError(f"未找到 LLM 提供商: {target}")


class DataConfig(BaseModel):
    """数据目录配置"""
    root: str = "./data"
    raw_dir: str = "raw"
    wiki_dir: str = "wiki"
    assets_dir: str = "assets"

    @property
    def root_path(self) -> Path:
        return Path(self.root).resolve()

    @property
    def raw_path(self) -> Path:
        return self.root_path / self.raw_dir

    @property
    def wiki_path(self) -> Path:
        return self.root_path / self.wiki_dir

    @property
    def assets_path(self) -> Path:
        return self.root_path / self.assets_dir

    @property
    def pages_path(self) -> Path:
        return self.wiki_path / "pages"

    @property
    def index_path(self) -> Path:
        return self.wiki_path / "index.md"

    @property
    def log_path(self) -> Path:
        return self.wiki_path / "log.md"

    @property
    def overview_path(self) -> Path:
        return self.wiki_path / "overview.md"


class PDFConfig(BaseModel):
    """PDF 处理配置"""
    converter: str = "marker"  # "marker" | "pymupdf4llm"
    use_gpu: bool = True
    use_llm: bool = False


class LanguageConfig(BaseModel):
    """语言配置"""
    ocr_languages: list[str] = Field(default_factory=lambda: ["en", "zh"])
    wiki_language: str = "zh"


class SearchConfig(BaseModel):
    """搜索配置"""
    engine: str = "duckduckgo"
    searxng_url: str = ""


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True


class AppConfig(BaseModel):
    """应用总配置"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    pdf: PDFConfig = Field(default_factory=PDFConfig)
    language: LanguageConfig = Field(default_factory=LanguageConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """从 YAML 文件加载配置"""
    if config_path is None:
        # 从项目根目录向上查找 config.yaml
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            candidate = parent / "config.yaml"
            if candidate.exists():
                config_path = candidate
                break

    if config_path is None or not Path(config_path).exists():
        return AppConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    return AppConfig(**raw)


# 全局配置实例（延迟初始化）
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """获取全局配置（单例）"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: str | Path | None = None) -> AppConfig:
    """重新加载配置"""
    global _config
    _config = load_config(config_path)
    return _config
