import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// ---- Wiki ----

export interface WikiPageSummary {
  slug: string
  title: string
  summary: string
  category: string
}

export interface WikiPage {
  slug: string
  title: string
  content: string
  backlinks: string[]
  outlinks: string[]
  category: string
  updated_at: string
}

export interface GraphData {
  nodes: { id: string; label: string; category: string; size: number }[]
  edges: { source: string; target: string }[]
}

export function fetchPages() {
  return api.get<WikiPageSummary[]>('/wiki/pages')
}

export function fetchPage(slug: string) {
  return api.get<WikiPage>(`/wiki/pages/${encodeURIComponent(slug)}`)
}

export function createPage(data: { slug: string; title: string; content: string; category: string }) {
  return api.post('/wiki/pages', data)
}

export function updatePage(slug: string, data: { content: string; title?: string }) {
  return api.put(`/wiki/pages/${encodeURIComponent(slug)}`, data)
}

export function deletePage(slug: string) {
  return api.delete(`/wiki/pages/${encodeURIComponent(slug)}`)
}

export function fetchGraph() {
  return api.get<GraphData>('/wiki/graph')
}

export function fetchIndex() {
  return api.get<string>('/wiki/index')
}

// ---- Raw ----

export interface RawFile {
  path: string
  name: string
  type: string
  size: number
  modified: string
}

export function fetchRawFiles() {
  return api.get<RawFile[]>('/raw/')
}

export function fetchRawFile(path: string) {
  return api.get<string>(`/raw/${path}`)
}

// ---- Ingest ----

export function ingestContent(data: { content: string; source_type: string; url?: string; title?: string }) {
  return api.post('/ingest', data)
}

export function ingestPaper(file: File) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/ingest/paper', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ---- Query ----

export interface QueryResponse {
  answer: string
  sources?: string[]
}

export function queryLLM(data: { question: string; provider?: string }) {
  return api.post<QueryResponse>('/query', data)
}

// ---- Deposit ----

export function deposit(data: { content: string; title: string; slug?: string }) {
  return api.post('/deposit', data)
}

// ---- Lint ----

export interface LintIssue {
  category: string
  severity: string
  description: string
  pages: string[]
  suggestion: string
}

export function runLint() {
  return api.post('/lint')
}

export function fetchLintReport() {
  return api.get<LintIssue[]>('/lint/report')
}

// ---- Papers ----

export interface Paper {
  paper_id: string
  title: string
  authors: string[]
  year: number | null
  venue: string
  citation_count: number
  abstract: string
  open_access_url: string
  doi: string
  in_wiki: boolean
}

export interface PaperSearchResponse {
  papers: Paper[]
  total: number
}

export function searchPapers(data: { query: string; limit?: number }) {
  return api.post<PaperSearchResponse>('/papers/search', data)
}

export function expandPapers(data: { paper_id?: string; topic?: string; limit?: number }) {
  return api.post<PaperSearchResponse>('/papers/expand', data)
}

export function downloadPapers(data: { papers: Paper[] }) {
  return api.post('/papers/download', data)
}

// ---- Log ----

export interface LogEntry {
  timestamp: string
  action: string
  detail: string
  pages: string[]
}

export function fetchLog() {
  return api.get<LogEntry[]>('/log')
}

// ---- Web ----

export function webSearch(data: { query: string; max_results?: number }) {
  return api.post('/web/search', data)
}

export function webFetch(data: { url: string }) {
  return api.post('/web/fetch', data)
}

// ---- WebSocket ----

export function connectProgress(onMessage: (data: any) => void): WebSocket {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${proto}://${location.host}/ws/progress`)
  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data))
    } catch {
      onMessage(e.data)
    }
  }
  return ws
}

export default api
