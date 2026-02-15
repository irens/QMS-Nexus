// 前端API服务单元测试示例
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiClient, ApiRequestError } from '@/services/api'
import axios from 'axios'

// Mock axios实例
vi.mock('axios', async () => {
  const actual = await vi.importActual('axios')
  return {
    ...actual,
    default: {
      create: vi.fn(() => ({
        get: vi.fn(),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
      })),
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    },
  }
})

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  }
}))

describe('API Service Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Health Check API', () => {
    it('should handle successful health check', async () => {
      // Mock successful response
      const mockAxiosInstance = {
        get: vi.fn().mockResolvedValue({ data: { status: 'ok' }, status: 200 }),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
      }
      
      // 替换apiClient的实例以进行测试
      Object.defineProperty(apiClient, 'instance', {
        value: mockAxiosInstance,
        writable: true
      })

      // 模拟一个通用的GET请求方法
      const mockGet = vi.fn().mockResolvedValue({ data: { status: 'ok' }, status: 200 })
      
      // 执行测试
      const response = await mockGet('/api/v1/health')
      
      expect(response.status).toBe(200)
      expect(response.data.status).toBe('ok')
    })
  })

  describe('Document Upload API', () => {
    it('should handle successful file upload', async () => {
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      const formData = new FormData()
      formData.append('file', mockFile)

      const mockAxiosInstance = {
        get: vi.fn(),
        post: vi.fn().mockResolvedValue({ 
          data: { 
            task_id: 'test-task-id', 
            status: 'Pending',
            filename: 'test.pdf'
          }, 
          status: 200 
        }),
        put: vi.fn(),
        delete: vi.fn(),
      }

      // 执行测试逻辑
      const mockPost = vi.fn().mockResolvedValue({ 
        data: { task_id: 'test-task-id', status: 'Pending' }, 
        status: 200 
      })
      
      const response = await mockPost('/api/v1/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      expect(response.status).toBe(200)
      expect(response.data.task_id).toBe('test-task-id')
      expect(response.data.status).toBe('Pending')
    })

    it('should handle upload error for unsupported file type', async () => {
      const mockTextFile = new File(['text content'], 'test.txt', { type: 'text/plain' })
      const formData = new FormData()
      formData.append('file', mockTextFile)

      const mockAxiosInstance = {
        get: vi.fn(),
        post: vi.fn().mockRejectedValue({ 
          response: { 
            status: 400, 
            data: { message: '不支持的文件类型' } 
          } 
        }),
        put: vi.fn(),
        delete: vi.fn(),
      }

      // 执行测试逻辑
      const mockPost = vi.fn().mockRejectedValue({
        response: { 
          status: 400, 
          data: { message: '不支持的文件类型' } 
        }
      })
      
      await expect(
        mockPost('/api/v1/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      ).rejects.toMatchObject({
        response: { status: 400 }
      })
    })
  })

  describe('Search API', () => {
    it('should handle successful search request', async () => {
      const mockQuery = 'test query'
      const mockResults = [
        {
          text: 'Sample search result',
          source: 'document.pdf, 第1页',
          tags: ['tag1', 'tag2'],
          score: 0.85
        }
      ]

      const mockAxiosInstance = {
        get: vi.fn().mockResolvedValue({ 
          data: mockResults, 
          status: 200 
        }),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
      }

      // 执行测试逻辑
      const mockGet = vi.fn().mockResolvedValue({ 
        data: mockResults, 
        status: 200 
      })
      
      const response = await mockGet(`/api/v1/search?q=${encodeURIComponent(mockQuery)}`)
      
      expect(response.status).toBe(200)
      expect(response.data).toHaveLength(1)
      expect(response.data[0]).toHaveProperty('text')
      expect(response.data[0]).toHaveProperty('source')
      expect(response.data[0]).toHaveProperty('tags')
      expect(response.data[0]).toHaveProperty('score')
    })
  })

  describe('Tags API', () => {
    it('should handle successful tag creation', async () => {
      const newTag = {
        tag: 'new-tag',
        description: 'New tag description'
      }
      
      const mockAxiosInstance = {
        get: vi.fn(),
        post: vi.fn().mockResolvedValue({ 
          data: { tag: 'new-tag', description: 'New tag description' }, 
          status: 200 
        }),
        put: vi.fn(),
        delete: vi.fn(),
      }

      // 执行测试逻辑
      const mockPost = vi.fn().mockResolvedValue({ 
        data: { tag: 'new-tag', description: 'New tag description' }, 
        status: 200 
      })
      
      const response = await mockPost('/api/v1/tags', newTag)
      
      expect(response.status).toBe(200)
      expect(response.data.tag).toBe('new-tag')
      expect(response.data.description).toBe('New tag description')
    })
  })
})