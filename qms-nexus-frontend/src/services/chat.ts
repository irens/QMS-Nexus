// 问答服务
import { apiClient } from './api'
import { knowledgeBaseService } from './knowledgeBase'

export interface AskRequest {
  question: string
  collection?: string
  skip_correction?: boolean
  version_strategy?: 'latest_effective' | 'specific_date' | 'all_versions'
  specific_date?: string
  include_version_info?: boolean
}

export interface Source {
  document_name: string
  version_id: string
  version_number: number
  version_label: string
  status: 'draft' | 'review' | 'approved' | 'effective' | 'obsolete'
  is_latest: boolean
  effective_date?: string
  page: number
  score: number
  warning?: string
}

export interface AskResponse {
  answer: string
  sources: string[]
  is_corrected?: boolean
  correction_id?: number
  version_info_included?: boolean
  version_sources?: Source[]
}

export interface AskWithCorrectionRequest {
  question: string
  correct_answer?: string
  save_correction?: boolean
  collection?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  sources?: string[]
  isCorrected?: boolean
  correctionId?: number
  timestamp: string
}

/**
 * 问答服务类
 */
export class ChatService {
  /**
   * 发送问答请求
   * @param question - 用户问题
   * @param options - 可选参数
   * @returns 问答响应
   */
  async askQuestion(
    question: string,
    options?: {
      collection?: string
      skipCorrection?: boolean
      versionStrategy?: 'latest_effective' | 'specific_date' | 'all_versions'
      specificDate?: string
      includeVersionInfo?: boolean
    }
  ): Promise<AskResponse> {
    const collection = options?.collection || knowledgeBaseService.getCurrentCollection()

    const request: AskRequest = {
      question,
      collection,
      skip_correction: options?.skipCorrection || false,
      version_strategy: options?.versionStrategy || 'latest_effective',
      specific_date: options?.specificDate,
      include_version_info: options?.includeVersionInfo ?? true
    }

    return apiClient.post<AskResponse>('/ask', request)
  }

  /**
   * 提交修正答案
   * @param question - 问题
   * @param correctAnswer - 正确答案
   * @param options - 可选参数
   * @returns 问答响应
   */
  async submitCorrection(
    question: string,
    correctAnswer: string,
    options?: {
      collection?: string
      saveCorrection?: boolean
    }
  ): Promise<AskResponse> {
    const collection = options?.collection || knowledgeBaseService.getCurrentCollection()
    
    const request: AskWithCorrectionRequest = {
      question,
      correct_answer: correctAnswer,
      save_correction: options?.saveCorrection ?? true,
      collection
    }
    
    return apiClient.post<AskResponse>('/ask-with-correction', request)
  }

  /**
   * 保存修正记录
   * @param question - 问题
   * @param correctAnswer - 正确答案
   * @param originalAnswer - 原答案（可选）
   * @param sourceDoc - 来源文档（可选）
   */
  async saveCorrection(
    question: string,
    correctAnswer: string,
    originalAnswer?: string,
    sourceDoc?: string
  ): Promise<{ id: number; message: string }> {
    return apiClient.post('/corrections', {
      question,
      correct_answer: correctAnswer,
      original_answer: originalAnswer,
      source_doc: sourceDoc
    })
  }

  /**
   * 获取问答历史（本地存储）
   */
  getChatHistory(): ChatMessage[] {
    const history = localStorage.getItem('qms_chat_history')
    return history ? JSON.parse(history) : []
  }

  /**
   * 保存问答历史到本地存储
   * @param messages - 消息列表
   */
  saveChatHistory(messages: ChatMessage[]): void {
    localStorage.setItem('qms_chat_history', JSON.stringify(messages))
  }

  /**
   * 清空问答历史
   */
  clearChatHistory(): void {
    localStorage.removeItem('qms_chat_history')
  }

  /**
   * 添加消息到历史
   * @param message - 消息
   */
  addMessageToHistory(message: ChatMessage): void {
    const history = this.getChatHistory()
    history.push(message)
    // 只保留最近100条
    if (history.length > 100) {
      history.shift()
    }
    this.saveChatHistory(history)
  }

  /**
   * 流式问答请求
   * @param question - 用户问题
   * @param onChunk - 接收到数据块的回调
   * @param options - 可选参数
   * @returns 问答响应
   */
  async askQuestionStream(
    question: string,
    onChunk: (chunk: string) => void,
    options?: {
      collection?: string
      skipCorrection?: boolean
      versionStrategy?: 'latest_effective' | 'specific_date' | 'all_versions'
      specificDate?: string
      includeVersionInfo?: boolean
    }
  ): Promise<AskResponse> {
    const collection = options?.collection || knowledgeBaseService.getCurrentCollection()

    const request: AskRequest = {
      question,
      collection,
      skip_correction: options?.skipCorrection || false,
      version_strategy: options?.versionStrategy || 'latest_effective',
      specific_date: options?.specificDate,
      include_version_info: options?.includeVersionInfo ?? true
    }

    // 使用 fetch API 进行 SSE 流式请求
    const response = await fetch(`${apiClient.getBaseUrl()}/ask/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    let fullResponse = ''
    let finalData: AskResponse | null = null

    if (reader) {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              break
            }
            try {
              const parsed = JSON.parse(data)
              if (parsed.chunk) {
                fullResponse += parsed.chunk
                onChunk(parsed.chunk)
              } else if (parsed.answer) {
                // 最终响应包含完整数据
                finalData = parsed as AskResponse
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
    }

    return finalData || {
      answer: fullResponse,
      sources: []
    }
  }

  /**
   * 对比两个文档版本
   * @param documentId - 文档ID
   * @param v1Id - 版本1 ID
   * @param v2Id - 版本2 ID
   * @returns 版本对比结果
   */
  async compareVersions(
    documentId: string,
    v1Id: string,
    v2Id: string
  ): Promise<{
    summary: string
    added_sections: string[]
    removed_sections: string[]
    modified_sections: string[]
    key_changes: string[]
    v1_info: {
      version_id: string
      version_label: string
      version_number: number
      status: string
      change_summary?: string
    }
    v2_info: {
      version_id: string
      version_label: string
      version_number: number
      status: string
      change_summary?: string
    }
  }> {
    return apiClient.get(`/documents/versions/${v1Id}/compare/${v2Id}`)
  }

  /**
   * 记录错误日志
   * @param errorInfo - 错误信息
   */
  async logError(errorInfo: {
    error: string
    stack?: string
    component: string
    info: string
  }): Promise<void> {
    try {
      await apiClient.post('/logs/error', errorInfo)
    } catch (e) {
      console.error('Failed to log error:', e)
    }
  }
}

// 创建问答服务实例
export const chatService = new ChatService()
