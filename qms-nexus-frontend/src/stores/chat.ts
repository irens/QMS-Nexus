// 问答状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, AskResponse } from '@/types/api'

import { APP_CONFIG } from '@/constants'

export interface ChatState {
  messages: ChatMessage[]
  currentInput: string
  isTyping: boolean
  isWaiting: boolean
  streamingContent: string
  error: string | null
  sessionId: string
  history: ChatMessage[]
}

export const useChatStore = defineStore('chat', () => {
  // 状态
  const messages = ref<ChatMessage[]>([])
  const currentInput = ref('')
  const isTyping = ref(false)
  const isWaiting = ref(false)
  const streamingContent = ref('')
  const error = ref<string | null>(null)
  const sessionId = ref(generateSessionId())
  const history = ref<ChatMessage[]>([])
  
  // 计算属性
  const hasMessages = computed(() => messages.value.length > 0)
  const isStreaming = computed(() => streamingContent.value.length > 0)
  const canSendMessage = computed(() => 
    currentInput.value.trim().length > 0 && !isWaiting.value && !isTyping.value
  )
  
  const lastMessage = computed(() => messages.value[messages.value.length - 1] || null)
  const isLastMessageFromUser = computed(() => 
    lastMessage.value?.role === 'user'
  )
  
  const conversationContext = computed(() => {
    // 获取最近的对话上下文（最多5条消息）
    const recentMessages = messages.value.slice(-10)
    return recentMessages.map(msg => msg.content)
  })
  
  // 方法
  /**
   * 发送消息
   */
  async function sendMessage(question?: string): Promise<void> {
    const message = question || currentInput.value.trim()
    
    if (!message || isWaiting.value) {
      return
    }
    
    try {
      error.value = null
      isWaiting.value = true
      
      // 创建用户消息
      const userMessage: ChatMessage = {
        id: generateMessageId(),
        role: 'user',
        content: message,
        timestamp: Date.now(),
        status: 'sending'
      }
      
      // 添加到消息列表
      messages.value.push(userMessage)
      
      // 清空输入框
      if (!question) {
        currentInput.value = ''
      }
      
      // 创建AI回复消息
      const assistantMessage: ChatMessage = {
        id: generateMessageId(),
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        status: 'thinking'
      }
      
      messages.value.push(assistantMessage)
      
      // 更新用户消息状态
      userMessage.status = 'complete'
      
      // 开始流式回复
      await streamAnswer(message, assistantMessage)
      
      // 保存到历史记录
      saveToHistory()
      
    } catch (err) {
      error.value = err instanceof Error ? err.message : '发送消息失败'
      console.error('Failed to send message:', err)
      
      // 更新最后一条消息状态为错误
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg && lastMsg.role === 'assistant') {
        lastMsg.status = 'error'
        lastMsg.error = error.value
      }
    } finally {
      isWaiting.value = false
      isTyping.value = false
      streamingContent.value = ''
    }
  }
  
  /**
   * 流式获取回答
   */
  async function streamAnswer(question: string, message: ChatMessage): Promise<void> {
    try {
      // 模拟流式响应
      // 实际项目中这里应该调用真实的流式API
      const mockResponse = generateMockAnswer(question)
      
      message.status = 'streaming'
      
      // 模拟打字机效果
      for (let i = 0; i <= mockResponse.answer.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 50))
        message.content = mockResponse.answer.slice(0, i)
        streamingContent.value = message.content
      }
      
      // 添加来源信息
      message.sources = mockResponse.sources
      message.status = 'complete'
      
    } catch (err) {
      message.status = 'error'
      message.error = err instanceof Error ? err.message : '获取回答失败'
      throw err
    }
  }
  
  /**
   * 重新生成回答
   */
  async function regenerateAnswer(messageId: string): Promise<void> {
    const messageIndex = messages.value.findIndex(msg => msg.id === messageId)
    if (messageIndex === -1) return
    
    const message = messages.value[messageIndex]
    if (message.role !== 'assistant') return
    
    // 找到对应的问题
    const userMessage = messages.value[messageIndex - 1]
    if (!userMessage || userMessage.role !== 'user') return
    
    try {
      error.value = null
      isWaiting.value = true
      
      // 重置AI消息
      message.content = ''
      message.sources = undefined
      message.status = 'thinking'
      message.error = undefined
      
      // 重新获取回答
      await streamAnswer(userMessage.content, message)
      
      // 保存到历史记录
      saveToHistory()
      
    } catch (err) {
      error.value = err instanceof Error ? err.message : '重新生成回答失败'
      console.error('Failed to regenerate answer:', err)
    } finally {
      isWaiting.value = false
      isTyping.value = false
      streamingContent.value = ''
    }
  }
  
  /**
   * 清除消息
   */
  function clearMessages(): void {
    messages.value = []
    error.value = null
    streamingContent.value = ''
    isWaiting.value = false
    isTyping.value = false
  }
  
  /**
   * 清除错误
   */
  function clearError(): void {
    error.value = null
  }
  
  /**
   * 开始输入
   */
  function startTyping(): void {
    isTyping.value = true
  }
  
  /**
   * 停止输入
   */
  function stopTyping(): void {
    isTyping.value = false
  }
  
  /**
   * 设置当前输入
   */
  function setCurrentInput(input: string): void {
    currentInput.value = input
  }
  
  /**
   * 获取历史记录
   */
  function loadHistory(): void {
    try {
      const savedHistory = localStorage.getItem(`${APP_CONFIG.STORAGE_KEYS.CHAT_HISTORY}_${sessionId.value}`)
      if (savedHistory) {
        history.value = JSON.parse(savedHistory)
      }
    } catch (err) {
      console.error('Failed to load chat history:', err)
    }
  }
  
  /**
   * 保存到历史记录
   */
  function saveToHistory(): void {
    try {
      if (messages.value.length > 0) {
        const historyItem = {
          id: generateMessageId(),
          messages: [...messages.value],
          timestamp: Date.now()
        }
        
        history.value.push({
          id: historyItem.id,
          role: 'assistant',
          content: '',
          timestamp: historyItem.timestamp,
          status: 'complete'
        })
        
        // 限制历史记录数量（最多保存50条）
        if (history.value.length > 50) {
          history.value = history.value.slice(-50)
        }
        
        localStorage.setItem(`${APP_CONFIG.STORAGE_KEYS.CHAT_HISTORY}_${sessionId.value}`, JSON.stringify(history.value))
      }
    } catch (err) {
      console.error('Failed to save chat history:', err)
    }
  }
  
  /**
   * 加载历史会话
   */
  function loadConversation(historyId: string): void {
    const item = history.value.find(h => h.id === historyId)
    if (item && 'messages' in item) {
      messages.value = [...(item as any).messages]
    }
  }
  
  /**
   * 删除历史会话
   */
  function deleteHistory(historyId: string): void {
    const index = history.value.findIndex(h => h.id === historyId)
    if (index !== -1) {
      history.value.splice(index, 1)
      
      try {
        localStorage.setItem(`${APP_CONFIG.STORAGE_KEYS.CHAT_HISTORY}_${sessionId.value}`, JSON.stringify(history.value))
      } catch (err) {
        console.error('Failed to save chat history:', err)
      }
    }
  }
  
  /**
   * 清除历史记录
   */
  function clearHistory(): void {
    history.value = []
    
    try {
      localStorage.removeItem(`${APP_CONFIG.STORAGE_KEYS.CHAT_HISTORY}_${sessionId.value}`)
    } catch (err) {
      console.error('Failed to clear chat history:', err)
    }
  }
  
  /**
   * 重置会话
   */
  function resetSession(): void {
    sessionId.value = generateSessionId()
    clearMessages()
    clearHistory()
  }
  
  /**
   * 重置所有状态
   */
  function reset(): void {
    messages.value = []
    currentInput.value = ''
    isTyping.value = false
    isWaiting.value = false
    streamingContent.value = ''
    error.value = null
    sessionId.value = generateSessionId()
    history.value = []
  }
  
  // 工具函数
  /**
   * 生成会话ID
   */
  function generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }
  
  /**
   * 生成消息ID
   */
  function generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }
  
  /**
   * 生成模拟回答（开发用）
   */
  function generateMockAnswer(_question: string): AskResponse {
    const answers = [
      '根据您的文档内容，这是一个关于质量管理体系的问题。',
      '根据相关法规要求，医疗器械质量管理需要遵循ISO 13485标准。',
      '您的问题涉及产品质量控制，建议参考相关的技术文档。',
      '根据文档中的描述，这个流程需要严格按照SOP执行。',
      '这是一个常见的质量问题，建议采取预防措施。'
    ]
    
    const sources = [
      { documentName: '医疗器械质量管理规范.pdf', page: 12, score: 0.95 },
      { documentName: 'ISO 13485实施指南.docx', page: 45, score: 0.87 },
      { documentName: '质量控制流程.xlsx', table: 'Sheet1', score: 0.82 }
    ]
    
    return {
      answer: answers[Math.floor(Math.random() * answers.length)],
      sources,
      totalTokens: Math.floor(Math.random() * 500) + 100,
      responseTime: Math.floor(Math.random() * 2000) + 500
    }
  }
  
  // 初始化时加载历史记录
  loadHistory()
  
  return {
    // 状态
    messages,
    currentInput,
    isTyping,
    isWaiting,
    streamingContent,
    error,
    sessionId,
    history,
    
    // 计算属性
    hasMessages,
    isStreaming,
    canSendMessage,
    lastMessage,
    isLastMessageFromUser,
    conversationContext,
    
    // 方法
    sendMessage,
    regenerateAnswer,
    clearMessages,
    clearError,
    startTyping,
    stopTyping,
    setCurrentInput,
    loadHistory,
    loadConversation,
    deleteHistory,
    clearHistory,
    resetSession,
    reset
  }
})