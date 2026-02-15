import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTagStore } from '@/stores/tag'
import { TestUtils } from '@/utils/test-utils'

// 模拟 Element Plus
TestUtils.mockElementPlus()

// 模拟 API 服务
vi.mock('@/services/tag', () => ({
  tagService: {
    getTags: vi.fn().mockImplementation((page, pageSize, search) =>
      TestUtils.mockApiResponse({
        items: [
          { id: '1', name: 'test-tag', color: 'blue', usageCount: 5, createdAt: '2024-01-01', updatedAt: '2024-01-01' }
        ],
        total: 1,
        page,
        pageSize
      })
    ),
    createTag: vi.fn().mockImplementation((name, description, color) =>
      TestUtils.mockApiResponse({
        id: '2',
        name,
        description,
        color,
        usageCount: 0,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01'
      })
    ),
    updateTag: vi.fn().mockImplementation((tagId, updates) =>
      TestUtils.mockApiResponse({
        id: tagId,
        ...updates,
        updatedAt: '2024-01-02'
      })
    ),
    deleteTag: vi.fn().mockImplementation(() => TestUtils.mockApiResponse({})),
    getTagStats: vi.fn().mockImplementation(() =>
      TestUtils.mockApiResponse({
        totalTags: 10,
        totalDocuments: 50,
        averageDocumentsPerTag: 5,
        mostUsedTags: [
          { tagId: '1', tagName: 'test-tag', documentCount: 10 }
        ]
      })
    )
  }
}))

describe('Tag Store', () => {
  let tagStore: ReturnType<typeof useTagStore>

  beforeEach(() => {
    // 创建新的 Pinia 实例
    setActivePinia(createPinia())
    tagStore = useTagStore()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('状态管理', () => {
    it('应该初始化正确的默认值', () => {
      expect(tagStore.tags).toEqual([])
      expect(tagStore.loading).toBe(false)
      expect(tagStore.error).toBe(null)
      expect(tagStore.currentPage).toBe(1)
      expect(tagStore.pageSize).toBe(20)
      expect(tagStore.total).toBe(0)
      expect(tagStore.searchQuery).toBe('')
    })

    it('应该正确计算是否有标签', () => {
      expect(tagStore.hasTags).toBe(false)
      
      // 添加标签
      tagStore.tags = [TestUtils.createMockTag()]
      expect(tagStore.hasTags).toBe(true)
    })

    it('应该正确计算是否为空', () => {
      expect(tagStore.isEmpty).toBe(true)
      
      // 添加标签
      tagStore.tags = [TestUtils.createMockTag()]
      expect(tagStore.isEmpty).toBe(false)
      
      // 设置加载状态
      tagStore.loading = true
      expect(tagStore.isEmpty).toBe(false)
    })

    it('应该正确计算总页数', () => {
      tagStore.total = 50
      tagStore.pageSize = 20
      expect(tagStore.totalPages).toBe(3)
      
      tagStore.total = 0
      expect(tagStore.totalPages).toBe(0)
    })
  })

  describe('获取标签列表', () => {
    it('应该成功获取标签列表', async () => {
      await tagStore.fetchTags()
      
      expect(tagStore.tags).toHaveLength(1)
      expect(tagStore.tags[0].name).toBe('test-tag')
      expect(tagStore.loading).toBe(false)
      expect(tagStore.error).toBe(null)
    })

    it('应该处理获取标签列表的错误', async () => {
      // 模拟 API 错误
      vi.mocked(tagService.getTags).mockRejectedValueOnce(new Error('Network error'))
      
      await tagStore.fetchTags()
      
      expect(tagStore.tags).toEqual([])
      expect(tagStore.error).toBe('Network error')
      expect(tagStore.loading).toBe(false)
    })

    it('应该支持搜索功能', async () => {
      await tagStore.searchTags('test')
      
      expect(tagStore.searchQuery).toBe('test')
      expect(tagStore.currentPage).toBe(1)
    })
  })

  describe('创建标签', () => {
    it('应该成功创建新标签', async () => {
      const newTag = await tagStore.createTag('new-tag', 'New tag description', 'green')
      
      expect(newTag).toBeTruthy()
      expect(newTag?.name).toBe('new-tag')
      expect(newTag?.description).toBe('New tag description')
      expect(newTag?.color).toBe('green')
      expect(tagStore.loading).toBe(false)
      expect(tagStore.error).toBe(null)
    })

    it('应该处理创建标签的错误', async () => {
      // 模拟 API 错误
      vi.mocked(tagService.createTag).mockRejectedValueOnce(new Error('Creation failed'))
      
      const newTag = await tagStore.createTag('error-tag')
      
      expect(newTag).toBe(null)
      expect(tagStore.error).toBe('Creation failed')
      expect(tagStore.loading).toBe(false)
    })
  })

  describe('更新标签', () => {
    it('应该成功更新标签', async () => {
      // 先添加一个标签
      tagStore.tags = [TestUtils.createMockTag()]
      const tagId = tagStore.tags[0].id
      
      const updatedTag = await tagStore.updateTag(tagId, {
        name: 'updated-tag',
        description: 'Updated description'
      })
      
      expect(updatedTag).toBeTruthy()
      expect(updatedTag?.name).toBe('updated-tag')
      expect(updatedTag?.description).toBe('Updated description')
      expect(tagStore.tags[0].name).toBe('updated-tag')
    })

    it('应该处理更新标签的错误', async () => {
      // 模拟 API 错误
      vi.mocked(tagService.updateTag).mockRejectedValueOnce(new Error('Update failed'))
      
      const updatedTag = await tagStore.updateTag('1', { name: 'error-tag' })
      
      expect(updatedTag).toBe(null)
      expect(tagStore.error).toBe('Update failed')
    })
  })

  describe('删除标签', () => {
    it('应该成功删除标签', async () => {
      // 先添加一个标签
      tagStore.tags = [TestUtils.createMockTag()]
      tagStore.total = 1
      const tagId = tagStore.tags[0].id
      
      const success = await tagStore.deleteTag(tagId)
      
      expect(success).toBe(true)
      expect(tagStore.tags).toHaveLength(0)
      expect(tagStore.total).toBe(0)
    })

    it('应该处理删除标签的错误', async () => {
      // 模拟 API 错误
      vi.mocked(tagService.deleteTag).mockRejectedValueOnce(new Error('Deletion failed'))
      
      const success = await tagStore.deleteTag('1')
      
      expect(success).toBe(false)
      expect(tagStore.error).toBe('Deletion failed')
    })
  })

  describe('获取标签统计', () => {
    it('应该成功获取标签统计信息', async () => {
      const stats = await tagStore.getTagStats()
      
      expect(stats).toBeTruthy()
      expect(stats?.totalTags).toBe(10)
      expect(stats?.totalDocuments).toBe(50)
      expect(stats?.averageDocumentsPerTag).toBe(5)
      expect(stats?.mostUsedTags).toHaveLength(1)
      expect(tagStore.loading).toBe(false)
      expect(tagStore.error).toBe(null)
    })

    it('应该处理获取标签统计的错误', async () => {
      // 模拟 API 错误
      vi.mocked(tagService.getTagStats).mockRejectedValueOnce(new Error('Stats failed'))
      
      const stats = await tagStore.getTagStats()
      
      expect(stats).toBe(null)
      expect(tagStore.error).toBe('Stats failed')
      expect(tagStore.loading).toBe(false)
    })
  })

  describe('状态重置', () => {
    it('应该正确重置所有状态', () => {
      // 设置一些状态
      tagStore.tags = [TestUtils.createMockTag()]
      tagStore.loading = true
      tagStore.error = 'Some error'
      tagStore.currentPage = 5
      tagStore.total = 10
      tagStore.searchQuery = 'search'
      
      tagStore.reset()
      
      expect(tagStore.tags).toEqual([])
      expect(tagStore.loading).toBe(false)
      expect(tagStore.error).toBe(null)
      expect(tagStore.currentPage).toBe(1)
      expect(tagStore.total).toBe(0)
      expect(tagStore.searchQuery).toBe('')
    })
  })
})