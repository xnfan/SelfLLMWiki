<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchLog, type LogEntry } from '../api/client'

const router = useRouter()

const logs = ref<LogEntry[]>([])
const loading = ref(true)
const filterAction = ref('')
const error = ref('')

const actionTypes = computed(() => {
  const types = new Set(logs.value.map(l => l.action))
  return Array.from(types).sort()
})

const filteredLogs = computed(() => {
  if (!filterAction.value) return logs.value
  return logs.value.filter(l => l.action === filterAction.value)
})

async function loadLogs() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchLog()
    logs.value = Array.isArray(res.data) ? res.data : []
  } catch (e: any) {
    error.value = '加载日志失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

function navigateToPage(slug: string) {
  router.push(`/wiki/${encodeURIComponent(slug)}`)
}

function formatTime(ts: string) {
  try {
    return new Date(ts).toLocaleString('zh-CN')
  } catch {
    return ts
  }
}

function refreshLogs() {
  loadLogs()
}

onMounted(() => {
  loadLogs()
})
</script>

<template>
  <div class="log-view">
    <div class="log-header">
      <div>
        <h2>操作日志</h2>
        <p class="view-desc">查看知识库的操作历史。</p>
      </div>
      <div class="header-actions">
        <select v-model="filterAction" class="filter-select">
          <option value="">全部操作</option>
          <option v-for="t in actionTypes" :key="t" :value="t">{{ t }}</option>
        </select>
        <button class="btn" @click="refreshLogs">刷新</button>
      </div>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="filteredLogs.length === 0" class="empty-state">
      <p>暂无日志记录。</p>
    </div>

    <table v-else class="log-table">
      <thead>
        <tr>
          <th class="col-time">时间</th>
          <th class="col-action">操作类型</th>
          <th class="col-detail">详情</th>
          <th class="col-pages">影响页面</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(log, idx) in filteredLogs" :key="idx">
          <td class="col-time">
            <span class="time-text">{{ formatTime(log.timestamp) }}</span>
          </td>
          <td class="col-action">
            <span class="action-tag">{{ log.action }}</span>
          </td>
          <td class="col-detail">{{ log.detail }}</td>
          <td class="col-pages">
            <span
              v-for="page in log.pages"
              :key="page"
              class="page-link"
              @click="navigateToPage(page)"
            >
              {{ page }}
            </span>
            <span v-if="!log.pages?.length" class="no-pages">-</span>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="filteredLogs.length > 0" class="log-footer">
      共 {{ filteredLogs.length }} 条记录
    </div>
  </div>
</template>

<style scoped>
.log-view {
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px 24px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.log-header h2 {
  margin-bottom: 4px;
}

.view-desc {
  color: var(--color-text-light);
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.filter-select {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 13px;
  background: white;
}

.btn {
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: white;
  cursor: pointer;
  font-size: 13px;
}

.btn:hover {
  background: var(--color-bg-secondary);
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

.log-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.log-table th {
  text-align: left;
  padding: 10px 12px;
  background: var(--color-bg-secondary);
  border-bottom: 2px solid var(--color-border);
  font-weight: 600;
  font-size: 13px;
  color: var(--color-text-light);
}

.log-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
  vertical-align: top;
}

.log-table tr:hover td {
  background: var(--color-bg-secondary);
}

.col-time {
  width: 160px;
}

.col-action {
  width: 120px;
}

.col-pages {
  width: 180px;
}

.time-text {
  font-size: 13px;
  color: var(--color-text-light);
  font-family: var(--font-mono);
}

.action-tag {
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 3px;
  background: var(--color-bg-secondary);
  color: var(--color-text);
  font-weight: 500;
}

.page-link {
  display: inline-block;
  color: var(--color-accent);
  cursor: pointer;
  padding: 1px 6px;
  background: #eef4fd;
  border-radius: 3px;
  font-size: 12px;
  margin: 2px 4px 2px 0;
}

.page-link:hover {
  text-decoration: underline;
}

.no-pages {
  color: var(--color-text-light);
}

.log-footer {
  margin-top: 16px;
  text-align: right;
  font-size: 13px;
  color: var(--color-text-light);
}
</style>
