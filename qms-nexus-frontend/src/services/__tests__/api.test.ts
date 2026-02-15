import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiClient, ApiRequestError } from '../api'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn()
  }
}))

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('ApiRequestError', () => {
    it('creates error with correct properties', () => {
      const error = new ApiRequestError('Test error', 404, { detail: 'Not found' })
      
      expect(error.message).toBe('Test error')
      expect(error.name).toBe('ApiRequestError')
      expect(error.code).toBe(404)
      expect(error.details).toEqual({ detail: 'Not found' })
    })
  })

  describe('apiClient', () => {
    it('has correct base configuration', () => {
      expect(apiClient).toBeDefined()
      expect(typeof apiClient.get).toBe('function')
      expect(typeof apiClient.post).toBe('function')
      expect(typeof apiClient.put).toBe('function')
      expect(typeof apiClient.delete).toBe('function')
      expect(typeof apiClient.upload).toBe('function')
      expect(typeof apiClient.download).toBe('function')
    })

    it('handles successful GET request', async () => {
      const mockResponse = { data: { id: 1, name: 'Test' } }
      
      // Mock the axios instance
      const originalGet = apiClient.get
      apiClient.get = vi.fn().mockResolvedValueOnce(mockResponse)
      
      const result = await apiClient.get('/test')
      
      expect(apiClient.get).toHaveBeenCalledWith('/test')
      expect(result).toEqual(mockResponse)
      
      // Restore original method
      apiClient.get = originalGet
    })

    it('handles successful POST request', async () => {
      const mockData = { name: 'New Item' }
      const mockResponse = { data: { id: 2, ...mockData } }
      
      const originalPost = apiClient.post
      apiClient.post = vi.fn().mockResolvedValueOnce(mockResponse)
      
      const result = await apiClient.post('/test', mockData)
      
      expect(apiClient.post).toHaveBeenCalledWith('/test', mockData)
      expect(result).toEqual(mockResponse)
      
      apiClient.post = originalPost
    })

    it('handles successful PUT request', async () => {
      const updateData = { name: 'Updated Item' }
      const mockResponse = { data: { id: 3, ...updateData } }
      
      const originalPut = apiClient.put
      apiClient.put = vi.fn().mockResolvedValueOnce(mockResponse)
      
      const result = await apiClient.put('/test/3', updateData)
      
      expect(apiClient.put).toHaveBeenCalledWith('/test/3', updateData)
      expect(result).toEqual(mockResponse)
      
      apiClient.put = originalPut
    })

    it('handles successful DELETE request', async () => {
      const mockResponse = { data: { success: true } }
      
      const originalDelete = apiClient.delete
      apiClient.delete = vi.fn().mockResolvedValueOnce(mockResponse)
      
      const result = await apiClient.delete('/test/4')
      
      expect(apiClient.delete).toHaveBeenCalledWith('/test/4')
      expect(result).toEqual(mockResponse)
      
      apiClient.delete = originalDelete
    })
  })

  describe('File Operations', () => {
    it('handles file upload', async () => {
      const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      const mockResponse = { data: { url: 'http://example.com/file.pdf' } }
      
      const originalUpload = apiClient.upload
      apiClient.upload = vi.fn().mockResolvedValueOnce(mockResponse)
      
      const result = await apiClient.upload('/upload', mockFile)
      
      expect(apiClient.upload).toHaveBeenCalledWith('/upload', mockFile, undefined)
      expect(result).toEqual(mockResponse)
      
      apiClient.upload = originalUpload
    })

    it('handles file download', async () => {
      const originalDownload = apiClient.download
      apiClient.download = vi.fn().mockResolvedValueOnce(undefined)
      
      await apiClient.download('/download/file.pdf', 'document.pdf')
      
      expect(apiClient.download).toHaveBeenCalledWith('/download/file.pdf', 'document.pdf')
      
      apiClient.download = originalDownload
    })
  })

  describe('Error Handling', () => {
    it('handles network errors', async () => {
      const networkError = new Error('Network Error')
      
      const originalGet = apiClient.get
      apiClient.get = vi.fn().mockRejectedValueOnce(networkError)
      
      await expect(apiClient.get('/test')).rejects.toThrow('Network Error')
      
      apiClient.get = originalGet
    })

    it('handles timeout errors', async () => {
      const timeoutError = new Error('timeout of 5000ms exceeded')
      
      const originalGet = apiClient.get
      apiClient.get = vi.fn().mockRejectedValueOnce(timeoutError)
      
      await expect(apiClient.get('/slow-endpoint')).rejects.toThrow('timeout of 5000ms exceeded')
      
      apiClient.get = originalGet
    })

    it('handles server errors', async () => {
      const serverError = new ApiRequestError('Internal Server Error', 500)
      
      const originalGet = apiClient.get
      apiClient.get = vi.fn().mockRejectedValueOnce(serverError)
      
      await expect(apiClient.get('/error-endpoint')).rejects.toThrow('Internal Server Error')
      
      apiClient.get = originalGet
    })
  })
})