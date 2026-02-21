// 问答服务
import { apiClient } from './api'
import { knowledgeBaseService } from './knowledgeBase'

export interface AskRequest {
  question: string
  collection?: string
  skip_correction?: boolean
}

export interface AskResponse {
  answer: string
  sources: string[]
  is_corrected?: boolean
  correction_id?: number
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
    }
  ): Promise<AskResponse> {
    const collection = options?.collection || knowledgeBaseService.getCurrentCollection()
    
    const request: AskRequest = {
      question,
      collection,
      skip_correction: options?.skipCorrection || false
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
}

// 创建问答服务实例
export const chatService = new ChatService()
