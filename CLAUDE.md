# SelfLLMWiki — Claude Code 配置

## 项目概述
自托管 LLM Wiki 知识库系统，基于 Karpathy 的 LLM Wiki 概念。
Python 后端（FastAPI） + Vue 3 前端 + Markdown 知识库。

## 技术栈
- 后端: Python 3.11+, FastAPI, Pydantic
- 前端: Vue 3 + Vite + TypeScript + D3.js
- LLM: OpenAI 兼容 API / Anthropic Claude API（可配置）
- PDF: Marker（含 Surya OCR）
- 搜索: DuckDuckGo + Semantic Scholar

## 关键目录
- `backend/` — FastAPI 后端
- `frontend/` — Vue 3 前端
- `data/` — Wiki 数据（raw/wiki/assets 三层架构）
- `config.yaml` — 用户配置

## 启动命令
```bash
# 后端
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# 前端
cd frontend && npm install && npm run dev
```

## 编码规范
- Python: 中文注释，async/await，类型注解
- TypeScript: `<script setup lang="ts">`，中文 UI
- 文件编码: UTF-8
- API: RESTful，前缀 /api/
