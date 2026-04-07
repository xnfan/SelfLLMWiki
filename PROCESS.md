# SelfLLMWiki 开发流程

本文档描述项目的开发规范和流程。

## 分支策略

- `main` - 稳定分支，仅通过 PR 合并
- `develop` - 开发分支，日常开发基于此
- `feature/*` - 特性分支
- `fix/*` - 修复分支

## 提交规范

```
<type>: <subject>

<body>
```

类型：
- `feat` - 新功能
- `fix` - 修复
- `docs` - 文档
- `style` - 格式调整
- `refactor` - 重构
- `test` - 测试
- `chore` - 构建/工具

示例：
```
feat: 添加 arXiv 论文搜索支持

- 实现 arXiv API 封装
- 添加多源自动切换逻辑
- 更新前端显示来源标签
```

## 开发环境

### 后端开发

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .  # 可编辑安装

# 启动开发服务器
python -m uvicorn app.main:app --reload --port 8001
```

### 前端开发

```bash
cd frontend
npm install

# 启动开发服务器
npm run dev

# 类型检查
npm run type-check

# 构建
npm run build
```

## 代码规范

### Python

- 使用 `ruff` 进行代码检查
- 类型注解必需
- 异步函数使用 `async/await`
- 中文注释和文档字符串

```bash
# 格式化
ruff format backend/

# 检查
ruff check backend/
```

### TypeScript/Vue

- 严格类型检查
- 组件使用 `<script setup lang="ts">`
- 中文 UI 文本
- CSS 使用 CSS 变量

```bash
# 类型检查
npm run type-check
```

## 测试

### 后端测试

```bash
cd backend
pytest tests/ -v
```

### 前端测试

```bash
cd frontend
npm run test
```

## 发布流程

1. 更新 `CHANGELOG.md`
2. 更新版本号（`backend/pyproject.toml` 和 `frontend/package.json`）
3. 创建 Git 标签：`git tag v0.1.0`
4. 推送到 GitHub：`git push origin main --tags`
5. 创建 GitHub Release

## 目录规范

### 后端目录

```
backend/app/
├── routers/          # API 路由，按功能分组
├── services/         # 业务逻辑层
├── models/           # Pydantic 模型
├── prompts/          # LLM 提示词模板
└── config.py         # 配置管理
```

### 前端目录

```
frontend/src/
├── views/            # 页面级组件
├── components/       # 可复用组件
├── api/              # API 客户端
├── stores/           # Pinia 状态管理
└── router.ts         # 路由配置
```

## API 设计规范

- RESTful 风格
- 前缀 `/api/`
- 使用 HTTP 状态码
- 响应格式统一

```python
# 成功响应
{"data": {...}, "message": "..."}

# 错误响应
{"error": "...", "detail": "..."}
```

## 数据库/文件规范

- Wiki 数据存储在 `data/` 目录
- 原始资料不可修改（immutable）
- 使用 Markdown 格式
- 图片等资产存 `data/assets/`

## 提示词管理

提示词模板存放在 `backend/app/prompts/`：

- `ingest.md` - 摄入提示词
- `paper_extract.md` - 论文提取提示词
- `query.md` - 查询提示词
- `lint.md` - 检查提示词

使用 `{placeholder}` 作为变量占位符。

## 配置管理

- 用户配置：`config.yaml`
- 默认配置：`backend/app/config.py`
- 环境变量覆盖（前缀 `SELFLLMWIKI_`）

## 文档维护

- README.md - 项目介绍
- PROCESS.md - 开发流程（本文档）
- CHANGELOG.md - 版本历史
- data/SCHEMA.md - Wiki 规范

## 问题反馈

- 使用 GitHub Issues
- 标签分类：`bug`, `feature`, `question`
- 提供复现步骤和环境信息
