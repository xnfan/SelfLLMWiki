<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { runLint, fetchLintReport, type LintIssue } from '../api/client'
import { useAppStore } from '../stores/app'

const router = useRouter()
const store = useAppStore()

const issues = ref<LintIssue[]>([])
const loading = ref(false)
const running = ref(false)
const error = ref('')

const severityOrder: Record<string, number> = {
  error: 0,
  warning: 1,
  info: 2,
}

const severityLabels: Record<string, string> = {
  error: '错误',
  warning: '警告',
  info: '信息',
}

async function handleRunLint() {
  running.value = true
  error.value = ''
  try {
    await runLint()
    store.setLastAction('检查完成')
    await loadReport()
  } catch (e: any) {
    error.value = '检查运行失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    running.value = false
  }
}

async function loadReport() {
  loading.value = true
  try {
    const res = await fetchLintReport()
    const data = Array.isArray(res.data) ? res.data : []
    issues.value = data.sort((a, b) =>
      (severityOrder[a.severity] ?? 9) - (severityOrder[b.severity] ?? 9)
    )
  } catch (e: any) {
    // 可能还没有报告
    issues.value = []
  } finally {
    loading.value = false
  }
}

function navigateToPage(slug: string) {
  router.push(`/wiki/${encodeURIComponent(slug)}`)
}

// 初始加载报告
loadReport()
</script>

<template>
  <div class="lint-view">
    <div class="lint-header">
      <div>
        <h2>知识库检查</h2>
        <p class="view-desc">检查 Wiki 中的质量问题、缺失链接和不一致。</p>
      </div>
      <button
        class="btn btn-primary"
        :disabled="running"
        @click="handleRunLint"
      >
        {{ running ? '检查中...' : '运行检查' }}
      </button>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="issues.length === 0 && !loading" class="empty-state">
      <p>暂无检查结果。点击"运行检查"开始。</p>
    </div>

    <div v-else class="issues-list">
      <div class="issues-summary">
        共发现 {{ issues.length }} 个问题:
        <span class="count-error">
          {{ issues.filter(i => i.severity === 'error').length }} 个错误
        </span>
        <span class="count-warning">
          {{ issues.filter(i => i.severity === 'warning').length }} 个警告
        </span>
        <span class="count-info">
          {{ issues.filter(i => i.severity === 'info').length }} 个信息
        </span>
      </div>

      <div
        v-for="(issue, idx) in issues"
        :key="idx"
        :class="['issue-card', `severity-${issue.severity}`]"
      >
        <div class="issue-header">
          <span :class="['severity-tag', issue.severity]">
            {{ severityLabels[issue.severity] || issue.severity }}
          </span>
          <span class="category-tag">{{ issue.category }}</span>
        </div>
        <p class="issue-desc">{{ issue.description }}</p>
        <div v-if="issue.pages?.length" class="issue-pages">
          <span class="pages-label">受影响页面:</span>
          <span
            v-for="page in issue.pages"
            :key="page"
            class="page-link"
            @click="navigateToPage(page)"
          >
            {{ page }}
          </span>
        </div>
        <div v-if="issue.suggestion" class="issue-suggestion">
          <strong>建议:</strong> {{ issue.suggestion }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lint-view {
  max-width: 860px;
  margin: 0 auto;
  padding: 32px 24px;
}

.lint-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.lint-header h2 {
  margin-bottom: 4px;
}

.view-desc {
  color: var(--color-text-light);
  font-size: 14px;
}

.btn {
  padding: 8px 18px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary {
  background: var(--color-accent);
  color: white;
  border-color: var(--color-accent);
}

.btn-primary:hover:not(:disabled) {
  background: #3a7bc8;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-msg {
  background: #fee2e2;
  color: #991b1b;
  padding: 12px;
  border-radius: var(--radius);
  margin-bottom: 16px;
  font-size: 14px;
}

.loading {
  text-align: center;
  padding: 60px 0;
  color: var(--color-text-light);
}

.empty-state {
  text-align: center;
  padding: 80px 0;
  color: var(--color-text-light);
}

.issues-summary {
  padding: 12px 16px;
  background: var(--color-bg-secondary);
  border-radius: var(--radius);
  margin-bottom: 16px;
  font-size: 14px;
  display: flex;
  gap: 16px;
  align-items: center;
}

.count-error { color: var(--color-danger); font-weight: 600; }
.count-warning { color: var(--color-warning); font-weight: 600; }
.count-info { color: var(--color-info); font-weight: 600; }

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.issue-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 16px;
  border-left: 4px solid var(--color-border);
}

.issue-card.severity-error {
  border-left-color: var(--color-danger);
}

.issue-card.severity-warning {
  border-left-color: var(--color-warning);
}

.issue-card.severity-info {
  border-left-color: var(--color-info);
}

.issue-header {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.severity-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 3px;
  font-weight: 600;
  text-transform: uppercase;
}

.severity-tag.error {
  background: #fee2e2;
  color: #991b1b;
}

.severity-tag.warning {
  background: #fef3c7;
  color: #92400e;
}

.severity-tag.info {
  background: #dbeafe;
  color: #1e40af;
}

.category-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 3px;
  background: var(--color-bg-secondary);
  color: var(--color-text-light);
}

.issue-desc {
  margin-bottom: 8px;
  font-size: 14px;
  line-height: 1.5;
}

.issue-pages {
  margin-bottom: 8px;
  font-size: 13px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.pages-label {
  color: var(--color-text-light);
}

.page-link {
  color: var(--color-accent);
  cursor: pointer;
  padding: 2px 6px;
  background: #eef4fd;
  border-radius: 3px;
  font-size: 12px;
}

.page-link:hover {
  text-decoration: underline;
}

.issue-suggestion {
  font-size: 13px;
  color: var(--color-text-light);
  padding: 8px 12px;
  background: var(--color-bg-secondary);
  border-radius: 4px;
  line-height: 1.5;
}
</style>
