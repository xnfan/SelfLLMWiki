"""JSON 解析工具 — 从 LLM 输出中提取结构化数据"""

from __future__ import annotations

import json
import re

# 匹配 JSON 块（可能被 ```json ... ``` 包裹）
_JSON_RE = re.compile(r"```json\s*\n(.*?)\n\s*```", re.DOTALL)
# 匹配 JSON 数组（可能被 ```json ... ``` 包裹）
_JSON_ARRAY_RE = re.compile(r"```json\s*\n(\[.*?\])\s*\n```", re.DOTALL)


def extract_json(text: str) -> dict:
    """从 LLM 输出中提取 JSON 对象

    首先尝试匹配 ```json ... ``` 代码块，
    如果失败则尝试直接解析（找第一个 { 到最后一个 }）

    Parameters
    ----------
    text : str
        包含 JSON 的文本

    Returns
    -------
    dict
        解析后的 JSON 对象，失败返回空字典
    """
    # 先尝试匹配 ```json ... ```
    m = _JSON_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试直接解析（找第一个 { 到最后一个 }）
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return {}


def extract_json_array(text: str) -> list[dict]:
    """从 LLM 输出中提取 JSON 数组

    首先尝试匹配 ```json ... ``` 代码块，
    如果失败则尝试直接解析（找第一个 [ 到最后一个 ]）

    Parameters
    ----------
    text : str
        包含 JSON 数组的文本

    Returns
    -------
    list[dict]
        解析后的 JSON 数组，失败返回空列表
    """
    # 先尝试匹配 ```json ... ```
    m = _JSON_ARRAY_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试直接解析（找第一个 [ 到最后一个 ]）
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and start < end:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return []
