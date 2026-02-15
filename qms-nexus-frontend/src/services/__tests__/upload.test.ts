import { describe, it, expect, vi, beforeEach } from 'vitest'
import { uploadService, UploadService } from '../upload'
import { apiClient } from '../api'

// Mock apiClient
vi.mock('../api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    upload: vi.fn().mockImplementation((url, file, onProgress) => {
      // 模拟进度回调
      if (onProgress) {
        onProgress(0)
        setTimeout(() => onProgress(50), 10)
        setTimeout(() => onProgress(100), 20)
      }
      return Promise.resolve({ id: 1, name: file.name, status: 'Completed' })
    })
  }
}))

describe('Upload Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('UploadService', () => {
    it('should be defined', () => {
      expect(uploadService).toBeDefined()
      expect(uploadService).toBeInstanceOf(UploadService)
    })

    describe('uploadFile', () => {
      it('uploads single file successfully', async () => {
        const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
        const mockResponse = {
          id: 1,
          name: 'test.pdf',
          type: 'pdf',
          size: 1024,
          url: 'http://example.com/files/test.pdf'
        }
        
        vi.mocked(apiClient.upload).mockResolvedValueOnce(mockResponse)

        const result = await uploadService.uploadFile(mockFile)
        
        expect(apiClient.upload).toHaveBeenCalledWith('/upload', mockFile, undefined)
        expect(result).toEqual(mockResponse)
      })

      it('uploads file with progress callback', async () => {
        const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
        const progressCallback = vi.fn()
        const mockResponse = { id: 1, name: 'test.pdf' }
        
        vi.mocked(apiClient.upload).mockResolvedValueOnce(mockResponse)

        const result = await uploadService.uploadFile(mockFile, progressCallback)
        
        expect(apiClient.upload).toHaveBeenCalledWith('/upload', mockFile, progressCallback)
        expect(result).toEqual(mockResponse)
      })
    })

    describe('getTaskStatus', () => {
      it('gets upload task status', async () => {
        const taskId = 'task-123'
        const mockTask = {
          id: taskId,
          status: 'Processing',
          progress: 50,
          fileName: 'test.pdf',
          fileSize: 1024
        }
        
        vi.mocked(apiClient.get).mockResolvedValueOnce(mockTask)

        const result = await uploadService.getTaskStatus(taskId)
        
        expect(apiClient.get).toHaveBeenCalledWith(`/tasks/${taskId}`)
        expect(result).toEqual(mockTask)
      })
    })

    describe('pollTaskStatus', () => {
      it('polls task status until completion', async () => {
        const taskId = 'task-123'
        const mockProgressTask = {
          id: taskId,
          status: 'Processing',
          progress: 50,
          fileName: 'test.pdf'
        }
        const mockCompletedTask = {
          id: taskId,
          status: 'Completed',
          progress: 100,
          fileName: 'test.pdf',
          result: { url: 'http://example.com/file.pdf' }
        }
        
        vi.mocked(apiClient.get)
          .mockResolvedValueOnce(mockProgressTask)
          .mockResolvedValueOnce(mockCompletedTask)

        const progressCallback = vi.fn()
        const result = await uploadService.pollTaskStatus(taskId, progressCallback, 5000)
        
        expect(apiClient.get).toHaveBeenCalledWith(`/tasks/${taskId}`)
        expect(progressCallback).toHaveBeenCalledWith(mockProgressTask)
        expect(progressCallback).toHaveBeenCalledWith(mockCompletedTask)
        expect(result).toEqual(mockCompletedTask)
      })

      it('rejects when task fails', async () => {
        const taskId = 'task-456'
        const mockFailedTask = {
          id: taskId,
          status: 'Failed',
          progress: 0,
          fileName: 'test.pdf',
          errorMessage: 'File processing failed'
        }
        
        vi.mocked(apiClient.get).mockResolvedValueOnce(mockFailedTask)

        await expect(uploadService.pollTaskStatus(taskId)).rejects.toThrow('File processing failed')
      })

      it('times out after specified duration', async () => {
        const taskId = 'task-789'
        const mockProcessingTask = {
          id: taskId,
          status: 'Processing',
          progress: 25,
          fileName: 'test.pdf'
        }
        
        vi.mocked(apiClient.get).mockResolvedValue(mockProcessingTask)

        await expect(uploadService.pollTaskStatus(taskId, undefined, 100)).rejects.toThrow('文件处理超时')
      })
    })

    describe('uploadFiles', () => {
      it('uploads multiple files successfully', async () => {
        const mockFiles = [
          new File(['content1'], 'file1.pdf', { type: 'application/pdf' }),
          new File(['content2'], 'file2.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
        ]
        
        const mockTasks = [
          { id: 1, name: 'file1.pdf', status: 'Completed' },
          { id: 2, name: 'file2.docx', status: 'Completed' }
        ]
        
        vi.mocked(apiClient.upload)
          .mockResolvedValueOnce(mockTasks[0])
          .mockResolvedValueOnce(mockTasks[1])

        const result = await uploadService.uploadFiles(mockFiles)
        
        expect(apiClient.upload).toHaveBeenCalledTimes(2)
        expect(result).toEqual(mockTasks)
      })

      it('uploads files with progress callback', async () => {
        const mockFiles = [
          new File(['content1'], 'file1.pdf', { type: 'application/pdf' }),
          new File(['content2'], 'file2.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
        ]
        
        const progressCallback = vi.fn()
        const mockTask = { id: 1, name: 'file.pdf', status: 'Completed' }
        
        vi.mocked(apiClient.upload).mockResolvedValue(mockTask)

        await uploadService.uploadFiles(mockFiles, progressCallback)
        
        expect(apiClient.upload).toHaveBeenCalledTimes(2)
        expect(progressCallback).toHaveBeenCalledTimes(2)
      })

      it('continues uploading even if one file fails', async () => {
        const mockFiles = [
          new File(['content1'], 'file1.pdf', { type: 'application/pdf' }),
          new File(['content2'], 'file2.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
        ]
        
        const mockTask1 = { id: 1, name: 'file1.pdf', status: 'Completed' }
        
        vi.mocked(apiClient.upload)
          .mockResolvedValueOnce(mockTask1)
          .mockRejectedValueOnce(new Error('Upload failed'))

        const result = await uploadService.uploadFiles(mockFiles)
        
        expect(apiClient.upload).toHaveBeenCalledTimes(2)
        expect(result).toEqual([mockTask1])
      })
    })

    describe('getSupportedFileTypes', () => {
      it('returns supported file types', () => {
        const supportedTypes = uploadService.getSupportedFileTypes()
        
        expect(Array.isArray(supportedTypes)).toBe(true)
        expect(supportedTypes.length).toBeGreaterThan(0)
        expect(supportedTypes).toContain('application/pdf')
        expect(supportedTypes).toContain('application/msword')
      })
    })

    describe('validateFile', () => {
      it('validates supported file type', () => {
        const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
        
        const result = uploadService.validateFile(validFile)
        
        expect(result.valid).toBe(true)
        expect(result.error).toBeUndefined()
      })

      it('rejects unsupported file type', () => {
        const invalidFile = new File(['content'], 'test.exe', { type: 'application/x-msdownload' })
        
        const result = uploadService.validateFile(invalidFile)
        
        expect(result.valid).toBe(false)
        expect(result.error).toBe('不支持的文件类型')
      })

      it('rejects oversized files', () => {
        const largeFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
        Object.defineProperty(largeFile, 'size', { value: 60 * 1024 * 1024 }) // 60MB
        
        const result = uploadService.validateFile(largeFile)
        
        expect(result.valid).toBe(false)
        expect(result.error).toBe('文件大小不能超过50MB')
      })

      it('accepts files within size limit', () => {
        const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
        Object.defineProperty(validFile, 'size', { value: 10 * 1024 * 1024 }) // 10MB
        
        const result = uploadService.validateFile(validFile)
        
        expect(result.valid).toBe(true)
        expect(result.error).toBeUndefined()
      })
    })
  })
})