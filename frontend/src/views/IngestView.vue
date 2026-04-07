<script setup lang="ts">
import { ref } from 'vue'
import { ingestContent, ingestPaper, webFetch, connectProgress } from '../api/client'
import { useAppStore } from '../stores/app'

const store = useAppStore()

type TabMode = 'text' | 'url' | 'file'
const activeTab = ref<TabMode>('text')

// 文本模式
const textContent = ref('')
const sourceType = ref('note')
const textTitle = ref('')

// URL 模式
const urlInput = ref('')
const fetchedContent = ref('')
const urlTitle = ref('')

// 文件模式
const selectedFile = ref<File | null>(null)
const isDragging = ref(false)

// 通用状态
const submitting = ref(false)
const progress = ref('')
const result = ref('')
const error = ref('')

function resetState() {
  progress.value = ''
  result.value = ''
  error.value = ''
}

async function submitText() {
  if (!textContent.value.trim()) return
  resetState()
  submitting.value = true
  try {
    const ws = connectProgress((data) => {
      progress.value = typeof data === 'string' ? data : data.message || JSON.stringify(data)
    })
    const res = await ingestContent({
      content: textContent.value,
      source_type: sourceType.value,
      title: textTitle.value || undefined,
    })
    result.value = '摄入成功: ' + JSON.stringify(res.data)
    store.setLastAction('文本摄入完成')
    ws.close()
  } catch (e: any) {
    error.value = '摄入失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    submitting.value = false
  }
}

async function fetchUrl() {
  if (!urlInput.value.trim()) return
  resetState()
  submitting.value = true
  try {
    const res = await webFetch({ url: urlInput.value })
    fetchedContent.value = typeof res.data === 'string' ? res.data : res.data.content || JSON.stringify(res.data)
    result.value = '已获取网页内容'
  } catch (e: any) {
    error.value = '获取失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    submitting.value = false
  }
}

async function submitUrl() {
  if (!fetchedContent.value.trim() && !urlInput.value.trim()) return
  resetState()
  submitting.value = true
  try {
    await ingestContent({
      content: fetchedContent.value || '',
      source_type: 'web',
      url: urlInput.value,
      title: urlTitle.value || undefined,
    })
    result.value = 'URL 摄入成功'
    store.setLastAction('URL 摄入完成')
  } catch (e: any) {
    error.value = '摄入失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    submitting.value = false
  }
}

function handleDragOver(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}

function handleDragLeave() {
  isDragging.value = false
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    selectedFile.value = files[0]
  }
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0]
  }
}

async function submitFile() {
  if (!selectedFile.value) return
  resetState()
  submitting.value = true
  try {
    const ws = connectProgress((data) => {
      progress.value = typeof data === 'string' ? data : data.message || JSON.stringify(data)
    })
    const res = await ingestPaper(selectedFile.value)
    result.value = '文件摄入成功: ' + JSON.stringify(res.data)
    store.setLastAction('文件摄入完成')
    ws.close()
  } catch (e: any) {
    error.value = '摄入失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="ingest-view">
    <h2>内容摄入</h2>
    <p class="view-desc">将文本、网页或文件导入到知识库中。</p>

    <div class="tabs">
      <button
        :class="['tab', { active: activeTab === 'text' }]"
        @click="activeTab = 'text'"
      >
        文本
      </button>
      <button
        :class="['tab', { active: activeTab === 'url' }]"
        @click="activeTab = 'url'"
      >
        URL
      </button>
      <button
        :class="['tab', { active: activeTab === 'file' }]"
        @click="activeTab = 'file'"
      >
        文件上传
      </button>
    </div>

    <!-- 文本模式 -->
    <div v-if="activeTab === 'text'" class="tab-content">
      <div class="form-row">
        <label>标题</label>
        <input v-model="textTitle" placeholder="内容标题（可选）" class="form-input" />
      </div>
      <div class="form-row">
        <label>来源类型</label>
        <select v-model="sourceType" class="form-input">
          <option value="note">笔记</option>
          <option value="paper">论文</option>
          <option value="web">网页</option>
          <option value="book">书籍</option>
          <option value="other">其他</option>
        </select>
      </div>
      <div class="form-row">
        <label>内容</label>
        <textarea
          v-model="textContent"
          placeholder="粘贴文本内容..."
          class="form-textarea"
          rows="12"
        ></textarea>
      </div>
      <button
        class="btn btn-primary"
        :disabled="submitting || !textContent.trim()"
        @click="submitText"
      >
        {{ submitting ? '处理中...' : '摄入' }}
      </button>
    </div>

    <!-- URL 模式 -->
    <div v-if="activeTab === 'url'" class="tab-content">
      <div class="form-row">
        <label>网页 URL</label>
        <div class="input-group">
          <input v-model="urlInput" placeholder="https://..." class="form-input" />
          <button
            class="btn"
            :disabled="submitting || !urlInput.trim()"
            @click="fetchUrl"
          >
            抓取
          </button>
        </div>
      </div>
      <div class="form-row">
        <label>标题</label>
        <input v-model="urlTitle" placeholder="页面标题（可选）" class="form-input" />
      </div>
      <div v-if="fetchedContent" class="form-row">
        <label>获取的内容</label>
        <textarea
          v-model="fetchedContent"
          class="form-textarea"
          rows="10"
        ></textarea>
      </div>
      <button
        class="btn btn-primary"
        :disabled="submitting || (!urlInput.trim() && !fetchedContent.trim())"
        @click="submitUrl"
      >
        {{ submitting ? '处理中...' : '摄入' }}
      </button>
    </div>

    <!-- 文件模式 -->
    <div v-if="activeTab === 'file'" class="tab-content">
      <div
        :class="['drop-zone', { dragging: isDragging }]"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @drop="handleDrop"
      >
        <div v-if="!selectedFile">
          <p class="drop-text">将文件拖放到此处</p>
          <p class="drop-hint">或</p>
          <label class="file-label">
            选择文件
            <input type="file" accept=".pdf,.txt,.md" @change="handleFileSelect" hidden />
          </label>
          <p class="drop-formats">支持格式: PDF, TXT, Markdown</p>
        </div>
        <div v-else class="file-info">
          <span class="file-name">{{ selectedFile.name }}</span>
          <span class="file-size">{{ (selectedFile.size / 1024).toFixed(1) }} KB</span>
          <button class="btn-small" @click="selectedFile = null">移除</button>
        </div>
      </div>
      <button
        class="btn btn-primary"
        :disabled="submitting || !selectedFile"
        @click="submitFile"
      >
        {{ submitting ? '上传中...' : '上传并摄入' }}
      </button>
    </div>

    <!-- 进度 & 结果 -->
    <div v-if="progress" class="progress-bar">
      <div class="progress-text">{{ progress }}</div>
    </div>
    <div v-if="result" class="result-msg success">{{ result }}</div>
    <div v-if="error" class="result-msg error">{{ error }}</div>
  </div>
</template>

<style scoped>
.ingest-view {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px;
}

h2 {
  margin-bottom: 4px;
}

.view-desc {
  color: var(--color-text-light);
  margin-bottom: 24px;
  font-size: 14px;
}

.tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--color-border);
  margin-bottom: 24px;
}

.tab {
  padding: 10px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text-light);
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color 0.2s, border-color 0.2s;
}

.tab:hover {
  color: var(--color-text);
}

.tab.active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
  font-weight: 600;
}

.tab-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-row label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-light);
}

.form-input {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 14px;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.form-textarea {
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 14px;
  font-family: var(--font-mono);
  resize: vertical;
  line-height: 1.5;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.input-group {
  display: flex;
  gap: 8px;
}

.input-group .form-input {
  flex: 1;
}

.drop-zone {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius);
  padding: 48px 24px;
  text-align: center;
  transition: border-color 0.2s, background 0.2s;
}

.drop-zone.dragging {
  border-color: var(--color-accent);
  background: #eef4fd;
}

.drop-text {
  font-size: 16px;
  color: var(--color-text);
  margin-bottom: 8px;
}

.drop-hint {
  color: var(--color-text-light);
  font-size: 13px;
  margin-bottom: 12px;
}

.drop-formats {
  color: var(--color-text-light);
  font-size: 12px;
  margin-top: 12px;
}

.file-label {
  display: inline-block;
  padding: 8px 16px;
  background: var(--color-accent);
  color: white;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 14px;
}

.file-label:hover {
  background: #3a7bc8;
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.file-name {
  font-weight: 600;
}

.file-size {
  color: var(--color-text-light);
  font-size: 13px;
}

.btn {
  padding: 8px 18px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.btn:hover:not(:disabled) {
  background: var(--color-bg-secondary);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-accent);
  color: white;
  border-color: var(--color-accent);
  align-self: flex-start;
}

.btn-primary:hover:not(:disabled) {
  background: #3a7bc8;
}

.btn-small {
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 12px;
}

.progress-bar {
  margin-top: 16px;
  padding: 12px;
  background: #eef4fd;
  border-radius: var(--radius);
  font-size: 13px;
  color: var(--color-accent);
}

.result-msg {
  margin-top: 12px;
  padding: 12px;
  border-radius: var(--radius);
  font-size: 13px;
}

.result-msg.success {
  background: #dcfce7;
  color: #166534;
}

.result-msg.error {
  background: #fee2e2;
  color: #991b1b;
}
</style>
