// 修正库服务
import { apiClient } from './api'

export interface Correction {
  id: number
  question: string
  correct_answer: string
  original_answer?: string
  source_doc?: string
  page_number?: number
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface CorrectionCreate {
  question: string
  correct_answer: string
  original_answer?: string
  source_doc?: string
  page_number?: number
}

export interface CorrectionUpdate {
  correct_answer?: string
  is_active?: boolean
  source_doc?: string
  page_number?: number
}

export interface PaginatedCorrections {
  items: Correction[]
  total: number
  limit: number
  offset: number
}

export interface CorrectionStats {
  active: number
  total: number
  inactive: number
}

/**
 * 修正库服务
 */
export class CorrectionService {
  /**
   * 创建修正记录
   * @param data - 修正数据
   */
  async createCorrection(data: CorrectionCreate): Promise<{ id: number; message: string }> {
    return apiClient.post('/corrections', data)
  }

  /**
   * 获取修正记录列表
   * @param keyword - 搜索关键词
   * @param isActive - 是否只显示激活的
   * @param limit - 每页数量
   * @param offset - 偏移量
   */
  async listCorrections(
    keyword?: string,
    isActive?: boolean,
    limit: number = 50,
    offset: number = 0
  ): Promise<PaginatedCorrections> {
    const params = new URLSearchParams()
    if (keyword) params.append('keyword', keyword)
    if (isActive !== undefined) params.append('is_active', isActive.toString())
    params.append('limit', limit.toString())
    params.append('offset', offset.toString())

    return apiClient.get<PaginatedCorrections>(`/corrections?${params.toString()}`)
  }

  /**
   * 获取单个修正记录
   * @param id - 修正记录ID
   */
  async getCorrection(id: number): Promise<Correction> {
    return apiClient.get<Correction>(`/corrections/${id}`)
  }

  /**
   * 更新修正记录
   * @param id - 修正记录ID
   * @param data - 更新数据
   */
  async updateCorrection(id: number, data: CorrectionUpdate): Promise<{ message: string }> {
    return apiClient.put(`/corrections/${id}`, data)
  }

  /**
   * 删除修正记录（软删除）
   * @param id - 修正记录ID
   * @param hard - 是否硬删除
   */
  async deleteCorrection(id: number, hard: boolean = false): Promise<{ message: string }> {
    return apiClient.delete(`/corrections/${id}?hard=${hard}`)
  }

  /**
   * 获取修正库统计信息
   */
  async getStats(): Promise<CorrectionStats> {
    return apiClient.get<CorrectionStats>('/corrections/stats')
  }

  /**
   * 搜索修正记录
   * @param query - 查询文本
   */
  async searchCorrections(query: string): Promise<PaginatedCorrections> {
    return this.listCorrections(query)
  }
}

// 创建服务实例
export const correctionService = new CorrectionService()
