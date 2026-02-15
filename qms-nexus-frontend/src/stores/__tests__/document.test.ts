/**
 * Document Store单元测试
 * 测试文档状态管理、缓存机制、错误处理等
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDocumentStore } from '@/stores/document'
import { documentService } from '@/services/document'

// Mock documentService
vi.mock('@/services/document', () => ({
  documentService: {
    getDocuments: vi.fn(),
    getDocument: vi.fn(),
    deleteDocument: vi.fn(),
    updateDocument: vi.fn(),
    updateDocumentsStatus: vi.fn(),
    batchUpdateTags: vi.fn()
  }
}))

describe('Document Store', () => {
  let documentStore: ReturnType<typeof useDocumentStore>

  // 模拟文档数据
  const mockDocuments = [
    {
      id: '1',
      filename: 'ISO13485.pdf',
      fileType: 'pdf',
      fileSize: 5242880,
      uploadTime: '2024-01-15T10:00:00Z',
      status: 'Completed',
      tags: ['quality', 'standard'],
      metadata: { pages: 45, author: 'ISO' }
    },
    {
      id: '2',
      filename: '质量手册.docx',
      fileType: 'docx',
      fileSize: 2097152,
      uploadTime: '2024-01-14T09:30:00Z',
      status: 'Processing',
      tags: ['quality', 'medical'],
      metadata: { pages: 32, author: 'Admin' }
    },
    {
      id: '3',
      filename: '检验标准.xlsx',
      fileType: 'xlsx',
      fileSize: 1048576,
      uploadTime: '2024-01-13T14:20:00Z',
      status: 'Completed',
      tags: ['standard', 'training'],
      metadata: { pages: 15, author: 'Tester' }
    }
  ]

  beforeEach(() => {
    // 创建新的 Pinia 实例
    setActivePinia(createPinia())
    documentStore = useDocumentStore()
    
    // 清理所有 mocks
    vi.clearAllMocks()
    
    // 模拟 localStorage
    global.localStorage = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn()
    } as any
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ========================================
  // 1. 状态初始化测试
  // ========================================
  
  describe('状态初始化', () => {
    it('应该初始化正确的默认值', () => {
      expect(documentStore.documents).toEqual([])
      expect(documentStore.total).toBe(0)
      expect(documentStore.currentPage).toBe(1)
      expect(documentStore.pageSize).toBe(20)
      expect(documentStore.loading).toBe(false)
      expect(documentStore.error).toBeNull()
      expect(documentStore.selectedIds).toEqual([])
      expect(documentStore.query).toEqual({})
      expect(documentStore.lastFetchTime).toBe(0)
    })

    it('应该正确计算总页数', async () => {
      // 设置总记录数和每页大小
      documentStore.total = 100
      documentStore.pageSize = 10
      
      expect(documentStore.totalPages).toBe(10)
      
      // 测试不足一页的情况
      documentStore.total = 5
      expect(documentStore.totalPages).toBe(1)
      
      // 测试零记录的情况
      documentStore.total = 0
      expect(documentStore.totalPages).toBe(0)
    })

    it('应该判断是否有更多数据', () => {
      documentStore.currentPage = 1
      documentStore.total = 100
      documentStore.pageSize = 10
      
      expect(documentStore.hasMore).toBe(true)
      
      // 在最后一页
      documentStore.currentPage = 10
      expect(documentStore.hasMore).toBe(false)
    })
  })

  // ========================================
  // 2. 文档获取测试
  // ========================================
  
  describe('fetchDocuments - 文档获取', () => {
    it('应该正确获取文档列表', async () => {
      // Mock API响应
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: mockDocuments.length,
        page: 1,
        pageSize: 20
      })
      
      await documentStore.fetchDocuments({ page: 1, pageSize: 20 })
      
      // 验证状态更新
      expect(documentStore.documents).toEqual(mockDocuments)
      expect(documentStore.total).toBe(mockDocuments.length)
      expect(documentStore.currentPage).toBe(1)
      expect(documentStore.pageSize).toBe(20)
      expect(documentStore.loading).toBe(false)
      expect(documentStore.error).toBeNull()
      
      // 验证API调用
      expect(documentService.getDocuments).toHaveBeenCalledWith({
        page: 1,
        pageSize: 20
      })
    })

    it('应该应用搜索参数', async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: [mockDocuments[0]],
        total: 1,
        page: 1,
        pageSize: 20
      })
      
      await documentStore.fetchDocuments({ 
        page: 1, 
        pageSize: 20,
        search: 'ISO13485'
      })
      
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'ISO13485'
        })
      )
      
      // 验证query状态保存
      expect(documentStore.query.search).toBe('ISO13485')
    })

    it('应该应用类型筛选', async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments.filter(d => d.fileType === 'pdf'),
        total: 1,
        page: 1,
        pageSize: 20
      })
      
      await documentStore.fetchDocuments({ 
        page: 1, 
        pageSize: 20,
        fileType: ['pdf']
      })
      
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          fileType: ['pdf']
        })
      )
    })

    it('应该应用标签筛选', async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments.filter(d => d.tags.includes('quality')),
        total: 2,
        page: 1,
        pageSize: 20
      })
      
      await documentStore.fetchDocuments({ 
        page: 1, 
        pageSize: 20,
        tags: ['quality']
      })
      
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          tags: ['quality']
        })
      )
    })

    it('应该应用日期范围筛选', async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: 3,
        page: 1,
        pageSize: 20
      })
      
      const dateRange: [string, string] = ['2024-01-01', '2024-01-31']
      
      await documentStore.fetchDocuments({ 
        page: 1, 
        pageSize: 20,
        dateRange
      })
      
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          dateRange
        })
      )
    })

    it('应该应用排序参数', async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: 3,
        page: 1,
        pageSize: 20
      })
      
      await documentStore.fetchDocuments({ 
        page: 1, 
        pageSize: 20,
        sortBy: 'uploadTime',
        sortOrder: 'desc'
      })
      
      expect(documentService.getDocuments).toHaveBeenCalledWith(
        expect.objectContaining({
          sortBy: 'uploadTime',
          sortOrder: 'desc'
        })
      )
    })

    it('应该合并查询参数', async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: 3,
        page: 1,
        pageSize: 20
      })
      
      // 设置初始查询
      documentStore.query = {
        search: '质量',
        tags: ['quality']
      }
      
      // 调用时传入新参数
      await documentStore.fetchDocuments({ 
        page: 2,
        fileType: ['pdf']
      })
      
      // 验证参数合并
      expect(documentStore.query).toEqual({
        search: '质量',
        tags: ['quality'],
        page: 2,
        fileType: ['pdf']
      })
    })
  })

  // ========================================
  // 3. 文档操作测试
  // ========================================
  
  describe('文档操作', () => {
    beforeEach(async () => {
      // 预加载文档
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: mockDocuments.length,
        page: 1,
        pageSize: 20
      })
      
      await documentStore.fetchDocuments()
    })

    it('应该获取单个文档', async () => {
      const mockDocument = mockDocuments[0]
      vi.mocked(documentService.getDocument).mockResolvedValue(mockDocument)
      
      const result = await documentStore.fetchDocument('1')
      
      expect(documentService.getDocument).toHaveBeenCalledWith('1')
      expect(result).toEqual(mockDocument)
    })

    it('应该删除文档', async () => {
      vi.mocked(documentService.deleteDocument).mockResolvedValue(undefined)
      
      const initialCount = documentStore.documents.length
      
      await documentStore.deleteDocument('1')
      
      expect(documentService.deleteDocument).toHaveBeenCalledWith('1')
      expect(documentStore.documents.length).toBe(initialCount - 1)
      expect(documentStore.documents.find(d => d.id === '1')).toBeUndefined()
    })

    it('应该更新文档', async () => {
      const updateData = {
        filename: '更新后的文件名.pdf'
      }
      
      vi.mocked(documentService.updateDocument).mockResolvedValue({
        ...mockDocuments[0],
        ...updateData
      })
      
      await documentStore.updateDocument('1', updateData)
      
      expect(documentService.updateDocument).toHaveBeenCalledWith('1', updateData)
      expect(documentStore.documents[0].filename).toBe('更新后的文件名.pdf')
    })

    it('应该更新文档标签', async () => {
      const newTags = ['important', 'reviewed']
      
      vi.mocked(documentService.updateDocument).mockResolvedValue({
        ...mockDocuments[0],
        tags: newTags
      })
      
      await documentStore.updateDocumentTags('1', newTags)
      
      expect(documentStore.documents[0].tags).toEqual(newTags)
    })

    it('应该批量更新文档状态', async () => {
      const documentIds = ['1', '2']
      const newStatus = 'archived'
      
      vi.mocked(documentService.updateDocumentsStatus).mockResolvedValue(undefined)
      
      await documentStore.updateDocumentsStatus(documentIds, newStatus)
      
      expect(documentService.updateDocumentsStatus).toHaveBeenCalledWith(
        documentIds,
        newStatus
      )
      
      // 验证本地状态更新
      documentIds.forEach(id => {
        const doc = documentStore.documents.find(d => d.id === id)
        if (doc) {
          expect(doc.status).toBe(newStatus)
        }
      })
    })

    it('应该批量更新标签', async () => {
      const documentIds = ['1', '2']
      const tags = ['urgent', 'review']
      const operation = 'add'
      
      vi.mocked(documentService.batchUpdateTags).mockResolvedValue(undefined)
      
      await documentStore.batchUpdateTags(documentIds, tags, operation)
      
      expect(documentService.batchUpdateTags).toHaveBeenCalledWith(
        documentIds,
        tags,
        operation
      )
    })
  })

  // ========================================
  // 4. 缓存机制测试
  // ========================================
  
  describe('缓存机制', () => {
    it('应该缓存成功的请求', async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: mockDocuments.length,
        page: 1,
        pageSize: 20
      })
      
      const query = { page: 1, pageSize: 20 }
      
      // 第一次请求
      await documentStore.fetchDocuments(query)
      
      // 第二次相同请求应该使用缓存
      const startTime = Date.now()
      await documentStore.fetchDocuments(query)
      const endTime = Date.now()
      
      // 验证缓存使用（第二次应该很快）
      expect(endTime - startTime).toBeLessThan(100) // 应该很快，因为使用了缓存
      
      // 验证只调用了一次API
      expect(documentService.getDocuments).toHaveBeenCalledTimes(1)
    })

    it('应该验证缓存有效性', async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: mockDocuments.length,
        page: 1,
        pageSize: 20
      })
      
      const query = { page: 1, pageSize: 20 }
      
      // 第一次请求
      await documentStore.fetchDocuments(query)
      
      // 修改查询参数
      const differentQuery = { page: 2, pageSize: 20 }
      await documentStore.fetchDocuments(differentQuery)
      
      // 验证API被调用了两次（不同查询）
      expect(documentService.getDocuments).toHaveBeenCalledTimes(2)
    })

    it('应该清理过期缓存', async () => {
      // Mock Date.now() 来模拟时间流逝
      const originalNow = Date.now
      let currentTime = 1000000
      
      global.Date.now = vi.fn(() => currentTime)
      
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: mockDocuments.length,
        page: 1,
        pageSize: 20
      })
      
      const query = { page: 1, pageSize: 20 }
      
      // 第一次请求
      await documentStore.fetchDocuments(query)
      
      // 快进时间（超过缓存有效期）
      currentTime += 30 * 60 * 1000 // 30分钟
      
      // 再次请求（缓存应该已过期）
      await documentStore.fetchDocuments(query)
      
      // 验证API被调用了两次（缓存过期）
      expect(documentService.getDocuments).toHaveBeenCalledTimes(2)
      
      // 恢复Date.now
      global.Date.now = originalNow
    })

    it('应该检查缓存是否有效', () => {
      // 设置初始时间
      documentStore.lastFetchTime = Date.now()
      
      // 缓存应该有效
      expect(documentStore.isCacheValid).toBe(true)
      
      // 模拟时间流逝
      documentStore.lastFetchTime = Date.now() - 40 * 60 * 1000 // 40分钟前
      
      // 缓存应该无效
      expect(documentStore.isCacheValid).toBe(false)
    })
  })

  // ========================================
  // 5. 选择管理测试
  // ========================================
  
  describe('选择管理', () => {
    beforeEach(async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: mockDocuments.length,
        page: 1,
        pageSize: 20
      })
      
      await documentStore.fetchDocuments()
    })

    it('应该正确计算选中的文档', () => {
      documentStore.selectedIds = ['1', '3']
      
      expect(documentStore.selectedDocuments).toHaveLength(2)
      expect(documentStore.selectedDocuments[0].id).toBe('1')
      expect(documentStore.selectedDocuments[1].id).toBe('3')
    })

    it('应该按状态分组文档', () => {
      const byStatus = documentStore.documentsByStatus
      
      expect(byStatus.get('Completed')).toHaveLength(2)
      expect(byStatus.get('Processing')).toHaveLength(1)
    })

    it('应该按类型分组文档', () => {
      const byType = documentStore.documentsByType
      
      expect(byType.get('pdf')).toHaveLength(1)
      expect(byType.get('docx')).toHaveLength(1)
      expect(byType.get('xlsx')).toHaveLength(1)
    })
  })

  // ========================================
  // 6. 错误处理测试
  // ========================================
  
  describe('错误处理', () => {
    it('应该处理获取文档列表失败', async () => {
      const errorMessage = 'Failed to fetch documents'
      vi.mocked(documentService.getDocuments).mockRejectedValue(
        new Error(errorMessage)
      )
      
      await documentStore.fetchDocuments()
      
      expect(documentStore.error).toBe(errorMessage)
      expect(documentStore.loading).toBe(false)
      expect(documentStore.documents).toEqual([])
    })

    it('应该处理获取单个文档失败', async () => {
      const errorMessage = 'Document not found'
      vi.mocked(documentService.getDocument).mockRejectedValue(
        new Error(errorMessage)
      )
      
      const result = await documentStore.fetchDocument('999')
      
      expect(result).toBeNull()
      expect(documentStore.error).toBe(errorMessage)
    })

    it('应该处理删除文档失败', async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: mockDocuments.length,
        page: 1,
        pageSize: 20
      })
      
      await documentStore.fetchDocuments()
      
      const initialCount = documentStore.documents.length
      
      vi.mocked(documentService.deleteDocument).mockRejectedValue(
        new Error('Delete failed')
      )
      
      await documentStore.deleteDocument('1')
      
      expect(documentStore.error).toBe('Delete failed')
      // 验证文档未被删除
      expect(documentStore.documents.length).toBe(initialCount)
    })

    it('应该在错误后重置loading状态', async () => {
      vi.mocked(documentService.getDocuments).mockRejectedValue(
        new Error('Network error')
      )
      
      documentStore.loading = true
      await documentStore.fetchDocuments()
      
      expect(documentStore.loading).toBe(false)
    })

    it('应该处理无效的响应格式', async () => {
      // Mock无效的响应（没有items）
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        total: 0,
        page: 1,
        pageSize: 20
      } as any)
      
      await documentStore.fetchDocuments()
      
      // 应该设置错误
      expect(documentStore.error).toBeTruthy()
      expect(documentStore.documents).toEqual([])
    })
  })

  // ========================================
  // 7. 重置和清理测试
  // ========================================
  
  describe('重置和清理', () => {
    beforeEach(async () => {
      vi.mocked(documentService.getDocuments).mockResolvedValue({
        items: mockDocuments,
        total: mockDocuments.length,
        page: 1,
        pageSize: 20
      })
      
      await documentStore.fetchDocuments()
      documentStore.selectedIds = ['1', '2']
    })

    it('应该重置查询参数', () => {
      documentStore.query = {
        search: 'test',
        tags: ['quality'],
        fileType: ['pdf']
      }
      
      // 重置查询
      documentStore.query = {}
      
      expect(documentStore.query).toEqual({})
    })

    it('应该清理缓存', async () => {
      // 先填充缓存
      await documentStore.fetchDocuments({ page: 1, pageSize: 20 })
      
      // 添加一些过期缓存
      const oldCacheKey = JSON.stringify({ page: 999 })
      documentStore.cache.set(oldCacheKey, {
        data: [],
        timestamp: Date.now() - 2 * 60 * 60 * 1000 // 2小时前
      })
      
      // 清理缓存（移除过期的）
      const cacheSizeBefore = documentStore.cache.size
      
      // 模拟缓存清理逻辑
      const now = Date.now()
      const cacheTime = APP_CONFIG.CACHE_CONFIG.DOCUMENT_LIST
      
      for (const [key, value] of documentStore.cache.entries()) {
        if (now - value.timestamp > cacheTime) {
          documentStore.cache.delete(key)
        }
      }
      
      const cacheSizeAfter = documentStore.cache.size
      expect(cacheSizeAfter).toBeLessThanOrEqual(cacheSizeBefore)
    })

    it('应该清除所有状态', () => {
      // 设置一些状态
      documentStore.documents = mockDocuments
      documentStore.total = mockDocuments.length
      documentStore.selectedIds = ['1', '2', '3']
      documentStore.error = 'Some error'
      
      // 清除状态
      documentStore.documents = []
      documentStore.total = 0
      documentStore.selectedIds = []
      documentStore.error = null
      documentStore.query = {}
      
      // 验证状态已清除
      expect(documentStore.documents).toEqual([])
      expect(documentStore.total).toBe(0)
      expect(documentStore.selectedIds).toEqual([])
      expect(documentStore.error).toBeNull()
      expect(documentStore.query).toEqual({})
    })
  })
})
