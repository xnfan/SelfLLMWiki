import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

export const useAppStore = defineStore('app', () => {
  const pageCount = ref(0)
  const lastAction = ref('')
  const chatHistory = ref<ChatMessage[]>([])

  function setPageCount(n: number) {
    pageCount.value = n
  }

  function setLastAction(action: string) {
    lastAction.value = action
  }

  function addChatMessage(msg: ChatMessage) {
    chatHistory.value.push(msg)
  }

  function clearChat() {
    chatHistory.value = []
  }

  return { pageCount, lastAction, chatHistory, setPageCount, setLastAction, addChatMessage, clearChat }
})
