// Chat Service 测试
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ChatService } from '../chat'
import type { AskRequest, AskResponse } from '@/types/api'

// Mock apiClient
vi.mock('../api', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn()
  }
}))

import { apiClient } from '../api'

describe('ChatService', () => {
  let chatService: ChatService

  beforeEach(() => {
    vi.clearAllMocks()
    chatService = new ChatService()
  })

  describe('askQuestion', () => {
    it('应该成功发送问答请求', async () => {
      const mockResponse: AskResponse = {
        answer: '这是AI的回答',
        sources: [
          {
            documentId: 'doc-1',
            documentName: '医疗器械质量管理规范.pdf',
            pageNumber: 5,
            relevance: 0.95
          }
        ],
        sessionId: 'session-123',
        timestamp: Date.now()
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await chatService.askQuestion('什么是ISO 13485？')

      expect(result).toEqual(mockResponse)
      expect(apiClient.post).toHaveBeenCalledWith('/ask', {
        question: '什么是ISO 13485？',
        context: undefined,
        filterTags: undefined,
        topK: 5
      })
    })

    it('应该支持上下文参数', async () => {
      const mockResponse: AskResponse = {
        answer: '基于上下文的回答',
        sources: [],
        sessionId: 'session-456',
        timestamp: Date.now()
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const context = ['之前的对话内容1', '之前的对话内容2']
      await chatService.askQuestion('请继续解释', context)

      expect(apiClient.post).toHaveBeenCalledWith('/ask', {
        question: '请继续解释',
        context,
        filterTags: undefined,
        topK: 5
      })
    })

    it('应该支持标签筛选', async () => {
      const mockResponse: AskResponse = {
        answer: '标签筛选后的回答',
        sources: [],
        sessionId: 'session-789',
        timestamp: Date.now()
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const filterTags = ['质量管理', 'ISO 13485']
      await chatService.askQuestion('相关标准是什么？', undefined, filterTags)

      expect(apiClient.post).toHaveBeenCalledWith('/ask', {
        question: '相关标准是什么？',
        context: undefined,
        filterTags,
        topK: 5
      })
    })

    it('应该支持自定义topK参数', async () => {
      const mockResponse: AskResponse = {
        answer: '自定义topK的回答',
        sources: [],
        sessionId: 'session-999',
        timestamp: Date.now()
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      await chatService.askQuestion('问题', undefined, undefined, 10)

      expect(apiClient.post).toHaveBeenCalledWith('/ask', {
        question: '问题',
        context: undefined,
        filterTags: undefined,
        topK: 10
      })
    })

    it('应该处理API调用失败', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'))

      await expect(
        chatService.askQuestion('失败的问题')
      ).rejects.toThrow('Network error')
    })

    it('应该处理超时错误', async () => {
      vi.mocked(apiClient.post).mockRejectedValue({
        message: 'Request timeout',
        code: 'ECONNABORTED'
      })

      await expect(
        chatService.askQuestion('超时测试')
      ).rejects.toMatchObject({
        message: 'Request timeout',
        code: 'ECONNABORTED'
      })
    })
  })

  describe('askQuestionStream', () => {
    beforeEach(() => {
      // Mock EventSource
      global.EventSource = vi.fn().mockImplementation(() => ({
        close: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        onmessage: null,
        onerror: null,
        onopen: null
      }))
    })

    it('应该支持流式响应', async () => {
      const mockResponse: AskResponse = {
        answer: '流式回答',
        sources: [],
        sessionId: 'stream-session',
        timestamp: Date.now()
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const onChunk = vi.fn()
      const result = await chatService.askQuestionStream('流式问题', undefined, undefined, 5, onChunk)

      expect(result).toEqual(mockResponse)
      expect(onChunk).toHaveBeenCalled() // 流式回调应该被调用
    })

    it('应该不使用流式当没有提供回调', async () => {
      const mockResponse: AskResponse = {
        answer: '普通回答',
        sources: [],
        sessionId: 'normal-session',
        timestamp: Date.now()
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await chatService.askQuestionStream('普通问题')

      expect(result).toEqual(mockResponse)
      expect(apiClient.post).toHaveBeenCalledWith('/ask', {
        question: '普通问题',
        context: undefined,
        filterTags: undefined,
        topK: 5
      })
    })

    it('应该处理流式响应错误', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Stream error'))

      const onChunk = vi.fn()
      await expect(
        chatService.askQuestionStream('错误流式', undefined, undefined, 5, onChunk)
      ).rejects.toThrow('Stream error')
    })
  })

  describe('错误处理', () => {
    it('应该处理网络错误', async () => {
      vi.mocked(apiClient.post).mockRejectedValue({
        message: 'Network Error',
        code: 'ERR_NETWORK'
      })

      await expect(
        chatService.askQuestion('网络错误测试')
      ).rejects.toMatchObject({
        message: 'Network Error',
        code: 'ERR_NETWORK'
      })
    })

    it('应该处理404错误', async () => {
      vi.mocked(apiClient.post).mockRejectedValue({
        message: 'Not Found',
        status: 404
      })

      await expect(
        chatService.askQuestion('404测试')
      ).rejects.toMatchObject({
        message: 'Not Found',
        status: 404
      })
    })

    it('应该处理500服务器错误', async () => {
      vi.mocked(apiClient.post).mockRejectedValue({
        message: 'Internal Server Error',
        status: 500
      })

      await expect(
        chatService.askQuestion('500测试')
      ).rejects.toMatchObject({
        message: 'Internal Server Error',
        status: 500
      })
    })

    it('应该处理空回复', async () => {
      const mockResponse: AskResponse = {
        answer: '',
        sources: [],
        sessionId: 'empty-session',
        timestamp: Date.now()
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await chatService.askQuestion('空回复测试')

      expect(result.answer).toBe('')
      expect(result.sources).toEqual([])
    })
  })

  describe('边界情况', () => {
    it('应该处理空字符串问题', async () => {
      const mockResponse: AskResponse = {
        answer: '请提供有效的问题',
        sources: [],
        sessionId: 'empty-question',
        timestamp: Date.now()
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await chatService.askQuestion('')

      expect(result.answer).toBe('请提供有效的问题')
    })

    it('应该处理超长问题', async () => {
      const longQuestion = 'a'.repeat(10000)
      const mockResponse: AskResponse = {
        answer: '问题过长，请简化',
        sources: [],
        sessionId: 'long-question',
        timestamp: Date.now()
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await chatService.askQuestion(longQuestion)

      expect(result.answer).toBe('问题过长，请简化')
    })

    it('应该处理特殊字符问题', async () => {
      const mockResponse: AskResponse = {
        answer: '已处理特殊字符',
        sources: [],
        sessionId: 'special-chars',
        timestamp: Date.now()
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await chatService.askQuestion('问题<>&"\'\\n')

      expect(result.answer).toBe('已处理特殊字符')
      expect(apiClient.post).toHaveBeenCalledWith('/ask', {
        question: '问题<>&"\'\\n',
        context: undefined,
        filterTags: undefined,
        topK: 5
      })
    })
  })
})
