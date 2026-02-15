/**
 * Chat组件单元测试
 * 测试智能问答功能的核心逻辑
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ElMessage } from 'element-plus'
import Chat from '../Chat.vue'
import { chatService } from '@/services/chat'
import ErrorBoundary from '@/components/ErrorBoundary.vue'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  }
}))

// Mock ErrorBoundary
vi.mock('@/components/ErrorBoundary.vue', () => ({
  default: {
    template: '<div class="mock-error-boundary"><slot /></div>'
  }
}))

// Mock chatService
vi.mock('@/services/chat', () => ({
  chatService: {
    askQuestion: vi.fn(),
    askQuestionStream: vi.fn()
  }
}))

// Mock Vue Router
const mockRouter = {
  push: vi.fn()
}

vi.mock('vue-router', () => ({
  useRouter: () => mockRouter
}))

describe('Chat.vue', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    // 创建新的 Pinia 实例
    setActivePinia(createPinia())
    
    // 清理所有 mocks
    vi.clearAllMocks()
    
    // 挂载组件
    wrapper = mount(Chat, {
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-icon': true,
          'el-button': true,
          'el-input': true,
          'el-checkbox': true,
          'el-avatar': true,
          'el-dropdown': true,
          'el-dropdown-menu': true,
          'el-dropdown-item': true,
          'el-result': true
        }
      }
    })
  })

  afterEach(() => {
    wrapper.unmount()
  })

  // ========================================
  // 1. 组件渲染测试
  // ========================================
  
  describe('组件渲染', () => {
    it('应该正确渲染聊天界面', () => {
      expect(wrapper.text()).toContain('智能问答')
      expect(wrapper.text()).toContain('基于医疗文档知识库的智能问答系统')
    })

    it('应该显示新建对话按钮', () => {
      const newChatButton = wrapper.findAll('button').find(btn => 
        btn.text().includes('新建对话')
      )
      expect(newChatButton).toBeTruthy()
    })

    it('应该显示历史对话列表', () => {
      const historyItems = wrapper.findAll('.p-3.hover\\:bg-gray-50')
      expect(historyItems.length).toBeGreaterThan(0)
    })

    it('应该显示消息输入区域', () => {
      const inputArea = wrapper.find('.p-4.border-t')
      expect(inputArea.exists()).toBe(true)
    })

    it('应该显示快速建议按钮', () => {
      const suggestions = wrapper.findAll('.space-y-2 .el-button')
      expect(suggestions.length).toBeGreaterThan(0)
    })
  })

  // ========================================
  // 2. 消息输入和发送测试
  // ========================================
  
  describe('消息输入功能', () => {
    beforeEach(() => {
      // 设置输入消息
      wrapper.vm.inputMessage = '测试问题'
    })

    it('应该正确输入消息', () => {
      expect(wrapper.vm.inputMessage).toBe('测试问题')
    })

    it('应该通过点击按钮发送消息', async () => {
      const mockResponse = {
        answer: '这是一个测试回答',
        sources: []
      }
      
      vi.mocked(chatService.askQuestion).mockResolvedValue(mockResponse)
      
      // 点击发送按钮
      const sendButton = wrapper.findAll('button').find(btn => 
        btn.attributes('type') === 'primary'
      )
      await sendButton?.trigger('click')
      
      await wrapper.vm.$nextTick()
      
      // 验证消息已发送
      expect(wrapper.vm.messages.length).toBeGreaterThan(0)
      expect(wrapper.vm.isThinking).toBe(false)
    })

    it('应该支持Enter键发送消息', async () => {
      const mockResponse = {
        answer: '这是一个测试回答',
        sources: []
      }
      
      vi.mocked(chatService.askQuestion).mockResolvedValue(mockResponse)
      
      // 模拟Enter键
      wrapper.vm.inputMessage = '测试问题'
      await wrapper.vm.sendMessage()
      
      await wrapper.vm.$nextTick()
      
      // 验证消息已发送
      expect(wrapper.vm.messages.length).toBeGreaterThan(0)
    })

    it('不应该发送空消息', async () => {
      wrapper.vm.inputMessage = ''
      await wrapper.vm.sendMessage()
      
      expect(wrapper.vm.messages.length).toBe(0)
    })

    it('不应该在思考状态下发送消息', async () => {
      wrapper.vm.isThinking = true
      wrapper.vm.inputMessage = '测试问题'
      
      await wrapper.vm.sendMessage()
      
      expect(wrapper.vm.messages.length).toBe(0)
    })

    it('发送后应该清空输入框', async () => {
      const mockResponse = {
        answer: '这是一个测试回答',
        sources: []
      }
      
      vi.mocked(chatService.askQuestion).mockResolvedValue(mockResponse)
      
      wrapper.vm.inputMessage = '测试问题'
      await wrapper.vm.sendMessage()
      
      expect(wrapper.vm.inputMessage).toBe('')
    })

    it('应该显示用户消息', async () => {
      const mockResponse = {
        answer: '这是一个测试回答',
        sources: []
      }
      
      vi.mocked(chatService.askQuestion).mockResolvedValue(mockResponse)
      
      wrapper.vm.inputMessage = '我的问题'
      await wrapper.vm.sendMessage()
      
      await wrapper.vm.$nextTick()
      
      const userMessages = wrapper.vm.messages.filter((m: any) => m.role === 'user')
      expect(userMessages.length).toBeGreaterThan(0)
      expect(userMessages[0].content).toBe('我的问题')
    })
  })

  // ========================================
  // 3. 流式响应测试
  // ========================================
  
  describe('流式响应功能', () => {
    beforeEach(() => {
      wrapper.vm.enableStreaming = true
    })

    it('应该启用流式响应', () => {
      expect(wrapper.vm.enableStreaming).toBe(true)
    })

    it('应该调用askQuestionStream进行流式响应', async () => {
      const mockChunkCallback = vi.fn()
      const mockResponse = {
        answer: '完整的回答内容',
        sources: []
      }
      
      vi.mocked(chatService.askQuestionStream).mockImplementation(
        async (question, context, filterTags, topK, onChunk) => {
          // 模拟流式响应
          const chunks = ['正在', '为您', '查询', '相关', '知识', '...']
          for (const chunk of chunks) {
            onChunk(chunk)
            await new Promise(resolve => setTimeout(resolve, 100))
          }
          return mockResponse
        }
      )
      
      wrapper.vm.inputMessage = '流式测试问题'
      await wrapper.vm.sendMessage()
      
      await new Promise(resolve => setTimeout(resolve, 800))
      
      // 验证流式响应被调用
      expect(chatService.askQuestionStream).toHaveBeenCalled()
      
      // 验证AI消息状态
      const aiMessages = wrapper.vm.messages.filter((m: any) => m.role === 'assistant')
      expect(aiMessages.length).toBeGreaterThan(0)
      expect(aiMessages[0].status).toBe('completed')
    })

    it('应该显示流式响应内容', async () => {
      const chunks: string[] = []
      
      vi.mocked(chatService.askQuestionStream).mockImplementation(
        async (question, context, filterTags, topK, onChunk) => {
          const testChunks = ['第一', '第二', '第三']
          for (const chunk of testChunks) {
            chunks.push(chunk)
            onChunk(chunk)
          }
          return {
            answer: chunks.join(''),
            sources: []
          }
        }
      )
      
      wrapper.vm.inputMessage = '流式显示测试'
      await wrapper.vm.sendMessage()
      
      await new Promise(resolve => setTimeout(resolve, 500))
      
      const aiMessages = wrapper.vm.messages.filter((m: any) => m.role === 'assistant')
      expect(aiMessages[0].content).toBe('第一第二第三')
    })

    it('应该显示思考状态', async () => {
      vi.mocked(chatService.askQuestionStream).mockImplementation(
        async () => {
          // 模拟延迟响应
          await new Promise(resolve => setTimeout(resolve, 500))
          return {
            answer: '思考完成',
            sources: []
          }
        }
      )
      
      wrapper.vm.inputMessage = '思考测试'
      await wrapper.vm.sendMessage()
      
      await wrapper.vm.$nextTick()
      
      // 验证思考状态
      const aiMessages = wrapper.vm.messages.filter((m: any) => m.role === 'assistant')
      expect(aiMessages[0].status).toBe('thinking')
    })

    it('应该正确显示来源标注', async () => {
      const mockResponse = {
        answer: '根据文档内容回答',
        sources: [
          {
            documentName: 'ISO13485.pdf',
            page: 15,
            table: '相关章节'
          },
          {
            documentName: '质量手册.docx',
            page: 3,
            table: '管理要求'
          }
        ]
      }
      
      vi.mocked(chatService.askQuestionStream).mockResolvedValue(mockResponse)
      
      wrapper.vm.enableSources = true
      wrapper.vm.inputMessage = '来源测试问题'
      await wrapper.vm.sendMessage()
      
      await new Promise(resolve => setTimeout(resolve, 500))
      
      const aiMessages = wrapper.vm.messages.filter((m: any) => m.role === 'assistant')
      expect(aiMessages[0].sources).toBeDefined()
      expect(aiMessages[0].sources.length).toBe(2)
      expect(aiMessages[0].sources[0].fileName).toBe('ISO13485.pdf')
      expect(aiMessages[0].sources[1].fileName).toBe('质量手册.docx')
    })

    it('应该可以禁用流式响应', async () => {
      wrapper.vm.enableStreaming = false
      
      const mockResponse = {
        answer: '非流式回答',
        sources: []
      }
      
      vi.mocked(chatService.askQuestion).mockResolvedValue(mockResponse)
      
      wrapper.vm.inputMessage = '非流式测试'
      await wrapper.vm.sendMessage()
      
      await wrapper.vm.$nextTick()
      
      // 验证调用的是askQuestion而非askQuestionStream
      expect(chatService.askQuestion).toHaveBeenCalled()
      expect(chatService.askQuestionStream).not.toHaveBeenCalled()
    })
  })

  // ========================================
  // 4. 错误处理测试
  // ========================================
  
  describe('错误处理', () => {
    it('应该处理网络错误', async () => {
      vi.mocked(chatService.askQuestion).mockRejectedValue(
        new Error('Network error')
      )
      
      wrapper.vm.inputMessage = '网络错误测试'
      await wrapper.vm.sendMessage()
      
      await wrapper.vm.$nextTick()
      
      // 验证错误消息
      const aiMessages = wrapper.vm.messages.filter((m: any) => m.role === 'assistant')
      expect(aiMessages[0].content).toContain('抱歉')
      expect(aiMessages[0].content).toContain('稍后重试')
      
      // 验证isThinking重置
      expect(wrapper.vm.isThinking).toBe(false)
    })

    it('应该处理超时错误', async () => {
      vi.mocked(chatService.askQuestion).mockRejectedValue({
        code: 'ETIMEDOUT',
        message: 'Request timeout'
      })
      
      wrapper.vm.inputMessage = '超时测试'
      await wrapper.vm.sendMessage()
      
      await wrapper.vm.$nextTick()
      
      expect(ElMessage.error).toHaveBeenCalled()
      expect(wrapper.vm.isThinking).toBe(false)
    })

    it('应该处理服务器错误', async () => {
      vi.mocked(chatService.askQuestion).mockRejectedValue({
        response: {
          status: 500,
          data: { message: 'Internal server error' }
        }
      })
      
      wrapper.vm.inputMessage = '服务器错误测试'
      await wrapper.vm.sendMessage()
      
      await wrapper.vm.$nextTick()
      
      const aiMessages = wrapper.vm.messages.filter((m: any) => m.role === 'assistant')
      expect(aiMessages[0].content).toContain('抱歉')
    })

    it('应该处理流式响应错误', async () => {
      vi.mocked(chatService.askQuestionStream).mockRejectedValue(
        new Error('Stream error')
      )
      
      wrapper.vm.inputMessage = '流式错误测试'
      await wrapper.vm.sendMessage()
      
      await new Promise(resolve => setTimeout(resolve, 500))
      
      expect(wrapper.vm.isThinking).toBe(false)
    })

    it('应该在错误后重置思考状态', async () => {
      vi.mocked(chatService.askQuestion).mockRejectedValue(
        new Error('Test error')
      )
      
      wrapper.vm.isThinking = true
      wrapper.vm.inputMessage = '重置测试'
      await wrapper.vm.sendMessage()
      
      await wrapper.vm.$nextTick()
      
      expect(wrapper.vm.isThinking).toBe(false)
    })
  })

  // ========================================
  // 5. 对话历史管理测试
  // ========================================
  
  describe('对话历史管理', () => {
    it('应该开始新对话', () => {
      wrapper.vm.messages.push({
        id: '1',
        role: 'user',
        content: '测试消息',
        timestamp: '10:00'
      })
      
      wrapper.vm.startNewChat()
      
      expect(wrapper.vm.currentChatId).toBe('')
      expect(wrapper.vm.currentChatTitle).toBe('')
      expect(wrapper.vm.messages.length).toBe(0)
    })

    it('应该加载历史对话', () => {
      const testChatId = '1'
      wrapper.vm.loadChat(testChatId)
      
      expect(wrapper.vm.currentChatId).toBe(testChatId)
      const chat = wrapper.vm.chatHistory.find((c: any) => c.id === testChatId)
      expect(wrapper.vm.currentChatTitle).toBe(chat.title)
    })

    it('应该清空当前对话', () => {
      wrapper.vm.messages.push(
        { id: '1', role: 'user', content: '消息1', timestamp: '10:00' },
        { id: '2', role: 'assistant', content: '回复1', timestamp: '10:01' }
      )
      
      wrapper.vm.clearCurrentChat()
      
      expect(wrapper.vm.messages.length).toBe(0)
    })

    it('应该更新对话历史', async () => {
      const mockResponse = {
        answer: '测试回答',
        sources: []
      }
      
      vi.mocked(chatService.askQuestion).mockResolvedValue(mockResponse)
      
      wrapper.vm.inputMessage = '历史更新测试'
      await wrapper.vm.sendMessage()
      
      await wrapper.vm.$nextTick()
      
      // 验证对话历史已更新
      const historyItem = wrapper.vm.chatHistory.find(
        (h: any) => h.lastMessage === '历史更新测试'
      )
      expect(historyItem).toBeTruthy()
    })
  })

  // ========================================
  // 6. 辅助功能测试
  // ========================================
  
  describe('辅助功能', () => {
    it('应该正确格式化消息', () => {
      const formatted = wrapper.vm.formatMessage('第一行\n第二行\n第三行')
      expect(formatted).toBe('第一行<br>第二行<br>第三行')
    })

    it('应该滚动到底部', async () => {
      // 添加多条消息
      for (let i = 0; i < 10; i++) {
        wrapper.vm.messages.push({
          id: i.toString(),
          role: 'user',
          content: `消息${i}`,
          timestamp: '10:00'
        })
      }
      
      await wrapper.vm.$nextTick()
      wrapper.vm.scrollToBottom()
      
      // 验证滚动位置
      await new Promise(resolve => setTimeout(resolve, 100))
      // 由于JSDOM限制，无法完全验证滚动行为
    })

    it('应该正确显示快速建议', () => {
      const suggestions = wrapper.vm.quickSuggestions
      expect(suggestions.length).toBeGreaterThan(0)
      expect(suggestions[0]).toContain('质量管理')
    })

    it('应该通过点击快速建议发送消息', async () => {
      const mockResponse = {
        answer: '快速建议回答',
        sources: []
      }
      
      vi.mocked(chatService.askQuestion).mockResolvedValue(mockResponse)
      
      // 获取第一个快速建议
      const firstSuggestion = wrapper.vm.quickSuggestions[0]
      
      // 模拟点击快速建议
      wrapper.vm.sendMessage(firstSuggestion)
      
      await wrapper.vm.$nextTick()
      
      // 验证消息已发送
      const userMessages = wrapper.vm.messages.filter((m: any) => m.role === 'user')
      expect(userMessages.length).toBeGreaterThan(0)
      expect(userMessages[0].content).toBe(firstSuggestion)
    })
  })

  // ========================================
  // 7. 来源标注测试
  // ========================================
  
  describe('来源标注', () => {
    it('应该可以禁用来源显示', async () => {
      wrapper.vm.enableSources = false
      
      const mockResponse = {
        answer: '没有来源的回答',
        sources: [
          { documentName: 'test.pdf', page: 1, table: '内容' }
        ]
      }
      
      vi.mocked(chatService.askQuestion).mockResolvedValue(mockResponse)
      
      wrapper.vm.inputMessage = '禁用来源测试'
      await wrapper.vm.sendMessage()
      
      await wrapper.vm.$nextTick()
      
      const aiMessages = wrapper.vm.messages.filter((m: any) => m.role === 'assistant')
      expect(aiMessages[0].sources).toBeUndefined()
    })

    it('应该显示多个来源', async () => {
      const mockResponse = {
        answer: '多来源回答',
        sources: [
          { documentName: 'doc1.pdf', page: 1, table: '内容1' },
          { documentName: 'doc2.pdf', page: 2, table: '内容2' },
          { documentName: 'doc3.pdf', page: 3, table: '内容3' }
        ]
      }
      
      vi.mocked(chatService.askQuestion).mockResolvedValue(mockResponse)
      
      wrapper.vm.enableSources = true
      wrapper.vm.inputMessage = '多来源测试'
      await wrapper.vm.sendMessage()
      
      await wrapper.vm.$nextTick()
      
      const aiMessages = wrapper.vm.messages.filter((m: any) => m.role === 'assistant')
      expect(aiMessages[0].sources).toBeDefined()
      expect(aiMessages[0].sources.length).toBe(3)
    })
  })
})
