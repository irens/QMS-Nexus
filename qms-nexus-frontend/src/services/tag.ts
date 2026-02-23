// 标签管理服务
import axios from 'axios'
import type { Tag, PaginatedResponse } from '@/types/api'

const API_BASE_URL = import.meta.env.PROD ? '/api/v1' : 'http://localhost:8000/api/v1'

export class TagService {
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
    
    const response = await axios.get<PaginatedResponse<Tag>>(`${API_BASE_URL}/tags?${params.toString()}`)
    return response.data
  }

  async createTag(
    name: string,
    description?: string,
    color?: string
  ): Promise<Tag> {
    const response = await axios.post<Tag>(`${API_BASE_URL}/tags`, {
      name,
      description,
      color
    })
    return response.data
  }

  async updateTag(
    tagId: string,
    updates: {
      name?: string
      description?: string
      color?: string
    }
  ): Promise<Tag> {
    const response = await axios.put<Tag>(`${API_BASE_URL}/tags/${tagId}`, updates)
    return response.data
  }

  async deleteTag(tagId: string): Promise<void> {
    await axios.delete(`${API_BASE_URL}/tags/${tagId}`)
  }

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
    const response = await axios.get(`${API_BASE_URL}/tags/stats`)
    return response.data
  }

  async getTaggedDocuments(
    tagId: string,
    page: number = 1,
    pageSize: number = 10
  ): Promise<PaginatedResponse<any>> {
    const params = new URLSearchParams({
      page: page.toString(),
      pageSize: pageSize.toString()
    })
    
    const response = await axios.get<PaginatedResponse<any>>(`${API_BASE_URL}/tags/${tagId}/documents?${params.toString()}`)
    return response.data
  }

  async addTagsToDocuments(
    documentIds: string[],
    tagIds: string[]
  ): Promise<void> {
    await axios.post(`${API_BASE_URL}/tags/batch/add`, {
      documentIds,
      tagIds
    })
  }

  async removeTagsFromDocuments(
    documentIds: string[],
    tagIds: string[]
  ): Promise<void> {
    await axios.post(`${API_BASE_URL}/tags/batch/remove`, {
      documentIds,
      tagIds
    })
  }

  async searchTags(query: string, limit: number = 10): Promise<Tag[]> {
    const response = await axios.get<Tag[]>(`${API_BASE_URL}/tags/search?query=${encodeURIComponent(query)}&limit=${limit}`)
    return response.data
  }
}

export const tagService = new TagService()
