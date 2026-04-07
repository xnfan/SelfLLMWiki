<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { queryLLM, deposit } from '../api/client'
import { useAppStore, type ChatMessage } from '../stores/app'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const store = useAppStore()

const input = ref('')
const loading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function sendQuery() {
  const question = input.value.trim()
  if (!question || loading.value) return

  store.addChatMessage({
    role: 'user',
    content: question,
    timestamp: Date.now(),
  })
  input.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const res = await queryLLM({ question })
    const answer = res.data.answer || JSON.stringify(res.data)
    store.addChatMessage({
      role: 'assistant',
      content: answer,
      timestamp: Date.now(),
    })
    store.setLastAction('查询完成')
  } catch (e: any) {
    store.addChatMessage({
      role: 'assistant',
      content: '查询失败: ' + (e.response?.data?.detail || e.message),
      timestamp: Date.now(),
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

async function depositToWiki(msg: ChatMessage) {
  const title = prompt('请输入 Wiki 页面标题:')
  if (!title) return

  try {
    await deposit({
      content: msg.content,
      title: title,
    })
    store.setLastAction(`已存入 Wiki: ${title}`)
    alert('已成功存入 Wiki')
  } catch (e: any) {
    alert('存入失败: ' + (e.response?.data?.detail || e.message))
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendQuery()
  }
}

function formatTime(ts: number) {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="query-view">
    <div class="chat-header">
      <h2>智能查询</h2>
      <button class="btn-clear" @click="store.clearChat" v-if="store.chatHistory.length">
        清空对话
      </button>
    </div>

    <div class="messages-area" ref="messagesContainer">
      <div v-if="store.chatHistory.length === 0" class="empty-chat">
        <p>向知识库提出问题，AI 将基于 Wiki 内容回答。</p>
      </div>

      <div
        v-for="(msg, idx) in store.chatHistory"
        :key="idx"
        :class="['message', msg.role]"
      >
        <div class="message-header">
          <span class="message-role">{{ msg.role === 'user' ? '你' : 'AI' }}</span>
          <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
        </div>
        <div class="message-content">
          <MarkdownRenderer v-if="msg.role === 'assistant'" :content="msg.content" />
          <p v-else>{{ msg.content }}</p>
        </div>
        <div v-if="msg.role === 'assistant'" class="message-actions">
          <button class="btn-deposit" @click="depositToWiki(msg)">
            存入 Wiki
          </button>
        </div>
      </div>

      <div v-if="loading" class="message assistant loading-msg">
        <div class="message-header">
          <span class="message-role">AI</span>
        </div>
        <div class="message-content">
          <span class="typing-indicator">思考中...</span>
        </div>
      </div>
    </div>

    <div class="input-area">
      <textarea
        v-model="input"
        placeholder="输入问题... (Enter 发送, Shift+Enter 换行)"
        class="chat-input"
        rows="2"
        @keydown="handleKeydown"
      ></textarea>
      <button
        class="btn-send"
        :disabled="loading || !input.trim()"
        @click="sendQuery"
      >
        发送
      </button>
    </div>
  </div>
</template>

<style scoped>
.query-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 80px);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.chat-header h2 {
  margin: 0;
}

.btn-clear {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: white;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text-light);
}

.btn-clear:hover {
  background: var(--color-bg-secondary);
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-chat {
  text-align: center;
  padding-top: 120px;
  color: var(--color-text-light);
  font-size: 15px;
}

.message {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
}

.message.user {
  align-self: flex-end;
  background: var(--color-accent);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant {
  align-self: flex-start;
  background: var(--color-bg-secondary);
  border-bottom-left-radius: 4px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 11px;
  opacity: 0.7;
}

.message.user .message-header {
  color: rgba(255, 255, 255, 0.8);
}

.message-role {
  font-weight: 600;
}

.message-content {
  font-size: 14px;
  line-height: 1.6;
}

.message-content p {
  margin: 0;
  white-space: pre-wrap;
}

.message-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.btn-deposit {
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 12px;
  color: var(--color-accent);
}

.btn-deposit:hover {
  background: #eef4fd;
}

.typing-indicator {
  color: var(--color-text-light);
  font-style: italic;
}

.loading-msg {
  opacity: 0.7;
}

.input-area {
  display: flex;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-border);
  background: white;
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 14px;
  resize: none;
  font-family: inherit;
  line-height: 1.5;
}

.chat-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.btn-send {
  padding: 10px 24px;
  background: var(--color-accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  align-self: flex-end;
}

.btn-send:hover:not(:disabled) {
  background: #3a7bc8;
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
