<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchRawFiles, fetchRawFile, type RawFile } from '../api/client'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const files = ref<RawFile[]>([])
const selectedFile = ref<RawFile | null>(null)
const fileContent = ref('')
const loading = ref(true)
const loadingContent = ref(false)
const error = ref('')

async function loadFiles() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchRawFiles()
    files.value = Array.isArray(res.data) ? res.data : []
  } catch (e: any) {
    error.value = '加载文件列表失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function selectFile(file: RawFile) {
  selectedFile.value = file
  loadingContent.value = true
  fileContent.value = ''
  try {
    const res = await fetchRawFile(file.path)
    fileContent.value = typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2)
  } catch (e: any) {
    fileContent.value = '加载文件内容失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    loadingContent.value = false
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

function getFileIcon(type: string): string {
  switch (type.toLowerCase()) {
    case 'pdf': return '📄'
    case 'md':
    case 'markdown': return '📝'
    case 'txt': return '📃'
    case 'json': return '{ }'
    default: return '📎'
  }
}

function isMarkdown(file: RawFile): boolean {
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  return ['md', 'markdown', 'txt'].includes(ext)
}

onMounted(() => {
  loadFiles()
})
</script>

<template>
  <div class="raw-view">
    <div class="raw-sidebar">
      <div class="sidebar-header">
        <h3>原始资料</h3>
        <span class="file-count">{{ files.length }} 个文件</span>
      </div>

      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="error" class="error-text">{{ error }}</div>

      <ul v-else class="file-list">
        <li
          v-for="file in files"
          :key="file.path"
          :class="{ active: selectedFile?.path === file.path }"
          @click="selectFile(file)"
        >
          <span class="file-icon">{{ getFileIcon(file.type) }}</span>
          <div class="file-meta">
            <span class="file-name">{{ file.name }}</span>
            <span class="file-details">
              {{ formatSize(file.size) }} &middot; {{ formatDate(file.modified) }}
            </span>
          </div>
        </li>
      </ul>
    </div>

    <div class="raw-content">
      <div v-if="!selectedFile" class="empty-state">
        <p>从左侧选择一个文件查看内容。</p>
      </div>

      <div v-else>
        <div class="content-header">
          <h2>{{ selectedFile.name }}</h2>
          <div class="content-meta">
            <span>类型: {{ selectedFile.type }}</span>
            <span>大小: {{ formatSize(selectedFile.size) }}</span>
            <span>修改时间: {{ formatDate(selectedFile.modified) }}</span>
          </div>
        </div>

        <div v-if="loadingContent" class="loading">加载内容中...</div>

        <div v-else class="content-body">
          <MarkdownRenderer v-if="isMarkdown(selectedFile)" :content="fileContent" />
          <pre v-else class="raw-text">{{ fileContent }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.raw-view {
  display: flex;
  height: calc(100vh - 80px);
}

.raw-sidebar {
  width: 300px;
  border-right: 1px solid var(--color-border);
  overflow-y: auto;
  flex-shrink: 0;
  background: var(--color-bg-secondary);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--color-border);
}

.sidebar-header h3 {
  font-size: 14px;
  font-weight: 600;
}

.file-count {
  font-size: 12px;
  color: var(--color-text-light);
}

.file-list {
  list-style: none;
  padding: 8px;
}

.file-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  border-radius: var(--radius);
  margin-bottom: 2px;
}

.file-list li:hover {
  background: white;
}

.file-list li.active {
  background: white;
  box-shadow: var(--shadow);
}

.file-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.file-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-details {
  font-size: 11px;
  color: var(--color-text-light);
  margin-top: 2px;
}

.raw-content {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
  min-width: 0;
}

.content-header {
  margin-bottom: 20px;
}

.content-header h2 {
  margin-bottom: 8px;
}

.content-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--color-text-light);
}

.raw-text {
  background: var(--color-bg-secondary);
  padding: 16px;
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

.loading {
  padding: 40px;
  text-align: center;
  color: var(--color-text-light);
}

.empty-state {
  text-align: center;
  padding-top: 120px;
  color: var(--color-text-light);
}

.error-text {
  padding: 16px;
  color: var(--color-danger);
  font-size: 13px;
}
</style>
