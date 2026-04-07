# SelfLLMWiki 代码审查报告

## 项目概述
SelfLLMWiki 是一个自托管的 LLM Wiki 知识库系统，基于 Python FastAPI 后端和 Vue 3 前端。支持论文 PDF 处理、知识图谱可视化、Web 搜索等功能。

---

## 一、架构设计缺陷

### 1.1 全局状态管理问题

**文件**: `backend/app/config.py`

**问题**: 使用全局变量 `_config` 实现单例模式，存在以下问题：

```python
# 全局配置实例（延迟初始化）
_config: AppConfig | None = None

def get_config() -> AppConfig:
    """获取全局配置（单例）"""
    global _config
    if _config is None:
        _config = load_config()
    return _config
```

**缺陷**:
- 全局状态难以测试，无法并行运行多个配置实例
- 没有线程/协程安全保证
- 配置热重载时可能产生竞态条件

**建议**: 使用依赖注入框架（如 `dependency-injector`）或 FastAPI 的依赖系统管理配置生命周期。

---

### 1.2 服务层缺乏抽象接口

**文件**: `backend/app/services/wiki_manager.py`, `backend/app/services/query_service.py` 等

**问题**: 服务类直接实例化依赖，违反依赖倒置原则：

```python
class QueryService:
    def __init__(self) -> None:
        self.wiki = WikiManager()  # 直接依赖具体实现
```

**缺陷**:
- 单元测试困难，无法 Mock 依赖
- 服务间耦合度高
- 无法灵活替换实现（如将文件存储改为数据库存储）

**建议**: 定义抽象接口，通过构造函数注入依赖。

---

### 1.3 错误处理策略不一致

**文件**: 多个路由文件

**问题**: 错误处理方式不统一：

```python
# ingest.py - 吞掉所有异常
@router.post("", summary="摄入文本或 URL")
async def ingest_text(body: IngestRequest) -> IngestResponse:
    ...
    except Exception as e:
        return IngestResponse(success=False, message=f"摄入失败: {e}")

# wiki.py - 使用 HTTPException
@router.get("/pages/{slug}", summary="获取页面")
async def get_page(slug: str) -> WikiPage:
    ...
    if page is None:
        raise HTTPException(status_code=404, detail=f"页面 '{slug}' 不存在")
```

**缺陷**:
- 前端无法统一处理错误响应
- 部分错误信息可能暴露内部实现细节
- 日志记录不完整

**建议**: 统一使用 FastAPI 的异常处理器，定义标准错误响应模型。

---

## 二、性能与扩展性问题

### 2.1 文件系统 I/O 阻塞

**文件**: `backend/app/services/wiki_manager.py:69-80`

**问题**: `list_pages()` 方法在每次调用时遍历所有文件并读取内容：

```python
def list_pages(self) -> list[WikiPageSummary]:
    pages: list[WikiPageSummary] = []
    for f in sorted(self.pages_path.glob("*.md")):
        content = f.read_text(encoding="utf-8")  # 同步文件 I/O
        ...
```

**缺陷**:
- 页面数量增加时性能线性下降
- 同步 I/O 阻塞事件循环
- 没有缓存机制

**建议**:
- 使用 `aiofiles` 进行异步文件操作
- 实现内存缓存或引入 SQLite 索引
- 考虑使用数据库（SQLite/PostgreSQL）替代文件系统

---

### 2.2 查询服务缺乏向量化检索

**文件**: `backend/app/services/query_service.py:20-38`

**问题**: 使用简单的关键词匹配进行页面检索：

```python
def _score_page(keywords: list[str], title: str, summary: str) -> int:
    score = 0
    text = (title + " " + summary).lower()
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in text:
            score += 1
            if kw_lower in title.lower():
                score += 2
    return score
```

**缺陷**:
- 无法处理语义相似性（如 "深度学习" 和 "神经网络"）
- 关键词匹配过于简单，召回率低
- 没有 BM25 或向量检索支持

**建议**: 集成 `sentence-transformers` 或 `faiss` 实现语义搜索。

---

### 2.3 图谱构建重复计算

**文件**: `backend/app/services/graph_builder.py:15-61`

**问题**: `build()` 方法每次调用都重新读取所有页面：

```python
def build(self) -> GraphData:
    pages = self.wiki.list_pages()  # 读取所有文件
    all_links = self.wiki.get_all_links()  # 再次读取所有文件
```

**缺陷**:
- `list_pages()` 和 `get_all_links()` 各自独立读取文件，重复 I/O
- 没有增量更新机制
- 大图时性能差

**建议**: 实现增量更新或添加缓存层。

---

## 三、安全与可靠性问题

### 3.1 路径遍历漏洞

**文件**: `backend/app/services/wiki_manager.py:32-36`

**问题**: slug 未经验证直接用于文件路径：

```python
def read_page(self, slug: str) -> WikiPage | None:
    path = self.pages_path / f"{slug}.md"  # 可能包含 ../
    if not path.exists():
        return None
```

**缺陷**: 恶意 slug 如 `../../../etc/passwd` 可能导致路径遍历攻击。

**建议**: 添加 slug 验证：

```python
import re

def validate_slug(slug: str) -> bool:
    return bool(re.match(r'^[\w\u4e00-\u9fff-]+$', slug))
```

---

### 3.2 没有请求限流

**文件**: `backend/app/routers/*.py`

**问题**: 所有 API 端点都没有速率限制，容易受到滥用：
- `/api/ingest` - 可能被用于 DoS 攻击
- `/api/query` - LLM 调用成本高，需要限制
- `/api/papers/search` - 外部 API 调用需要限制

**建议**: 集成 `slowapi` 或使用 FastAPI 中间件实现限流。

---

### 3.3 临时文件未安全清理

**文件**: `backend/app/services/paper_pipeline.py:134-154`

**问题**: 虽然尝试清理临时文件，但存在竞态条件：

```python
with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
    tmp.write(data)
    tmp_path = Path(tmp.name)

try:
    ...
finally:
    try:
        tmp_path.unlink()
    except OSError:
        pass
```

**缺陷**: 如果进程崩溃，`delete=False` 的临时文件可能残留。

**建议**: 使用 `tempfile.TemporaryDirectory` 作为上下文管理器。

---

### 3.4 日志注入风险

**文件**: `backend/app/services/wiki_manager.py:153-159`

**问题**: 用户输入直接写入日志文件：

```python
def append_log(self, operation: str, details: str, affected_pages: list[str] | None = None) -> None:
    pages_str = ", ".join(affected_pages) if affected_pages else "-"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"| {timestamp} | {operation} | {details} | {pages_str} |\n"
    with open(self.log_path, "a", encoding="utf-8") as f:
        f.write(entry)
```

**缺陷**: 如果 `details` 包含换行符或 Markdown 表格分隔符，可能破坏日志格式。

**建议**: 对输入进行转义或 sanitization。

---

## 四、代码质量问题

### 4.1 重复代码

**文件**: 多个文件

**问题**: JSON 提取逻辑重复：

```python
# ingest_service.py:45-56
def _extract_json(text: str) -> dict:
    m = _JSON_RE.search(text)
    if m:
        return json.loads(m.group(1))
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start : end + 1])
    return {}

# lint_service.py:22-36
def _extract_json_array(text: str) -> list[dict]:
    m = _JSON_ARRAY_RE.search(text)
    if m:
        return json.loads(m.group(1))
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return []
```

**建议**: 提取到通用工具模块。

---

### 4.2 魔法字符串

**文件**: `backend/app/services/wiki_manager.py:132`, `backend/app/services/graph_builder.py:41`

**问题**: 类别名称硬编码：

```python
cat_names = {"paper": "论文", "concept": "概念", "entity": "实体", "source": "来源摘要"}
...
node_map[target_slug] = GraphNode(
    id=target_slug,
    label=target_slug,
    category="missing",  # 魔法字符串
    size=0,
)
```

**建议**: 使用枚举类定义常量。

---

### 4.3 类型注解不完整

**文件**: `backend/app/services/paper_search.py:167-205`

**问题**: 使用 `Any` 类型过多，丢失类型安全：

```python
def _ss_paper_to_info(paper: Any) -> PaperInfo:
    if not isinstance(paper, dict):
        paper = paper.__dict__ if hasattr(paper, "__dict__") else {}
```

**建议**: 定义具体的 TypedDict 或 dataclass。

---

### 4.4 前端类型定义重复

**文件**: `frontend/src/api/client.ts`, `frontend/src/stores/app.ts`

**问题**: 接口定义与后端 Pydantic 模型不同步，需要手动维护两份定义。

**建议**: 使用 `openapi-typescript` 从 FastAPI 自动生成前端类型。

---

## 五、功能缺陷

### 5.1 反向链接更新不及时

**文件**: `backend/app/services/wiki_manager.py:93-102`

**问题**: `get_backlinks()` 每次实时扫描所有文件：

```python
def get_backlinks(self, slug: str) -> list[str]:
    backlinks: list[str] = []
    for f in self.pages_path.glob("*.md"):
        content = f.read_text(encoding="utf-8")
        if slug in self.extract_links(content):
            backlinks.append(f.stem)
    return backlinks
```

**缺陷**: 性能差，且 `read_page()` 返回的 backlinks 可能过时。

**建议**: 维护反向链接索引或数据库。

---

### 5.2 WebSocket 没有认证

**文件**: `backend/app/main.py:77-99`

**问题**: `/ws/progress` 端点完全开放：

```python
@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    await websocket.accept()
    ws_connections.add(websocket)
```

**缺陷**: 任何人都可以连接并接收进度通知，可能造成信息泄露。

**建议**: 添加 Token 认证或基于 Cookie 的会话验证。

---

### 5.3 论文下载缺少并发控制

**文件**: `backend/app/routers/papers.py:66-101`

**问题**: 批量下载论文是顺序执行的：

```python
for paper in body.papers:
    ...
    if paper.open_access_url:
        success = await download_paper_pdf(paper.open_access_url, save_path)
```

**缺陷**: 下载大量论文时耗时过长。

**建议**: 使用 `asyncio.gather` 或 `asyncio.Semaphore` 限制并发。

---

### 5.4 没有事务支持

**文件**: `backend/app/services/ingest_service.py:78-171`

**问题**: 摄入过程涉及多个步骤，但没有事务回滚机制：

```python
async def ingest_text(...) -> IngestResponse:
    # 1. 保存原始资料
    self.wiki.save_raw(...)
    # 2. 调用 LLM
    llm_response = await llm.complete(...)
    # 3. 写入页面
    self.wiki.write_page(...)
    # 4. 更新索引
    self.wiki.update_index()
```

**缺陷**: 如果第 4 步失败，前面步骤已经执行，数据不一致。

**建议**: 实现补偿事务或两阶段提交。

---

## 六、前端问题

### 6.1 没有错误边界

**文件**: `frontend/src/views/*.vue`

**问题**: Vue 组件没有错误边界处理，API 失败时用户体验差。

**建议**: 添加全局错误处理和组件级错误边界。

---

### 6.2 内存泄漏风险

**文件**: `frontend/src/views/GraphView.vue:22-203`

**问题**: D3 模拟器在组件卸载时停止，但事件监听器可能未完全清理：

```typescript
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (simulation) simulation.stop()
})
```

**缺陷**: D3 的 zoom 和 drag 行为可能残留事件监听器。

**建议**: 显式清理所有 D3 事件监听器。

---

### 6.3 缺乏加载状态管理

**文件**: `frontend/src/api/client.ts`

**问题**: API 客户端没有统一的加载状态、错误重试逻辑。

**建议**: 添加请求拦截器和响应拦截器，实现统一的 loading 和错误提示。

---

## 七、配置与部署问题

### 7.1 依赖版本未锁定

**文件**: `backend/requirements.txt` (未检查到)

**问题**: 如果存在 requirements.txt，可能缺少版本锁定。

**建议**: 使用 `pip-compile` 或 `poetry` 锁定依赖版本。

---

### 7.2 没有健康检查端点

**文件**: `backend/app/main.py`

**问题**: 缺少 `/health` 或 `/ready` 端点，不利于容器化部署。

**建议**: 添加健康检查端点，检查关键依赖（LLM 连接、文件系统权限等）。

---

### 7.3 日志配置不完整

**文件**: `backend/app/main.py`

**问题**: 使用默认日志配置，没有结构化日志输出。

**建议**: 配置 JSON 格式日志，便于日志收集系统处理。

---

## 八、改进建议优先级

### 高优先级（安全与稳定性）
1. 修复路径遍历漏洞
2. 添加请求限流
3. 实现 slug 验证
4. 添加 WebSocket 认证

### 中优先级（性能与可维护性）
5. 引入异步文件 I/O
6. 实现服务层抽象接口
7. 统一错误处理策略
8. 添加缓存层

### 低优先级（功能增强）
9. 实现语义搜索
10. 使用数据库存储
11. 自动生成前端类型
12. 添加健康检查端点

---

## 总结

SelfLLMWiki 是一个功能完整的知识库系统，但在以下方面需要改进：

1. **安全性**: 路径遍历、请求限流、认证缺失
2. **性能**: 同步 I/O、重复计算、缺乏缓存
3. **架构**: 紧耦合、缺乏抽象、全局状态
4. **可靠性**: 无事务支持、错误处理不一致

建议优先处理安全问题，然后逐步重构架构以提高可维护性。
