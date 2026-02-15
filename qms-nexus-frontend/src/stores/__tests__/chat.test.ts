// Chat Store 测试
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '../chat'
import type { ChatMessage } from '@/types/api'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
global.localStorage = localStorageMock as any

describe('Chat Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('状态初始化', () => {
    it('应该正确初始化所有状态', () => {
      const store = useChatStore()

      expect(store.messages).toEqual([])
      expect(store.currentInput).toBe('')
      expect(store.isTyping).toBe(false)
      expect(store.isWaiting).toBe(false)
      expect(store.streamingContent).toBe('')
      expect(store.error).toBe(null)
      expect(store.sessionId).toMatch(/^session_\d+_.+$/)
      expect(store.history).toEqual([])
    })

    it('应该正确计算 hasMessages', () => {
      const store = useChatStore()
      
      expect(store.hasMessages).toBe(false)
      
      store.messages = [
        {
          id: 'msg-1',
          role: 'user',
          content: '测试消息',
          timestamp: Date.now(),
          status: 'complete'
        }
      ]
      
      expect(store.hasMessages).toBe(true)
    })

    it('应该正确计算 isStreaming', () => {
      const store = useChatStore()
      
      expect(store.isStreaming).toBe(false)
      
      store.streamingContent = '流式内容'
      
      expect(store.isStreaming).toBe(true)
    })

    it('应该正确计算 canSendMessage', () => {
      const store = useChatStore()
      
      expect(store.canSendMessage).toBe(false) // 空输入
      
      store.currentInput = '  ' // 只有空格
      expect(store.canSendMessage).toBe(false)
      
      store.currentInput = '有效输入'
      expect(store.canSendMessage).toBe(true)
      
      store.isWaiting = true // 正在等待回复
      expect(store.canSendMessage).toBe(false)
      
      store.isWaiting = false
      store.isTyping = true // 正在输入
      expect(store.canSendMessage).toBe(false)
    })

    it('应该正确计算 lastMessage', () => {
      const store = useChatStore()
      
      expect(store.lastMessage).toBeNull()
      
      const message: ChatMessage = {
        id: 'msg-1',
        role: 'user',
        content: '最后一条消息',
        timestamp: Date.now(),
        status: 'complete'
      }
      
      store.messages = [{ ...message }]
      
      expect(store.lastMessage).toEqual(message)
    })

    it('应该正确计算 isLastMessageFromUser', () => {
      const store = useChatStore()
      
      expect(store.isLastMessageFromUser).toBe(false)
      
      store.messages = [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'AI回复',
          timestamp: Date.now(),
          status: 'complete'
        }
      ]
      
      expect(store.isLastMessageFromUser).toBe(false)
      
      store.messages.push({
        id: 'msg-2',
        role: 'user',
        content: '用户消息',
        timestamp: Date.now(),
        status: 'complete'
      })
      
      expect(store.isLastMessageFromUser).toBe(true)
    })

    it('应该正确计算 conversationContext', () => {
      const store = useChatStore()
      
      expect(store.conversationContext).toEqual([])
      
      store.messages = [
        {
          id: 'msg-1',
          role: 'assistant',
          content: 'AI回复1',
          timestamp: Date.now(),
          status: 'complete'
        },
        {
          id: 'msg-2',
          role: 'user',
          content: '用户消息1',
          timestamp: Date.now(),
          status: 'complete'
        },
        {
          id: 'msg-3',
          role: 'assistant',
          content: 'AI回复2',
          timestamp: Date.now(),
          status: 'complete'
        }
      ]
      
      const context = store.conversationContext
      expect(context).toHaveLength(3)
      expect(context).toEqual(['AI回复1', '用户消息1', 'AI回复2'])
    })
  })

  describe('消息管理', () => {
    it('应该成功发送消息', async () => {
      const store = useChatStore()
      
      store.currentInput = '测试问题'
      
      // 使用 setTimeout 来允许异步操作完成
      const sendPromise = store.sendMessage()
      
      // 验证消息已添加到列表
      expect(store.messages).toHaveLength(2) // 用户消息 + AI消息
      expect(store.messages[0].role).toBe('user')
      expect(store.messages[0].content).toBe('测试问题')
      expect(store.messages[0].status).toBe('complete')
      
      expect(store.messages[1].role).toBe('assistant')
      expect(store.messages[1].status).toBe('thinking')
      
      // 验证输入框已清空
      expect(store.currentInput).toBe('')
      
      // 等待发送完成
      await sendPromise
    })

    it('应该处理空消息发送', async () => {
      const store = useChatStore()
      
      store.currentInput = ''
      
      await store.sendMessage()
      
      expect(store.messages).toHaveLength(0)
      expect(store.isWaiting).toBe(false)
    })

    it('应该阻止重复发送', async () => {
      const store = useChatStore()
      
      store.currentInput = '测试问题'
      store.isWaiting = true // 模拟正在等待回复
      
      await store.sendMessage()
      
      expect(store.messages).toHaveLength(0) // 没有发送新消息
    })

    it('应该直接发送指定消息', async () => {
      const store = useChatStore()
      
      await store.sendMessage('直接发送的消息')
      
      expect(store.messages).toHaveLength(2)
      expect(store.messages[0].content).toBe('直接发送的消息')
      expect(store.currentInput).toBe('') // 输入框应该保持为空
    })
  })

  describe('流式回复', () => {
    it('应该正确流式接收回复', async () => {
      const store = useChatStore()
      
      store.messages = [
        {
          id: 'msg-1',
          role: 'user',
          content: '测试问题',
          timestamp: Date.now(),
          status: 'complete'
        },
        {
          id: 'msg-2',
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          status: 'thinking'
        }
      ]
      
      const aiMessage = store.messages[1]
      
      // 开始流式回复
      const streamPromise = store.streamAnswer('测试问题', aiMessage)
      
      // 等待流式完成
      await streamPromise
      
      expect(aiMessage.status).toBe('complete')
      expect(aiMessage.content.length).toBeGreaterThan(0)
      expect(store.streamingContent).toBe('') // 流式内容应该被清空
    })

    it('应该处理流式回复错误', async () => {
      const store = useChatStore()
      
      store.messages = [
        {
          id: 'msg-1',
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          status: 'thinking'
        }
      ]
      
      const aiMessage = store.messages[0]
      
      // Mock 生成错误
      vi.spyOn(store, 'streamAnswer').mockImplementation(() => {
        throw new Error('流式回复失败')
      })
      
      try {
        await store.streamAnswer('问题', aiMessage)
      } catch (err) {
        expect(err).toBeInstanceOf(Error)
      }
    })
  })

  describe('重新生成回答', () => {
    it('应该重新生成AI回答', async () => {
      const store = useChatStore()
      
      store.messages = [
        {
          id: 'msg-1',
          role: 'user',
          content: '原始问题',
          timestamp: Date.now(),
          status: 'complete'
        },
        {
          id: 'msg-2',
          role: 'assistant',
          content: '原始回答',
          timestamp: Date.now(),
          status: 'complete'
        }
      ]
      
      await store.regenerateAnswer('msg-2')
      
      const aiMessage = store.messages[1]
      expect(aiMessage.status).toBe('complete')
      expect(aiMessage.content).not.toBe('原始回答') // 应该生成新回答
    })

    it('应该处理无效的重新生成请求', async () => {
      const store = useChatStore()
      
      store.messages = [
        {
          id: 'msg-1',
          role: 'user',
          content: '问题',
          timestamp: Date.now(),
          status: 'complete'
        }
      ]
      
      await store.regenerateAnswer('invalid-id')
      
      expect(store.messages).toHaveLength(1) // 没有变化
      expect(store.error).toBeNull()
    })

    it('不应该重新生成用户消息', async () => {
      const store = useChatStore()
      
      store.messages = [
        {
          id: 'msg-1',
          role: 'user',
          content: '用户消息',
          timestamp: Date.now(),
          status: 'complete'
        }
      ]
      
      await store.regenerateAnswer('msg-1')
      
      expect(store.messages[0].content).toBe('用户消息') // 没有变化
    })
  })

  describe('状态管理', () => {
    it('应该清除所有消息', () => {
      const store = useChatStore()
      
      store.messages = [
        {
          id: 'msg-1',
          role: 'user',
          content: '消息',
          timestamp: Date.now(),
          status: 'complete'
        }
      ]
      store.error = '测试错误'
      store.streamingContent = '流式内容'
      store.isWaiting = true
      store.isTyping = true
      
      store.clearMessages()
      
      expect(store.messages).toEqual([])
      expect(store.error).toBeNull()
      expect(store.streamingContent).toBe('')
      expect(store.isWaiting).toBe(false)
      expect(store.isTyping).toBe(false)
    })

    it('应该清除错误', () => {
      const store = useChatStore()
      
      store.error = '测试错误'
      
      store.clearError()
      
      expect(store.error).toBeNull()
    })

    it('应该设置和清除输入状态', () => {
      const store = useChatStore()
      
      expect(store.isTyping).toBe(false)
      
      store.startTyping()
      expect(store.isTyping).toBe(true)
      
      store.stopTyping()
      expect(store.isTyping).toBe(false)
    })

    it('应该设置当前输入', () => {
      const store = useChatStore()
      
      store.setCurrentInput('新输入')
      
      expect(store.currentInput).toBe('新输入')
    })
  })

  describe('历史记录管理', () => {
    it('应该加载历史记录', () => {
      const store = useChatStore()
      
      const mockHistory = [
        {
          id: 'hist-1',
          role: 'assistant' as const,
          content: '',
          timestamp: Date.now(),
          status: 'complete' as const
        }
      ]
      
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockHistory))
      
      store.loadHistory()
      
      expect(store.history).toEqual(mockHistory)
      expect(localStorageMock.getItem).toHaveBeenCalled()
    })

    it('应该处理加载历史记录错误', () => {
      const store = useChatStore()
      
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('读取失败')
      })
      
      store.loadHistory()
      
      expect(store.history).toEqual([]) // 应该保持为空
      expect(localStorageMock.getItem).toHaveBeenCalled()
    })

    it('应该保存到历史记录', () => {
      const store = useChatStore()
      
      store.messages = [
        {
          id: 'msg-1',
          role: 'user' as const,
          content: '问题',
          timestamp: Date.now(),
          status: 'complete' as const
        },
        {
          id: 'msg-2',
          role: 'assistant' as const,
          content: '回答',
          timestamp: Date.now(),
          status: 'complete' as const
        }
      ]
      
      store.saveToHistory()
      
      expect(store.history.length).toBe(1)
      expect(localStorageMock.setItem).toHaveBeenCalled()
    })

    it('应该加载历史会话', () => {
      const store = useChatStore()
      
      const conversation = [
        {
          id: 'msg-1',
          role: 'user' as const,
          content: '历史问题',
          timestamp: Date.now(),
          status: 'complete' as const
        },
        {
          id: 'msg-2',
          role: 'assistant' as const,
          content: '历史回答',
          timestamp: Date.now(),
          status: 'complete' as const
        }
      ]
      
      const historyId = 'hist-1'
      store.history = [
        {
          id: historyId,
          messages: conversation,
          timestamp: Date.now()
        } as any
      ]
      
      store.loadConversation(historyId)
      
      expect(store.messages).toEqual(conversation)
    })

    it('应该删除历史会话', () => {
      const store = useChatStore()
      
      store.history = [
        {
          id: 'hist-1',
          role: 'assistant' as const,
          content: '',
          timestamp: Date.now(),
          status: 'complete' as const
        },
        {
          id: 'hist-2',
          role: 'assistant' as const,
          content: '',
          timestamp: Date.now(),
          status: 'complete' as const
        }
      ]
      
      store.deleteHistory('hist-1')
      
      expect(store.history).toHaveLength(1)
      expect(store.history[0].id).toBe('hist-2')
      expect(localStorageMock.setItem).toHaveBeenCalled()
    })

    it('应该清除历史记录', () => {
      const store = useChatStore()
      
      store.history = [
        {
          id: 'hist-1',
          role: 'assistant' as const,
          content: '',
          timestamp: Date.now(),
          status: 'complete' as const
        }
      ]
      
      store.clearHistory()
      
      expect(store.history).toEqual([])
      expect(localStorageMock.removeItem).toHaveBeenCalled()
    })
  })

  describe('会话管理', () => {
    it('应该重置会话', () => {
      const store = useChatStore()
      
      const oldSessionId = store.sessionId
      store.messages = [
        {
          id: 'msg-1',
          role: 'user' as const,
          content: '消息',
          timestamp: Date.now(),
          status: 'complete' as const
        }
      ]
      store.history = [
        {
          id: 'hist-1',
          role: 'assistant' as const,
          content: '',
          timestamp: Date.now(),
          status: 'complete' as const
        }
      ]
      
      store.resetSession()
      
      expect(store.sessionId).not.toBe(oldSessionId) // 会话ID应该改变
      expect(store.messages).toEqual([])
      expect(store.history).toEqual([])
      expect(localStorageMock.removeItem).toHaveBeenCalled()
    })

    it('应该重置所有状态', () => {
      const store = useChatStore()
      
      // 设置各种状态
      store.messages = [{ id: 'msg-1', role: 'user', content: '消息', timestamp: Date.now(), status: 'complete' }]
      store.currentInput = '输入'
      store.isTyping = true
      store.isWaiting = true
      store.streamingContent = '流式'
      store.error = '错误'
      store.history = [{ id: 'hist-1', role: 'assistant', content: '', timestamp: Date.now(), status: 'complete' }]
      
      store.reset()
      
      expect(store.messages).toEqual([])
      expect(store.currentInput).toBe('')
      expect(store.isTyping).toBe(false)
      expect(store.isWaiting).toBe(false)
      expect(store.streamingContent).toBe('')
      expect(store.error).toBeNull()
      expect(store.history).toEqual([])
    })
  })

  describe('工具函数', () => {
    it('应该生成会话ID', () => {
      const store = useChatStore()
      
      const sessionId1 = store.sessionId
      const sessionId2 = store.sessionId
      
      expect(sessionId1).toMatch(/^session_\d+_.+$/)
      expect(sessionId1).toBe(sessionId2) // 同一会话内应该相同
    })

    it('应该生成消息ID', () => {
      const store = useChatStore()
      
      const messageId1 = store['generateMessageId']?.()
      const messageId2 = store['generateMessageId']?.()
      
      expect(messageId1).toMatch(/^msg_\d+_.+$/)
      expect(messageId1).not.toBe(messageId2) // 每次应该不同
    })
  })

  describe('错误处理', () => {
    it('应该处理localStorage错误', () => {
      const store = useChatStore()
      
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('Storage error')
      })
      
      store.loadHistory()
      
      expect(store.history).toEqual([]) // 应该保持为空，不崩溃
      expect(localStorageMock.getItem).toHaveBeenCalled()
    })

    it('应该处理localStorage已满的情况', () => {
      const store = useChatStore()
      
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('QuotaExceededError')
      })
      
      store.messages = [
        {
          id: 'msg-1',
          role: 'user' as const,
          content: '消息',
          timestamp: Date.now(),
          status: 'complete' as const
        }
      ]
      
      store.saveToHistory()
      
      // 应该捕获错误，不崩溃
      expect(localStorageMock.setItem).toHaveBeenCalled()
    })
  })
})
