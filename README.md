# SelfLLMWiki

自托管 LLM Wiki 知识库系统 —— 基于 Karpathy 的 LLM Wiki 概念，将原始资料编译为持久、互链接的 Markdown 知识库。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Vue](https://img.shields.io/badge/vue-3.5+-green.svg)

## 核心特性

- **Karpathy 四层架构**：原始资料 → LLM 编译 → Wiki 页面 → 知识图谱
- **四大操作**：摄入(Ingest)、查询(Query)、存入(Deposit)、检查(Lint)
- **多源论文搜索**：Semantic Scholar + arXiv 自动切换
- **学术论文结构化提取**：背景、洞察、方法论、实现、实验、未来方向
- **知识图谱可视化**：D3.js 力导向图展示知识关联
- **灵活 LLM 接入**：支持 OpenAI、Claude、Ollama、OpenRouter 等
- **中英文支持**：Marker + Surya OCR 支持双语论文处理

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+, FastAPI, Pydantic |
| 前端 | Vue 3, Vite, TypeScript, D3.js |
| LLM | OpenAI API / Anthropic Claude / Ollama |
| PDF | Marker (Surya OCR), PyMuPDF4LLM |
| 搜索 | DuckDuckGo, Semantic Scholar, arXiv |

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/SelfLLMWiki.git
cd SelfLLMWiki
```

### 2. 配置环境

```bash
# 复制配置模板
cp config.yaml.example config.yaml

# 编辑 config.yaml，配置你的 LLM 提供商
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5176 即可使用。

## 配置说明

编辑 `config.yaml`：

```yaml
llm:
  providers:
    - name: "local-ollama"
      format: "openai"
      base_url: "http://localhost:11434/v1"
      api_key: "ollama"
      model: "qwen3:14b"
    - name: "openrouter"
      format: "openai"
      base_url: "https://openrouter.ai/api/v1"
      api_key: "sk-or-xxx"
      model: "google/gemini-2.5-pro"
  default: "local-ollama"

data:
  root: "./data"

pdf:
  converter: "marker"
  use_gpu: true
```

## 使用指南

### 摄入论文

1. 进入「论文发现」页面
2. 输入关键词搜索（自动从 Semantic Scholar 和 arXiv 获取）
3. 选择论文，点击「下载并摄入」
4. LLM 自动提取结构化知识并写入 Wiki

### 查询知识

1. 进入「查询」页面
2. 输入问题，LLM 基于 Wiki 内容回答
3. 点击「存入」将回答保存为 Wiki 页面

### 查看知识图谱

进入「图谱」页面，可视化浏览知识关联：
- 节点大小 = 连接数
- 颜色区分：概念(蓝)、论文(绿)、实体(橙)
- 点击节点跳转详情

## 项目结构

```
SelfLLMWiki/
├── backend/               # FastAPI 后端
│   ├── app/
│   │   ├── routers/       # API 路由
│   │   ├── services/      # 业务逻辑
│   │   ├── prompts/       # LLM 提示词模板
│   │   └── models/        # 数据模型
│   └── requirements.txt
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 公共组件
│   │   └── api/           # API 客户端
│   └── package.json
├── data/                  # Wiki 数据目录
│   ├── SCHEMA.md          # Wiki 规范
│   ├── raw/               # 原始资料
│   ├── wiki/              # 编译后的知识
│   └── assets/            # 附件
└── config.yaml            # 用户配置
```

## 开发流程

详见 [PROCESS.md](./PROCESS.md)

## 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/xxx`
3. 提交更改：`git commit -am 'Add xxx'`
4. 推送分支：`git push origin feature/xxx`
5. 提交 Pull Request

## 许可证

MIT License

## 致谢

- [Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) - LLM Wiki 概念
- [Marker](https://github.com/VikParuchuri/marker) - PDF 转 Markdown
- [Semantic Scholar](https://www.semanticscholar.org/) - 学术搜索 API
- [arXiv](https://arxiv.org/) - 开放获取论文
