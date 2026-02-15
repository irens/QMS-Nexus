// 问答服务
import { apiClient } from './api'
import type { AskRequest, AskResponse, ChatMessage } from '@/types/api'

/**
 * 问答服务类
 */
export class ChatService {
  /**
   * 发送问答请求
   * @param question - 用户问题
   * @param context - 上下文信息
   * @param filterTags - 标签筛选
   * @param topK - 返回结果数量
   * @returns 问答响应
   */
  async askQuestion(
    question: string,
    context?: string[],
    filterTags?: string[],
    topK: number = 5
  ): Promise<AskResponse> {
    const request: AskRequest = {
      question,
      context,
      filterTags,
      topK
    }
    
    return apiClient.post<AskResponse>('/ask', request)
  }

  /**
   * 流式问答 - 支持流式响应
   * @param question - 用户问题
   * @param context - 上下文信息
   * @param filterTags - 标签筛选
   * @param topK - 返回结果数量
   * @param onChunk - 接收流式数据的回调函数
   */
  async askQuestionStream(
    question: string,
    context?: string[],
    filterTags?: string[],
    topK: number = 5,
    onChunk?: (chunk: string) => void
  ): Promise<AskResponse> {
    const request: AskRequest = {
      question,
      context,
      filterTags,
      topK
    }

    // 如果使用流式回调，使用EventSource或WebSocket
    if (onChunk) {
      return this.streamAskRequest(request, onChunk)
    } else {
      // 普通请求
      return apiClient.post<AskResponse>('/ask', request)
    }
  }

  /**
   * 流式请求实现
   */
  private async streamAskRequest(
    request: AskRequest,
    onChunk: (chunk: string) => void
  ): Promise<AskResponse> {
    return new Promise((resolve, reject) => {
      const eventSource = new EventSource(
        `/api/v1/ask/stream?question=${encodeURIComponent(request.question)}` +
        (request.context ? `&context=${encodeURIComponent(JSON.stringify(request.context))}` : '') +
        (request.filterTags ? `&filterTags=${encodeURIComponent(JSON.stringify(request.filterTags))}` : '') +
        `&topK=${request.topK}`
      )

      let fullResponse = ''
      let sources: AskResponse['sources'] = []

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'chunk') {
            fullResponse += data.content
            onChunk(data.content)
          } else if (data.type === 'sources') {
            sources = data.sources
          } else if (data.type === 'complete') {
            eventSource.close()
            resolve({
              answer: fullResponse,
              sources,
              totalTokens: data.totalTokens || 0,
              responseTime: data.responseTime || 0
            })
          } else if (data.type === 'error') {
            eventSource.close()
            reject(new Error(data.message))
          }
        } catch (error) {
          eventSource.close()
          reject(error)
        }
      }

      eventSource.onerror = () => {
        eventSource.close()
        reject(new Error('流式连接失败'))
      }

      // 设置超时
      setTimeout(() => {
        eventSource.close()
        reject(new Error('流式请求超时'))
      }, 60000) // 60秒超时
    })
  }

  /**
   * 获取问答历史
   * @param page - 页码
   * @param pageSize - 每页数量
   * @returns 问答历史列表
   */
  async getChatHistory(page: number = 1, pageSize: number = 20): Promise<{
    items: ChatMessage[]
    total: number
    page: number
    pageSize: number
  }> {
    return apiClient.get(`/chat/history?page=${page}&pageSize=${pageSize}`)
  }

  /**
   * 保存对话
   * @param title - 对话标题
   * @param messages - 对话消息列表
   */
  async saveConversation(
    title: string,
    messages: ChatMessage[]
  ): Promise<{ conversationId: string }> {
    return apiClient.post('/chat/conversations', {
      title,
      messages
    })
  }

  /**
   * 获取对话详情
   * @param conversationId - 对话ID
   */
  async getConversation(conversationId: string): Promise<{
    id: string
    title: string
    messages: ChatMessage[]
    createdAt: string
    updatedAt: string
  }> {
    return apiClient.get(`/chat/conversations/${conversationId}`)
  }

  /**
   * 获取对话列表
   * @param page - 页码
   * @param pageSize - 每页数量
   */
  async getConversations(page: number = 1, pageSize: number = 10): Promise<{
    items: Array<{
      id: string
      title: string
      messageCount: number
      createdAt: string
      updatedAt: string
    }>
    total: number
    page: number
    pageSize: number
  }> {
    return apiClient.get(`/chat/conversations?page=${page}&pageSize=${pageSize}`)
  }

  /**
   * 删除对话
   * @param conversationId - 对话ID
   */
  async deleteConversation(conversationId: string): Promise<void> {
    return apiClient.delete(`/chat/conversations/${conversationId}`)
  }
}

// 创建问答服务实例
export const chatService = new ChatService()