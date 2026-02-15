// 标签管理服务
import { apiClient } from './api'
import type { Tag, PaginatedResponse } from '@/types/api'

/**
 * 标签服务类
 */
export class TagService {
  /**
   * 获取标签列表
   * @param page - 页码
   * @param pageSize - 每页数量
   * @param search - 搜索关键词
   * @returns 标签列表
   */
  async getTags(
    page: number = 1,
    pageSize: number = 20,
    search?: string
  ): Promise<PaginatedResponse<Tag>> {
    const params = new URLSearchParams({
      page: page.toString(),
      pageSize: pageSize.toString()
    })
    
    if (search) {
      params.append('search', search)
    }
    
    return apiClient.get<PaginatedResponse<Tag>>(`/tags?${params.toString()}`)
  }

  /**
   * 创建新标签
   * @param name - 标签名称
   * @param description - 标签描述
   * @param color - 标签颜色
   * @returns 创建的标签
   */
  async createTag(
    name: string,
    description?: string,
    color?: string
  ): Promise<Tag> {
    return apiClient.post<Tag>('/tags', {
      name,
      description,
      color
    })
  }

  /**
   * 更新标签
   * @param tagId - 标签ID
   * @param updates - 更新内容
   * @returns 更新后的标签
   */
  async updateTag(
    tagId: string,
    updates: {
      name?: string
      description?: string
      color?: string
    }
  ): Promise<Tag> {
    return apiClient.put<Tag>(`/tags/${tagId}`, updates)
  }

  /**
   * 删除标签
   * @param tagId - 标签ID
   */
  async deleteTag(tagId: string): Promise<void> {
    return apiClient.delete(`/tags/${tagId}`)
  }

  /**
   * 获取标签统计信息
   * @returns 标签统计
   */
  async getTagStats(): Promise<{
    totalTags: number
    totalDocuments: number
    averageDocumentsPerTag: number
    mostUsedTags: Array<{
      tagId: string
      tagName: string
      documentCount: number
    }>
  }> {
    return apiClient.get('/tags/stats')
  }

  /**
   * 获取标签下的文档
   * @param tagId - 标签ID
   * @param page - 页码
   * @param pageSize - 每页数量
   * @returns 文档列表
   */
  async getTaggedDocuments(
    tagId: string,
    page: number = 1,
    pageSize: number = 10
  ): Promise<PaginatedResponse<any>> {
    const params = new URLSearchParams({
      page: page.toString(),
      pageSize: pageSize.toString()
    })
    
    return apiClient.get<PaginatedResponse<any>>(`/tags/${tagId}/documents?${params.toString()}`)
  }

  /**
   * 批量添加文档标签
   * @param documentIds - 文档ID列表
   * @param tagIds - 标签ID列表
   */
  async addTagsToDocuments(
    documentIds: string[],
    tagIds: string[]
  ): Promise<void> {
    return apiClient.post('/tags/batch/add', {
      documentIds,
      tagIds
    })
  }

  /**
   * 批量移除文档标签
   * @param documentIds - 文档ID列表
   * @param tagIds - 标签ID列表
   */
  async removeTagsFromDocuments(
    documentIds: string[],
    tagIds: string[]
  ): Promise<void> {
    return apiClient.post('/tags/batch/remove', {
      documentIds,
      tagIds
    })
  }

  /**
   * 搜索标签
   * @param query - 搜索查询
   * @param limit - 返回数量限制
   * @returns 标签列表
   */
  async searchTags(query: string, limit: number = 10): Promise<Tag[]> {
    return apiClient.get<Tag[]>(`/tags/search?query=${encodeURIComponent(query)}&limit=${limit}`)
  }
}

// 创建标签服务实例
export const tagService = new TagService()