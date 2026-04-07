<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchPages, fetchPage, updatePage, createPage, deletePage, type WikiPageSummary, type WikiPage } from '../api/client'
import { useAppStore } from '../stores/app'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const pages = ref<WikiPageSummary[]>([])
const currentPage = ref<WikiPage | null>(null)
const editing = ref(false)
const editContent = ref('')
const editTitle = ref('')
const loading = ref(false)
const searchQuery = ref('')
const showNewForm = ref(false)
const newSlug = ref('')
const newTitle = ref('')
const newCategory = ref('concept')

const filteredPages = ref<WikiPageSummary[]>([])

watch(searchQuery, (q) => {
  if (!q.trim()) {
    filteredPages.value = pages.value
  } else {
    const lower = q.toLowerCase()
    filteredPages.value = pages.value.filter(
      p => p.title.toLowerCase().includes(lower) || p.slug.toLowerCase().includes(lower)
    )
  }
})

async function loadPages() {
  try {
    const res = await fetchPages()
    pages.value = res.data
    filteredPages.value = res.data
    store.setPageCount(res.data.length)
  } catch (e) {
    console.error('加载页面列表失败', e)
  }
}

async function loadPage(slug: string) {
  loading.value = true
  try {
    const res = await fetchPage(slug)
    currentPage.value = res.data
    editing.value = false
  } catch (e) {
    console.error('加载页面失败', e)
    currentPage.value = null
  } finally {
    loading.value = false
  }
}

function startEdit() {
  if (!currentPage.value) return
  editContent.value = currentPage.value.content
  editTitle.value = currentPage.value.title
  editing.value = true
}

function cancelEdit() {
  editing.value = false
}

async function saveEdit() {
  if (!currentPage.value) return
  try {
    await updatePage(currentPage.value.slug, {
      content: editContent.value,
      title: editTitle.value,
    })
    store.setLastAction(`已更新页面: ${currentPage.value.slug}`)
    await loadPage(currentPage.value.slug)
  } catch (e) {
    console.error('保存失败', e)
    alert('保存失败')
  }
}

async function handleDelete() {
  if (!currentPage.value) return
  if (!confirm(`确定删除页面 "${currentPage.value.title}" 吗?`)) return
  try {
    await deletePage(currentPage.value.slug)
    store.setLastAction(`已删除页面: ${currentPage.value.slug}`)
    currentPage.value = null
    router.push('/')
    await loadPages()
  } catch (e) {
    console.error('删除失败', e)
  }
}

async function handleCreate() {
  if (!newSlug.value.trim() || !newTitle.value.trim()) return
  try {
    await createPage({
      slug: newSlug.value.trim(),
      title: newTitle.value.trim(),
      content: `# ${newTitle.value.trim()}\n\n`,
      category: newCategory.value,
    })
    store.setLastAction(`已创建页面: ${newSlug.value}`)
    showNewForm.value = false
    newSlug.value = ''
    newTitle.value = ''
    await loadPages()
    router.push(`/wiki/${encodeURIComponent(newSlug.value.trim())}`)
  } catch (e) {
    console.error('创建失败', e)
    alert('创建失败')
  }
}

function navigateTo(slug: string) {
  router.push(`/wiki/${encodeURIComponent(slug)}`)
}

watch(() => route.params.slug, (slug) => {
  if (slug && typeof slug === 'string') {
    loadPage(slug)
  } else {
    currentPage.value = null
    editing.value = false
  }
}, { immediate: true })

onMounted(() => {
  loadPages()
})
</script>

<template>
  <div class="wiki-layout">
    <!-- 左侧栏：页面列表 -->
    <aside class="wiki-sidebar">
      <div class="sidebar-header">
        <h3>页面列表</h3>
        <button class="btn-small btn-primary" @click="showNewForm = !showNewForm">
          {{ showNewForm ? '取消' : '+ 新建' }}
        </button>
      </div>

      <div v-if="showNewForm" class="new-page-form">
        <input v-model="newSlug" placeholder="页面 slug" class="input-sm" />
        <input v-model="newTitle" placeholder="页面标题" class="input-sm" />
        <select v-model="newCategory" class="input-sm">
          <option value="concept">概念</option>
          <option value="paper">论文</option>
          <option value="entity">实体</option>
          <option value="source">来源</option>
        </select>
        <button class="btn-small btn-primary" @click="handleCreate">创建</button>
      </div>

      <input
        v-model="searchQuery"
        placeholder="搜索页面..."
        class="search-input"
      />

      <ul class="page-list">
        <li
          v-for="p in filteredPages"
          :key="p.slug"
          :class="{ active: currentPage?.slug === p.slug }"
          @click="navigateTo(p.slug)"
        >
          <span class="page-title">{{ p.title }}</span>
          <span :class="['category-tag', `cat-${p.category}`]">{{ p.category }}</span>
        </li>
      </ul>

      <div v-if="filteredPages.length === 0" class="empty-hint">
        暂无页面
      </div>
    </aside>

    <!-- 中间区域：内容 -->
    <section class="wiki-content">
      <div v-if="loading" class="loading-state">加载中...</div>

      <div v-else-if="!currentPage && !loading" class="empty-state">
        <h2>欢迎使用 SelfLLMWiki</h2>
        <p>从左侧选择一个页面查看，或创建新页面。</p>
      </div>

      <div v-else-if="currentPage">
        <div class="content-header">
          <h1 v-if="!editing">{{ currentPage.title }}</h1>
          <input v-else v-model="editTitle" class="title-input" />
          <div class="content-actions">
            <button
              v-if="!editing"
              class="btn btn-primary"
              @click="startEdit"
            >
              编辑
            </button>
            <template v-else>
              <button class="btn btn-success" @click="saveEdit">保存</button>
              <button class="btn" @click="cancelEdit">取消</button>
            </template>
            <button class="btn btn-danger" @click="handleDelete">删除</button>
          </div>
        </div>

        <div class="content-meta">
          <span :class="['category-tag', `cat-${currentPage.category}`]">
            {{ currentPage.category }}
          </span>
          <span class="updated-at">
            更新于: {{ new Date(currentPage.updated_at).toLocaleString('zh-CN') }}
          </span>
        </div>

        <div v-if="!editing" class="content-body">
          <MarkdownRenderer :content="currentPage.content" />
        </div>
        <div v-else class="editor-area">
          <textarea
            v-model="editContent"
            class="edit-textarea"
            placeholder="输入 Markdown 内容..."
          ></textarea>
        </div>
      </div>
    </section>

    <!-- 右侧栏：反向链接 -->
    <aside class="wiki-backlinks">
      <template v-if="currentPage">
        <div class="backlinks-section">
          <h4>反向链接</h4>
          <ul v-if="currentPage.backlinks?.length">
            <li v-for="bl in currentPage.backlinks" :key="bl">
              <a href="#" @click.prevent="navigateTo(bl)">{{ bl }}</a>
            </li>
          </ul>
          <p v-else class="empty-hint">无反向链接</p>
        </div>
        <div class="backlinks-section">
          <h4>出链</h4>
          <ul v-if="currentPage.outlinks?.length">
            <li v-for="ol in currentPage.outlinks" :key="ol">
              <a href="#" @click.prevent="navigateTo(ol)">{{ ol }}</a>
            </li>
          </ul>
          <p v-else class="empty-hint">无出链</p>
        </div>
      </template>
    </aside>
  </div>
</template>

<style scoped>
.wiki-layout {
  display: flex;
  height: calc(100vh - 80px);
}

.wiki-sidebar {
  width: 260px;
  border-right: 1px solid var(--color-border);
  padding: 16px;
  overflow-y: auto;
  flex-shrink: 0;
  background: var(--color-bg-secondary);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.sidebar-header h3 {
  font-size: 14px;
  font-weight: 600;
}

.new-page-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
  padding: 10px;
  background: white;
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
}

.input-sm {
  padding: 6px 8px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 13px;
}

.search-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 13px;
  margin-bottom: 12px;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.page-list {
  list-style: none;
}

.page-list li {
  padding: 8px 10px;
  cursor: pointer;
  border-radius: var(--radius);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  margin-bottom: 2px;
}

.page-list li:hover {
  background: white;
}

.page-list li.active {
  background: white;
  box-shadow: var(--shadow);
}

.page-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.category-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
  flex-shrink: 0;
  margin-left: 6px;
}

.cat-concept { background: #dbeafe; color: #1e40af; }
.cat-paper { background: #dcfce7; color: #166534; }
.cat-entity { background: #ffedd5; color: #9a3412; }
.cat-source { background: #f3f4f6; color: #4b5563; }
.cat-missing { background: #fee2e2; color: #991b1b; }

.wiki-content {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
  min-width: 0;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.content-header h1 {
  font-size: 24px;
  margin: 0;
}

.title-input {
  font-size: 24px;
  font-weight: 700;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 4px 8px;
  flex: 1;
  margin-right: 12px;
}

.content-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.content-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

.updated-at {
  font-size: 12px;
  color: var(--color-text-light);
}

.edit-textarea {
  width: 100%;
  min-height: 500px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
}

.edit-textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.wiki-backlinks {
  width: 220px;
  border-left: 1px solid var(--color-border);
  padding: 16px;
  overflow-y: auto;
  flex-shrink: 0;
  background: var(--color-bg-secondary);
}

.backlinks-section {
  margin-bottom: 20px;
}

.backlinks-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-light);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.backlinks-section ul {
  list-style: none;
}

.backlinks-section li {
  padding: 4px 0;
  font-size: 13px;
}

.empty-state {
  text-align: center;
  padding-top: 120px;
  color: var(--color-text-light);
}

.empty-state h2 {
  margin-bottom: 8px;
}

.loading-state {
  text-align: center;
  padding-top: 120px;
  color: var(--color-text-light);
}

.empty-hint {
  font-size: 12px;
  color: var(--color-text-light);
  padding: 8px 0;
}

.btn {
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: white;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.btn:hover {
  background: var(--color-bg-secondary);
}

.btn-primary {
  background: var(--color-accent);
  color: white;
  border-color: var(--color-accent);
}

.btn-primary:hover {
  background: #3a7bc8;
}

.btn-success {
  background: var(--color-success);
  color: white;
  border-color: var(--color-success);
}

.btn-success:hover {
  background: #219a52;
}

.btn-danger {
  background: white;
  color: var(--color-danger);
  border-color: var(--color-danger);
}

.btn-danger:hover {
  background: var(--color-danger);
  color: white;
}

.btn-small {
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 12px;
}

.btn-small.btn-primary {
  background: var(--color-accent);
  color: white;
  border-color: var(--color-accent);
}
</style>
