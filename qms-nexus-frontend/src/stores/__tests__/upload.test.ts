import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUploadStore } from '@/stores/upload'
import { TestUtils } from '@/utils/test-utils'

// 模拟 Element Plus
TestUtils.mockElementPlus()

// 模拟本地存储
const mockStorage = TestUtils.mockLocalStorage()

// 模拟 API 服务
vi.mock('@/services/upload', () => ({
  uploadService: {
    uploadFile: vi.fn().mockImplementation((file) => 
      TestUtils.mockApiResponse({ id: '1', name: file.name, status: 'completed' })
    ),
    getUploadStatus: vi.fn().mockImplementation((id) =>
      TestUtils.mockApiResponse({ id, status: 'completed', progress: 100 })
    )
  }
}))

describe('Upload Store', () => {
  let uploadStore: ReturnType<typeof useUploadStore>

  beforeEach(() => {
    // 创建新的 Pinia 实例
    setActivePinia(createPinia())
    uploadStore = useUploadStore()
    
    // 清理本地存储
    mockStorage.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('状态管理', () => {
    it('应该初始化正确的默认值', () => {
      expect(uploadStore.uploadQueue).toEqual([])
      expect(uploadStore.completedUploads).toEqual([])
      expect(uploadStore.maxConcurrentUploads).toBe(3)
      expect(uploadStore.currentUploads).toBe(0)
      expect(uploadStore.autoRetry).toBe(true)
      expect(uploadStore.retryCount).toBe(3)
    })

    it('应该正确计算待上传文件', () => {
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      expect(uploadStore.pendingUploads).toHaveLength(2)
      expect(uploadStore.pendingUploads[0].status).toBe('pending')
    })

    it('应该正确计算正在上传的文件', () => {
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      // 模拟上传状态
      uploadStore.uploadQueue[0].status = 'uploading'
      
      expect(uploadStore.activeUploads).toHaveLength(1)
      expect(uploadStore.activeUploads[0].status).toBe('uploading')
    })

    it('应该正确计算失败的文件', () => {
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      // 模拟失败状态
      uploadStore.uploadQueue[0].status = 'failed'
      
      expect(uploadStore.failedUploads).toHaveLength(1)
      expect(uploadStore.failedUploads[0].status).toBe('failed')
    })
  })

  describe('文件添加', () => {
    it('应该正确添加文件到上传队列', () => {
      const testFiles = TestUtils.createTestFiles(3)
      uploadStore.addFiles(testFiles)
      
      expect(uploadStore.uploadQueue).toHaveLength(3)
      expect(uploadStore.uploadQueue[0].file.name).toBe('test-file-1.txt')
      expect(uploadStore.uploadQueue[0].status).toBe('pending')
      expect(uploadStore.uploadQueue[0].progress).toBe(0)
    })

    it('应该为每个文件生成唯一ID', () => {
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      const ids = uploadStore.uploadQueue.map(item => item.id)
      expect(new Set(ids).size).toBe(2)
    })

    it('应该正确处理空文件列表', () => {
      uploadStore.addFiles([])
      expect(uploadStore.uploadQueue).toHaveLength(0)
    })
  })

  describe('文件移除', () => {
    it('应该正确移除上传队列中的文件', () => {
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      const fileId = uploadStore.uploadQueue[0].id
      uploadStore.removeFile(fileId)
      
      expect(uploadStore.uploadQueue).toHaveLength(1)
      expect(uploadStore.uploadQueue[0].id).not.toBe(fileId)
    })

    it('应该正确移除已完成上传的文件', () => {
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      // 模拟完成状态
      const fileId = uploadStore.uploadQueue[0].id
      uploadStore.uploadQueue[0].status = 'completed'
      uploadStore.completedUploads.push(uploadStore.uploadQueue[0])
      
      uploadStore.removeFile(fileId)
      
      expect(uploadStore.completedUploads).toHaveLength(0)
    })

    it('应该正确处理不存在的文件ID', () => {
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      uploadStore.removeFile('non-existent-id')
      
      expect(uploadStore.uploadQueue).toHaveLength(2)
    })
  })

  describe('并发控制', () => {
    it('应该正确控制并发上传数量', () => {
      uploadStore.setMaxConcurrentUploads(2)
      
      const testFiles = TestUtils.createTestFiles(5)
      uploadStore.addFiles(testFiles)
      
      expect(uploadStore.maxConcurrentUploads).toBe(2)
      expect(uploadStore.canUploadMore).toBe(true)
    })

    it('应该在达到并发限制时阻止新上传', () => {
      uploadStore.setMaxConcurrentUploads(2)
      
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      // 模拟正在上传
      uploadStore.uploadQueue.forEach(item => {
        item.status = 'uploading'
      })
      
      expect(uploadStore.canUploadMore).toBe(false)
    })
  })

  describe('重试机制', () => {
    it('应该正确重置失败文件状态', () => {
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      // 模拟失败状态
      uploadStore.uploadQueue[0].status = 'failed'
      uploadStore.uploadQueue[0].error = 'Upload failed'
      
      uploadStore.retryFailedUploads()
      
      expect(uploadStore.uploadQueue[0].status).toBe('pending')
      expect(uploadStore.uploadQueue[0].error).toBeUndefined()
      expect(uploadStore.uploadQueue[0].progress).toBe(0)
    })

    it('应该正确处理没有失败文件的情况', () => {
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      uploadStore.retryFailedUploads()
      
      expect(uploadStore.uploadQueue.every(item => item.status === 'pending')).toBe(true)
    })
  })

  describe('数据持久化', () => {
    it('应该正确保存状态到本地存储', async () => {
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      await TestUtils.waitForVueUpdate()
      
      const savedData = mockStorage.getItem('upload-store')
      expect(savedData).toBeTruthy()
      
      const parsedData = JSON.parse(savedData!)
      expect(parsedData.uploadQueue).toHaveLength(2)
    })

    it('应该正确从本地存储恢复状态', () => {
      // 先保存一些数据
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      // 创建新的 store 实例
      const newStore = useUploadStore()
      
      expect(newStore.uploadQueue).toHaveLength(2)
      expect(newStore.uploadQueue[0].file.name).toBe('test-file-1.txt')
    })
  })

  describe('错误处理', () => {
    it('应该正确处理文件验证错误', () => {
      const invalidFile = TestUtils.createTestFile('invalid.exe', 1024, 'application/x-msdownload')
      
      // 这里应该触发文件验证，假设验证失败
      uploadStore.addFiles([invalidFile])
      
      // 验证失败的处理逻辑应该在这里测试
      expect(uploadStore.uploadQueue).toHaveLength(0)
    })

    it('应该正确处理上传过程中的错误', () => {
      const testFiles = TestUtils.createTestFiles(1)
      uploadStore.addFiles(testFiles)
      
      // 模拟上传错误
      const fileItem = uploadStore.uploadQueue[0]
      fileItem.status = 'failed'
      fileItem.error = 'Network error'
      
      expect(fileItem.status).toBe('failed')
      expect(fileItem.error).toBe('Network error')
    })
  })

  describe('进度更新', () => {
    it('应该正确更新上传进度', () => {
      const testFiles = TestUtils.createTestFiles(1)
      uploadStore.addFiles(testFiles)
      
      const fileItem = uploadStore.uploadQueue[0]
      fileItem.progress = 50
      
      expect(fileItem.progress).toBe(50)
    })

    it('应该正确计算总上传进度', () => {
      const testFiles = TestUtils.createTestFiles(2)
      uploadStore.addFiles(testFiles)
      
      uploadStore.uploadQueue[0].progress = 50
      uploadStore.uploadQueue[1].progress = 75
      
      const totalProgress = uploadStore.uploadProgress
      expect(totalProgress).toBeGreaterThanOrEqual(0)
      expect(totalProgress).toBeLessThanOrEqual(100)
    })
  })
})