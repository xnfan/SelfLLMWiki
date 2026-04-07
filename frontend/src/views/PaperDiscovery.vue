<script setup lang="ts">
import { ref } from 'vue'
import { searchPapers, expandPapers, downloadPapers, type Paper } from '../api/client'
import { useAppStore } from '../stores/app'

const store = useAppStore()

type ViewMode = 'search' | 'expand'
const mode = ref<ViewMode>('search')

const searchQuery = ref('')
const expandInput = ref('')
const expandTopic = ref('')
const results = ref<Paper[]>([])
const selected = ref<Set<string>>(new Set())
const loading = ref(false)
const downloading = ref(false)
const error = ref('')
const message = ref('')

async function handleSearch() {
  if (!searchQuery.value.trim()) return
  loading.value = true
  error.value = ''
  message.value = ''
  results.value = []
  selected.value = new Set()
  try {
    const res = await searchPapers({ query: searchQuery.value, limit: 20 })
    results.value = res.data.papers || []
    if (results.value.length === 0) {
      error.value = '未找到相关论文，请尝试其他关键词'
    }
    store.setLastAction(`搜索论文: ${searchQuery.value}`)
  } catch (e: any) {
    error.value = '搜索失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function handleExpand() {
  loading.value = true
  error.value = ''
  message.value = ''
  results.value = []
  selected.value = new Set()
  try {
    const res = await expandPapers({
      paper_id: expandInput.value.trim() || undefined,
      topic: expandTopic.value.trim() || undefined,
      limit: 20,
    })
    results.value = res.data.papers || []
    if (results.value.length === 0) {
      error.value = '未找到相关论文'
    }
    store.setLastAction('论文拓展完成')
  } catch (e: any) {
    error.value = '拓展失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

function toggleSelect(id: string) {
  const s = new Set(selected.value)
  if (s.has(id)) {
    s.delete(id)
  } else {
    s.add(id)
  }
  selected.value = s
}

function selectAll() {
  if (selected.value.size === results.value.length) {
    selected.value = new Set()
  } else {
    selected.value = new Set(results.value.map(p => p.paper_id))
  }
}

async function handleDownload() {
  if (selected.value.size === 0) return
  downloading.value = true
  error.value = ''
  message.value = ''
  try {
    const papersToDownload = results.value.filter(p => selected.value.has(p.paper_id))
    await downloadPapers({ papers: papersToDownload })
    message.value = `已成功下载并摄入 ${selected.value.size} 篇论文`
    store.setLastAction(`下载并摄入 ${selected.value.size} 篇论文`)
    selected.value = new Set()
  } catch (e: any) {
    error.value = '下载失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    downloading.value = false
  }
}
</script>

<template>
  <div class="papers-view">
    <div class="page-header">
      <h1>论文发现</h1>
      <p class="subtitle">搜索学术论文并导入到知识库</p>
    </div>

    <div class="card search-card">
      <div class="mode-tabs">
        <button
          :class="['tab', { active: mode === 'search' }]"
          @click="mode = 'search'"
        >
          <span class="tab-icon">🔍</span>
          关键词搜索
        </button>
        <button
          :class="['tab', { active: mode === 'expand' }]"
          @click="mode = 'expand'"
        >
          <span class="tab-icon">✨</span>
          智能拓展
        </button>
      </div>

      <!-- 搜索模式 -->
      <div v-if="mode === 'search'" class="search-section">
        <div class="search-box">
          <input
            v-model="searchQuery"
            placeholder="输入论文标题、作者或关键词..."
            class="search-input"
            @keydown.enter="handleSearch"
          />
          <button
            class="btn btn-primary search-btn"
            :disabled="loading || !searchQuery.trim()"
            @click="handleSearch"
          >
            <span v-if="loading" class="spinner"></span>
            <span v-else>搜索</span>
          </button>
        </div>
      </div>

      <!-- 拓展模式 -->
      <div v-else class="expand-section">
        <div class="form-group">
          <label>论文 ID</label>
          <input v-model="expandInput" placeholder="输入论文 ID（可选）" />
        </div>
        <div class="form-group">
          <label>研究主题</label>
          <input v-model="expandTopic" placeholder="输入研究主题（可选）" />
        </div>
        <button
          class="btn btn-primary"
          :disabled="loading"
          @click="handleExpand"
        >
          <span v-if="loading" class="spinner"></span>
          <span v-else>查找相关论文</span>
        </button>
      </div>
    </div>

    <!-- 消息提示 -->
    <div v-if="error" class="alert alert-error">
      <span class="alert-icon">⚠️</span>
      {{ error }}
    </div>
    <div v-if="message" class="alert alert-success">
      <span class="alert-icon">✓</span>
      {{ message }}
    </div>

    <!-- 结果列表 -->
    <div v-if="results.length > 0" class="results-container">
      <div class="results-header">
        <span class="results-count">共 {{ results.length }} 条结果</span>
        <div class="results-actions">
          <button class="btn btn-small" @click="selectAll">
            {{ selected.size === results.length ? '取消全选' : '全选' }}
          </button>
          <button
            class="btn btn-primary btn-small"
            :disabled="downloading || selected.size === 0"
            @click="handleDownload"
          >
            <span v-if="downloading" class="spinner"></span>
            <span v-else>下载并摄入 ({{ selected.size }})</span>
          </button>
        </div>
      </div>

      <div class="papers-list">
        <div
          v-for="paper in results"
          :key="paper.paper_id"
          :class="['paper-item', { selected: selected.has(paper.paper_id) }]"
          @click="toggleSelect(paper.paper_id)"
        >
          <div class="paper-checkbox">
            <input
              type="checkbox"
              :checked="selected.has(paper.paper_id)"
              @click.stop
              @change="toggleSelect(paper.paper_id)"
            />
          </div>
          <div class="paper-content">
            <div class="paper-header">
              <h3 class="paper-title">
                {{ paper.title }}
                <span v-if="paper.in_wiki" class="badge badge-success">已在 Wiki</span>
                <span v-if="paper.paper_id?.startsWith('arxiv:')" class="badge badge-info">arXiv</span>
                <span v-else-if="paper.paper_id" class="badge badge-info">Semantic Scholar</span>
              </h3>
            </div>
            <div class="paper-meta">
              <span v-if="paper.authors?.length" class="meta-item">
                {{ paper.authors.slice(0, 3).join(', ') }}
                <span v-if="paper.authors.length > 3">等 {{ paper.authors.length }} 位作者</span>
              </span>
              <span v-if="paper.year" class="meta-item">{{ paper.year }}</span>
              <span v-if="paper.venue" class="meta-item">{{ paper.venue }}</span>
              <span v-if="paper.citation_count" class="meta-item">
                被引 {{ paper.citation_count }} 次
              </span>
            </div>
            <p v-if="paper.abstract" class="paper-abstract">{{ paper.abstract }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && !error" class="empty-state">
      <div class="empty-icon">📚</div>
      <h3>开始探索学术世界</h3>
      <p>输入关键词搜索论文，或使用智能拓展发现相关研究</p>
    </div>
  </div>
</template>

<style scoped>
.papers-view {
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 4px;
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: 15px;
}

.search-card {
  margin-bottom: 20px;
}

.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text);
}

.tab.active {
  background: var(--color-accent-light);
  color: var(--color-primary);
  border-color: var(--color-primary-light);
}

.tab-icon {
  font-size: 16px;
}

.search-box {
  display: flex;
  gap: 12px;
}

.search-input {
  flex: 1;
  font-size: 15px;
  padding: 12px 16px;
}

.search-btn {
  padding: 12px 24px;
  min-width: 100px;
}

.expand-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.results-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px;
}

.results-count {
  font-size: 14px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.results-actions {
  display: flex;
  gap: 8px;
}

.papers-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.paper-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.2s;
}

.paper-item:hover {
  border-color: var(--color-primary-light);
  box-shadow: var(--shadow-md);
}

.paper-item.selected {
  border-color: var(--color-primary);
  background: var(--color-accent-light);
}

.paper-checkbox {
  padding-top: 2px;
  flex-shrink: 0;
}

.paper-checkbox input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.paper-content {
  flex: 1;
  min-width: 0;
}

.paper-header {
  margin-bottom: 8px;
}

.paper-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.4;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.paper-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-item:not(:last-child)::after {
  content: '·';
  margin-left: 8px;
  color: var(--color-text-tertiary);
}

.paper-abstract {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--color-text-secondary);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 15px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.alert-icon {
  font-size: 16px;
  flex-shrink: 0;
}
</style>
