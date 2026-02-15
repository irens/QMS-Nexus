// 文档服务
import { apiClient } from './api'
import type { 
  Document, 
  PaginatedResponse, 
  SearchRequest, 
  SearchResult,
  Tag 
} from '@/types/api'

export interface DocumentQuery {
  page?: number
  pageSize?: number
  search?: string
  fileType?: string[]
  tags?: string[]
  status?: string[]
  dateRange?: [string, string]
  sortBy?: 'uploadTime' | 'fileName' | 'fileSize'
  sortOrder?: 'asc' | 'desc'
}

/**
 * 文档服务
 */
export class DocumentService {
  /**
   * 创建新文档
   * @param documentData - 文档数据
   * @returns 创建的文档
   */
  async createDocument(documentData: Partial<Document>): Promise<Document> {
    return apiClient.post<Document>('/documents', documentData)
  }

  /**
   * 获取文档列表
   * @param query - 查询参数
   * @returns 分页的文档列表
   */
  async getDocuments(query: DocumentQuery = {}): Promise<PaginatedResponse<Document>> {
    const params = new URLSearchParams()
    
    if (query.page) params.append('page', query.page.toString())
    if (query.pageSize) params.append('pageSize', query.pageSize.toString())
    if (query.search) params.append('search', query.search)
    if (query.sortBy) params.append('sortBy', query.sortBy)
    if (query.sortOrder) params.append('sortOrder', query.sortOrder)
    
    if (query.fileType?.length) {
      query.fileType.forEach(type => params.append('fileType', type))
    }
    
    if (query.tags?.length) {
      query.tags.forEach(tag => params.append('tags', tag))
    }
    
    if (query.status?.length) {
      query.status.forEach(status => params.append('status', status))
    }
    
    if (query.dateRange) {
      params.append('startDate', query.dateRange[0])
      params.append('endDate', query.dateRange[1])
    }
    
    const queryString = params.toString()
    const url = `/documents${queryString ? '?' + queryString : ''}`
    
    return apiClient.get<PaginatedResponse<Document>>(url)
  }
  
  /**
   * 获取单个文档
   * @param documentId - 文档ID
   * @returns 文档详情
   */
  async getDocument(documentId: string): Promise<Document> {
    return apiClient.get<Document>(`/documents/${documentId}`)
  }
  
  /**
   * 删除文档
   * @param documentId - 文档ID
   */
  async deleteDocument(documentId: string): Promise<void> {
    await apiClient.delete(`/documents/${documentId}`)
  }
  
  /**
   * 批量删除文档
   * @param documentIds - 文档ID列表
   */
  async deleteDocuments(documentIds: string[]): Promise<void> {
    await apiClient.delete('/documents', {
      data: { documentIds }
    })
  }
  
  /**
   * 更新文档标签
   * @param documentId - 文档ID
   * @param tags - 标签列表
   */
  async updateDocumentTags(documentId: string, tags: string[]): Promise<Document> {
    return apiClient.put<Document>(`/documents/${documentId}/tags`, { tags })
  }
  
  /**
   * 搜索文档内容
   * @param query - 搜索查询
   * @returns 搜索结果
   */
  async searchDocuments(query: SearchRequest): Promise<SearchResult[]> {
    const params = new URLSearchParams()
    params.append('q', query.query)
    
    if (query.filterTags?.length) {
      query.filterTags.forEach(tag => params.append('filter_tags', tag))
    }
    
    if (query.topK) {
      params.append('top_k', query.topK.toString())
    }
    
    if (query.page) {
      params.append('page', query.page.toString())
    }
    
    if (query.pageSize) {
      params.append('pageSize', query.pageSize.toString())
    }
    
    return apiClient.get<SearchResult[]>(`/search?${params.toString()}`)
  }
  
  /**
   * 下载文档
   * @param documentId - 文档ID
   * @param filename - 文件名（可选）
   */
  async downloadDocument(documentId: string, filename?: string): Promise<void> {
    await apiClient.download(`/documents/${documentId}/download`, filename)
  }
  
  /**
   * 预览文档
   * @param documentId - 文档ID
   * @param page - 页码（可选）
   * @returns 文档内容
   */
  async previewDocument(documentId: string, page?: number): Promise<string> {
    const params = page ? `?page=${page}` : ''
    return apiClient.get<string>(`/documents/${documentId}/preview${params}`)
  }
  
  /**
   * 获取文档统计信息
   * @returns 文档统计信息
   */
  async getDocumentStats(): Promise<{
    total: number
    byType: Record<string, number>
    byStatus: Record<string, number>
    byTag: Record<string, number>
    recentUploads: number
  }> {
    return apiClient.get('/documents/stats')
  }
  
  /**
   * 获取相关文档
   * @param documentId - 文档ID
   * @param limit - 返回数量限制
   * @returns 相关文档列表
   */
  async getRelatedDocuments(documentId: string, limit: number = 5): Promise<Document[]> {
    return apiClient.get<Document[]>(`/documents/${documentId}/related?limit=${limit}`)
  }
  
  /**
   * 批量更新文档状态
   * @param documentIds - 文档ID列表
   * @param status - 新状态
   */
  async updateDocumentsStatus(documentIds: string[], status: string): Promise<void> {
    await apiClient.put('/documents/batch/status', { documentIds, status })
  }
  
  /**
   * 批量更新文档标签
   * @param documentIds - 文档ID列表
   * @param tags - 标签列表
   * @param operation - 操作类型：add、remove、replace
   */
  async batchUpdateTags(
    documentIds: string[], 
    tags: string[], 
    operation: 'add' | 'remove' | 'replace' = 'add'
  ): Promise<void> {
    await apiClient.put('/documents/batch/tags', { documentIds, tags, operation })
  }
}

/**
 * 标签服务
 */
export class TagService {
  /**
   * 获取所有标签
   * @returns 标签列表
   */
  async getTags(): Promise<Tag[]> {
    return apiClient.get<Tag[]>('/tags')
  }
  
  /**
   * 创建标签
   * @param name - 标签名
   * @param description - 描述（可选）
   * @param color - 颜色（可选）
   * @returns 新创建的标签
   */
  async createTag(name: string, description?: string, color?: string): Promise<Tag> {
    return apiClient.post<Tag>('/tags', { name, description, color })
  }
  
  /**
   * 更新标签
   * @param tagId - 标签ID
   * @param data - 更新数据
   */
  async updateTag(tagId: string, data: { name?: string; description?: string; color?: string }): Promise<Tag> {
    return apiClient.put<Tag>(`/tags/${tagId}`, data)
  }
  
  /**
   * 删除标签
   * @param tagId - 标签ID
   */
  async deleteTag(tagId: string): Promise<void> {
    await apiClient.delete(`/tags/${tagId}`)
  }
  
  /**
   * 获取标签统计信息
   * @returns 标签使用统计
   */
  async getTagStats(): Promise<{
    total: number
    mostUsed: Tag[]
    recentlyCreated: Tag[]
  }> {
    return apiClient.get('/tags/stats')
  }
  
  /**
   * 搜索标签
   * @param query - 搜索关键词
   * @returns 匹配的标签列表
   */
  async searchTags(query: string): Promise<Tag[]> {
    return apiClient.get<Tag[]>(`/tags/search?q=${encodeURIComponent(query)}`)
  }
}

// 创建服务实例
export const documentService = new DocumentService()
export const tagService = new TagService()

// 默认导出
export default {
  documents: documentService,
  tags: tagService
}