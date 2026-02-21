// 知识库服务
import { apiClient } from './api'

export interface KnowledgeBase {
  id: string
  name: string
  description: string
  collection_name: string
  created_at: string
  updated_at: string
  is_active: boolean
  document_count: number
}

export interface KnowledgeBaseCreate {
  id: string
  name: string
  description?: string
}

export interface KnowledgeBaseUpdate {
  name?: string
  description?: string
}

const CURRENT_KB_KEY = 'qms_current_kb'

/**
 * 知识库服务
 */
export class KnowledgeBaseService {
  /**
   * 创建知识库
   * @param data - 知识库数据
   */
  async createKnowledgeBase(data: KnowledgeBaseCreate): Promise<{ id: string; message: string }> {
    return apiClient.post('/knowledge-bases', data)
  }

  /**
   * 获取知识库列表
   * @param includeInactive - 是否包含已删除的
   */
  async listKnowledgeBases(includeInactive: boolean = false): Promise<KnowledgeBase[]> {
    return apiClient.get<KnowledgeBase[]>(`/knowledge-bases?include_inactive=${includeInactive}`)
  }

  /**
   * 获取单个知识库
   * @param kbId - 知识库ID
   */
  async getKnowledgeBase(kbId: string): Promise<KnowledgeBase> {
    return apiClient.get<KnowledgeBase>(`/knowledge-bases/${kbId}`)
  }

  /**
   * 更新知识库
   * @param kbId - 知识库ID
   * @param data - 更新数据
   */
  async updateKnowledgeBase(kbId: string, data: KnowledgeBaseUpdate): Promise<{ message: string }> {
    return apiClient.put(`/knowledge-bases/${kbId}`, data)
  }

  /**
   * 删除知识库
   * @param kbId - 知识库ID
   * @param hard - 是否硬删除
   */
  async deleteKnowledgeBase(kbId: string, hard: boolean = false): Promise<{ message: string }> {
    return apiClient.delete(`/knowledge-bases/${kbId}?hard=${hard}`)
  }

  /**
   * 切换当前知识库
   * @param kbId - 知识库ID
   */
  async switchKnowledgeBase(kbId: string): Promise<{ message: string; kb_id: string; collection_name: string }> {
    const result = await apiClient.post(`/knowledge-bases/${kbId}/switch`)
    // 保存到本地存储
    localStorage.setItem(CURRENT_KB_KEY, kbId)
    return result
  }

  /**
   * 获取当前选择的知识库ID
   */
  getCurrentKnowledgeBaseId(): string {
    return localStorage.getItem(CURRENT_KB_KEY) || 'default'
  }

  /**
   * 获取当前选择的知识库名称
   */
  async getCurrentKnowledgeBaseName(): Promise<string> {
    const kbId = this.getCurrentKnowledgeBaseId()
    if (kbId === 'default') {
      return '默认知识库'
    }
    try {
      const kb = await this.getKnowledgeBase(kbId)
      return kb.name
    } catch {
      return '默认知识库'
    }
  }

  /**
   * 设置当前知识库（仅本地存储）
   * @param kbId - 知识库ID
   */
  setCurrentKnowledgeBase(kbId: string): void {
    localStorage.setItem(CURRENT_KB_KEY, kbId)
  }

  /**
   * 获取当前知识库对应的 collection 名称
   */
  getCurrentCollection(): string {
    const kbId = this.getCurrentKnowledgeBaseId()
    return kbId === 'default' ? 'qms_docs' : `kb_${kbId}`
  }

  /**
   * 清除当前知识库选择（恢复到默认）
   */
  clearCurrentKnowledgeBase(): void {
    localStorage.removeItem(CURRENT_KB_KEY)
  }
}

// 创建服务实例
export const knowledgeBaseService = new KnowledgeBaseService()
