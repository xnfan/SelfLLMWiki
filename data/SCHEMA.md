# Wiki 规范

## 用途
这是一个由 LLM 编译和维护的个人知识 Wiki。
人类策划来源并审核；LLM 撰写和更新页面。

## 目录结构
- `raw/` — 不可变的原始资料，按类型组织
  - `raw/papers/` — 论文
  - `raw/articles/` — 文章
  - `raw/web/` — 网页
  - `raw/notes/` — 笔记
- `wiki/` — 编译后的知识页面
  - `wiki/index.md` — 主索引，每页一条
  - `wiki/log.md` — 只追加的操作日志
  - `wiki/overview.md` — 高层次总览
  - `wiki/pages/` — 所有 Wiki 页面，扁平 slug 命名的 .md 文件
- `assets/` — 二进制文件（PDF、图片）

## 页面规范
- 文件名：小写，连字符分隔的 slug（如 `attention-mechanism.md`）
- 每个页面以 `# 标题` 作为 H1 开头
- 使用 `[[wikilinks]]` 进行内部链接（slug 格式）
- 使用标准 Markdown 格式
- 数学公式用 LaTeX：行内 `$..$`，行间 `$$..$$`
- 引用来源：`[来源: raw/type/filename.md]`

## 操作
- **摄入(Ingest)**：读取来源 → 提取知识 → 更新 Wiki
- **查询(Query)**：使用 Wiki 内容回答问题
- **存入(Deposit)**：将查询结果保存为新的 Wiki 页面
- **检查(Lint)**：健康检查——查找矛盾、孤立页面、空白

## 论文页面模板
每篇论文包含结构化部分：
1. 元数据（作者、年份、发表场所、DOI）
2. 背景与问题
3. 核心洞察
4. 方法论与数学框架
5. 实现细节
6. 实验结果
7. 局限与未来方向
8. 知识关联（相关概念、基于、被扩展）
