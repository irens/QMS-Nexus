// 文档状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Document } from '@/types/api'
import { documentService } from '@/services/document'
import { APP_CONFIG } from '@/constants'

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

export interface DocumentState {
  documents: Document[]
  total: number
  currentPage: number
  pageSize: number
  loading: boolean
  error: string | null
  selectedIds: string[]
  query: DocumentQuery
  cache: Map<string, { data: Document[]; timestamp: number }>
  lastFetchTime: number
}

export const useDocumentStore = defineStore('document', () => {
  // 状态
  const documents = ref<Document[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const selectedIds = ref<string[]>([])
  const query = ref<DocumentQuery>({})
  const cache = ref(new Map<string, { data: Document[]; timestamp: number }>())
  const lastFetchTime = ref(0)
  
  // 计算属性
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
  const hasMore = computed(() => currentPage.value < totalPages.value)
  const isCacheValid = computed(() => {
    const now = Date.now()
    return now - lastFetchTime.value < APP_CONFIG.CACHE_CONFIG.DOCUMENT_LIST
  })
  
  const selectedDocuments = computed(() => 
    documents.value.filter(doc => selectedIds.value.includes(doc.id))
  )
  
  const documentsByStatus = computed(() => {
    const map = new Map<string, Document[]>()
    documents.value.forEach(doc => {
      const list = map.get(doc.status) || []
      list.push(doc)
      map.set(doc.status, list)
    })
    return map
  })
  
  const documentsByType = computed(() => {
    const map = new Map<string, Document[]>()
    documents.value.forEach(doc => {
      const list = map.get(doc.fileType) || []
      list.push(doc)
      map.set(doc.fileType, list)
    })
    return map
  })
  
  // 方法
  /**
   * 获取文档列表
   */
  async function fetchDocuments(newQuery: DocumentQuery = {}): Promise<void> {
    try {
      loading.value = true
      error.value = null
      
      // 合并查询参数
      const finalQuery = { ...query.value, ...newQuery }
      query.value = finalQuery
      
      // 检查缓存
      const cacheKey = JSON.stringify(finalQuery)
      const cachedData = cache.value.get(cacheKey)
      if (cachedData && Date.now() - cachedData.timestamp < APP_CONFIG.CACHE_CONFIG.DOCUMENT_LIST) {
        // ✅ 验证缓存数据完整性和有效性
        if (Array.isArray(cachedData.data) && cachedData.total !== undefined) {
          documents.value = cachedData.data
          total.value = cachedData.total
          loading.value = false
          return
        }
        // ❌ 缓存数据无效，清除缓存并继续获取新数据
        cache.value.delete(cacheKey)
      }
      
      // 调用API
      const response = await documentService.getDocuments(finalQuery)
      
      // 更新状态
      documents.value = response.items
      total.value = response.total
      currentPage.value = response.page
      pageSize.value = response.pageSize
      lastFetchTime.value = Date.now()
      
      // 更新缓存
      cache.value.set(cacheKey, {
        data: response.items,
        timestamp: Date.now()
      })
      
      // 清理过期缓存
      cleanupCache()
      
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取文档列表失败'
      console.error('Failed to fetch documents:', err)
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取单个文档
   */
  async function fetchDocument(documentId: string): Promise<Document | null> {
    try {
      const document = await documentService.getDocument(documentId)
      
      // 更新本地缓存
      const index = documents.value.findIndex(doc => doc.id === documentId)
      if (index !== -1) {
        documents.value[index] = document
      }
      
      return document
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取文档详情失败'
      console.error('Failed to fetch document:', err)
      return null
    }
  }
  
  /**
   * 删除文档
   */
  async function deleteDocument(documentId: string): Promise<boolean> {
    try {
      await documentService.deleteDocument(documentId)
      
      // 从列表中移除
      const index = documents.value.findIndex(doc => doc.id === documentId)
      if (index !== -1) {
        documents.value.splice(index, 1)
        total.value--
      }
      
      // 从选中列表中移除
      const selectedIndex = selectedIds.value.indexOf(documentId)
      if (selectedIndex !== -1) {
        selectedIds.value.splice(selectedIndex, 1)
      }
      
      // 清理缓存
      cache.value.clear()
      
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除文档失败'
      console.error('Failed to delete document:', err)
      return false
    }
  }
  
  /**
   * 批量删除文档
   */
  async function deleteDocuments(documentIds: string[]): Promise<boolean> {
    try {
      await documentService.deleteDocuments(documentIds)
      
      // 从列表中移除
      documents.value = documents.value.filter(doc => !documentIds.includes(doc.id))
      total.value -= documentIds.length
      
      // 从选中列表中移除
      selectedIds.value = selectedIds.value.filter(id => !documentIds.includes(id))
      
      // 清理缓存
      cache.value.clear()
      
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '批量删除文档失败'
      console.error('Failed to delete documents:', err)
      return false
    }
  }
  
  /**
   * 更新文档标签
   */
  async function updateDocumentTags(documentId: string, tags: string[]): Promise<boolean> {
    try {
      const updatedDocument = await documentService.updateDocumentTags(documentId, tags)
      
      // 更新本地数据
      const index = documents.value.findIndex(doc => doc.id === documentId)
      if (index !== -1) {
        documents.value[index] = updatedDocument
      }
      
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新文档标签失败'
      console.error('Failed to update document tags:', err)
      return false
    }
  }
  
  /**
   * 搜索文档内容
   */
  async function searchDocuments(query: string, options: {
    filterTags?: string[]
    topK?: number
  } = {}): Promise<Document[]> {
    try {
      const results = await documentService.searchDocuments({
        query,
        ...options
      })
      
      // 将搜索结果转换为文档列表
      // 这里需要根据实际API返回格式调整
      return results.map(result => ({
        id: result.metadata?.chunkId || '',
        filename: result.source,
        fileType: 'pdf', // 需要根据实际文件类型确定
        fileSize: 0,
        uploadTime: new Date().toISOString(),
        status: 'Completed',
        tags: result.tags,
        metadata: {
          pages: result.metadata?.page,
          author: '',
          creationDate: '',
          lastModified: ''
        }
      }))
    } catch (err) {
      error.value = err instanceof Error ? err.message : '搜索文档失败'
      console.error('Failed to search documents:', err)
      return []
    }
  }
  
  /**
   * 下载文档
   */
  async function downloadDocument(documentId: string, filename?: string): Promise<boolean> {
    try {
      await documentService.downloadDocument(documentId, filename)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '下载文档失败'
      console.error('Failed to download document:', err)
      return false
    }
  }
  
  /**
   * 预览文档
   */
  async function previewDocument(documentId: string, page?: number): Promise<string | null> {
    try {
      return await documentService.previewDocument(documentId, page)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '预览文档失败'
      console.error('Failed to preview document:', err)
      return null
    }
  }
  
  /**
   * 获取文档统计信息
   */
  async function getDocumentStats(): Promise<{
    total: number
    byType: Record<string, number>
    byStatus: Record<string, number>
    byTag: Record<string, number>
    recentUploads: number
  }> {
    try {
      return await documentService.getDocumentStats()
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取文档统计失败'
      console.error('Failed to get document stats:', err)
      return {
        total: 0,
        byType: {},
        byStatus: {},
        byTag: {},
        recentUploads: 0
      }
    }
  }
  
  /**
   * 获取相关文档
   */
  async function getRelatedDocuments(documentId: string, limit: number = 5): Promise<Document[]> {
    try {
      return await documentService.getRelatedDocuments(documentId, limit)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取相关文档失败'
      console.error('Failed to get related documents:', err)
      return []
    }
  }
  
  /**
   * 批量更新文档状态
   */
  async function batchUpdateStatus(documentIds: string[], status: string): Promise<boolean> {
    try {
      // 这里应该调用实际的批量更新API
      // 目前只是更新本地状态
      
      // 更新本地数据
      documents.value.forEach(doc => {
        if (documentIds.includes(doc.id)) {
          doc.status = status as any
        }
      })
      
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '批量更新状态失败'
      console.error('Failed to batch update status:', err)
      return false
    }
  }
  
  /**
   * 批量更新文档标签
   */
  async function batchUpdateTags(
    documentIds: string[], 
    tags: string[], 
    operation: 'add' | 'remove' | 'replace' = 'add'
  ): Promise<boolean> {
    try {
      await documentService.batchUpdateTags(documentIds, tags, operation)
      
      // 更新本地数据
      documents.value.forEach(doc => {
        if (documentIds.includes(doc.id)) {
          if (operation === 'add') {
            doc.tags = [...new Set([...doc.tags, ...tags])]
          } else if (operation === 'remove') {
            doc.tags = doc.tags.filter(tag => !tags.includes(tag))
          } else if (operation === 'replace') {
            doc.tags = tags
          }
        }
      })
      
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '批量更新标签失败'
      console.error('Failed to batch update tags:', err)
      return false
    }
  }
  
  /**
   * 选择/取消选择文档
   */
  function toggleSelection(documentId: string): void {
    const index = selectedIds.value.indexOf(documentId)
    if (index === -1) {
      selectedIds.value.push(documentId)
    } else {
      selectedIds.value.splice(index, 1)
    }
  }
  
  /**
   * 全选/取消全选
   */
  function toggleAllSelection(): void {
    if (selectedIds.value.length === documents.value.length) {
      selectedIds.value = []
    } else {
      selectedIds.value = documents.value.map(doc => doc.id)
    }
  }
  
  /**
   * 清理缓存
   */
  function cleanupCache(): void {
    const now = Date.now()
    for (const [key, value] of cache.value.entries()) {
      if (now - value.timestamp > APP_CONFIG.CACHE_CONFIG.DOCUMENT_LIST) {
        cache.value.delete(key)
      }
    }
  }
  
  /**
   * 重置状态
   */
  function reset(): void {
    documents.value = []
    total.value = 0
    currentPage.value = 1
    pageSize.value = 20
    loading.value = false
    error.value = null
    selectedIds.value = []
    query.value = {}
    cache.value.clear()
    lastFetchTime.value = 0
  }
  
  return {
    // 状态
    documents,
    total,
    currentPage,
    pageSize,
    loading,
    error,
    selectedIds,
    query,
    
    // 计算属性
    totalPages,
    hasMore,
    isCacheValid,
    selectedDocuments,
    documentsByStatus,
    documentsByType,
    
    // 方法
    fetchDocuments,
    fetchDocument,
    deleteDocument,
    deleteDocuments,
    updateDocumentTags,
    searchDocuments,
    downloadDocument,
    previewDocument,
    getDocumentStats,
    getRelatedDocuments,
    batchUpdateStatus,
    batchUpdateTags,
    toggleSelection,
    toggleAllSelection,
    reset
  }
})