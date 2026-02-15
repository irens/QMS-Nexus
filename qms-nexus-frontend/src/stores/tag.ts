// 标签状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Tag } from '@/types/api'
import { tagService } from '@/services/tag'

export interface TagState {
  tags: Tag[]
  loading: boolean
  error: string | null
  currentPage: number
  pageSize: number
  total: number
  searchQuery: string
}

export const useTagStore = defineStore('tag', () => {
  // 状态
  const tags = ref<Tag[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const searchQuery = ref('')

  // 计算属性
  const hasTags = computed(() => tags.value.length > 0)
  const isEmpty = computed(() => tags.value.length === 0 && !loading.value)
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

  /**
   * 获取标签列表
   */
  async function fetchTags(page: number = currentPage.value, search?: string): Promise<void> {
    loading.value = true
    error.value = null
    
    try {
      const response = await tagService.getTags(page, pageSize.value, search || searchQuery.value)
      tags.value = response.items
      total.value = response.total
      currentPage.value = page
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取标签列表失败'
      console.error('获取标签列表失败:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * 搜索标签
   */
  async function searchTags(query: string): Promise<void> {
    searchQuery.value = query
    await fetchTags(1, query)
  }

  /**
   * 创建标签
   */
  async function createTag(name: string, description?: string, color?: string): Promise<Tag | null> {
    loading.value = true
    error.value = null
    
    try {
      const newTag = await tagService.createTag(name, description, color)
      await fetchTags() // 重新获取列表
      return newTag
    } catch (err) {
      error.value = err instanceof Error ? err.message : '创建标签失败'
      console.error('创建标签失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新标签
   */
  async function updateTag(tagId: string, updates: Partial<Tag>): Promise<Tag | null> {
    loading.value = true
    error.value = null
    
    try {
      const updatedTag = await tagService.updateTag(tagId, updates)
      // 更新本地数据
      const index = tags.value.findIndex(tag => tag.id === tagId)
      if (index !== -1) {
        tags.value[index] = { ...tags.value[index], ...updatedTag }
      }
      return updatedTag
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新标签失败'
      console.error('更新标签失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除标签
   */
  async function deleteTag(tagId: string): Promise<boolean> {
    loading.value = true
    error.value = null
    
    try {
      await tagService.deleteTag(tagId)
      // 从本地数据中移除
      const index = tags.value.findIndex(tag => tag.id === tagId)
      if (index !== -1) {
        tags.value.splice(index, 1)
        total.value--
      }
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除标签失败'
      console.error('删除标签失败:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取标签统计
   */
  async function getTagStats(): Promise<{
    totalTags: number
    totalDocuments: number
    averageDocumentsPerTag: number
    mostUsedTags: Array<{
      tagId: string
      tagName: string
      documentCount: number
    }>
  } | null> {
    loading.value = true
    error.value = null
    
    try {
      const stats = await tagService.getTagStats()
      return stats
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取标签统计失败'
      console.error('获取标签统计失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取标签下的文档
   */
  async function getTaggedDocuments(tagId: string, page: number = 1): Promise<any> {
    loading.value = true
    error.value = null
    
    try {
      const response = await tagService.getTaggedDocuments(tagId, page, pageSize.value)
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取标签文档失败'
      console.error('获取标签文档失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 重置状态
   */
  function reset(): void {
    tags.value = []
    loading.value = false
    error.value = null
    currentPage.value = 1
    total.value = 0
    searchQuery.value = ''
  }

  return {
    // 状态
    tags,
    loading,
    error,
    currentPage,
    pageSize,
    total,
    searchQuery,
    
    // 计算属性
    hasTags,
    isEmpty,
    totalPages,
    
    // 方法
    fetchTags,
    searchTags,
    createTag,
    updateTag,
    deleteTag,
    getTagStats,
    getTaggedDocuments,
    reset
  }
})