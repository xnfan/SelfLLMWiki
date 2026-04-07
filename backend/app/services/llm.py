"""LLM 提供商抽象层 — 统一 OpenAI 兼容 / Anthropic Claude 接口"""

from __future__ import annotations

import logging
from typing import AsyncIterator, Protocol, runtime_checkable

from ..config import LLMProviderConfig, get_config

logger = logging.getLogger(__name__)


# ── Protocol 定义 ──

@runtime_checkable
class LLMProvider(Protocol):
    """LLM 提供商协议"""

    async def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 8192,
        temperature: float = 0.3,
    ) -> str:
        """发送聊天请求并返回完整响应文本"""
        ...

    async def complete_stream(
        self,
        system: str,
        user: str,
        max_tokens: int = 8192,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        """发送聊天请求并以流式方式逐 token 返回"""
        ...


# ── OpenAI 兼容提供商 ──

class OpenAICompatibleProvider:
    """基于 openai 库的 AsyncOpenAI 客户端，兼容所有 OpenAI API 格式的提供商（包括 Ollama、vLLM 等）"""

    def __init__(self, config: LLMProviderConfig) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ImportError(
                "需要安装 openai 库：pip install openai"
            ) from exc

        self.config = config
        self.client = AsyncOpenAI(
            base_url=config.base_url or None,
            api_key=config.api_key or "EMPTY",
        )
        self.model = config.model

    async def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 8192,
        temperature: float = 0.3,
    ) -> str:
        """调用 chat.completions.create 获取完整响应"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    async def complete_stream(
        self,
        system: str,
        user: str,
        max_tokens: int = 8192,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        """调用 chat.completions.create(stream=True) 流式返回"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


# ── Anthropic Claude 提供商 ──

class ClaudeProvider:
    """基于 anthropic 库的 AsyncAnthropic 客户端"""

    def __init__(self, config: LLMProviderConfig) -> None:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise ImportError(
                "需要安装 anthropic 库：pip install anthropic"
            ) from exc

        self.config = config
        self.client = AsyncAnthropic(
            api_key=config.api_key or None,
            base_url=config.base_url or None,
        )
        self.model = config.model

    async def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 8192,
        temperature: float = 0.3,
    ) -> str:
        """调用 messages.create 获取完整响应"""
        kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user}],
        }
        if system:
            kwargs["system"] = system

        resp = await self.client.messages.create(**kwargs)
        # Anthropic 返回的 content 是一个块列表
        parts = []
        for block in resp.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "".join(parts)

    async def complete_stream(
        self,
        system: str,
        user: str,
        max_tokens: int = 8192,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        """调用 messages.create(stream=True) 流式返回"""
        kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user}],
            "stream": True,
        }
        if system:
            kwargs["system"] = system

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text


# ── 工厂函数 ──

def create_provider(config: LLMProviderConfig) -> LLMProvider:
    """根据配置创建对应的 LLM 提供商实例"""
    fmt = config.format.lower()
    if fmt == "anthropic":
        return ClaudeProvider(config)  # type: ignore[return-value]
    # 默认使用 OpenAI 兼容格式（openai / ollama / vllm 等）
    return OpenAICompatibleProvider(config)  # type: ignore[return-value]


def get_llm(provider_name: str | None = None) -> LLMProvider:
    """便捷函数：从全局配置获取 LLM 提供商实例"""
    cfg = get_config()
    provider_cfg = cfg.llm.get_provider(provider_name)
    logger.info("使用 LLM 提供商: %s (model=%s)", provider_cfg.name, provider_cfg.model)
    return create_provider(provider_cfg)
