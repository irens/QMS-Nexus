/**
 * Upload组件单元测试
 * 测试文件上传功能的核心逻辑
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import Upload from '../Upload.vue'
import { useUploadStore } from '@/stores/upload'
import { uploadService } from '@/services/upload'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn(() => Promise.resolve())
  }
}))

// Mock uploadService
vi.mock('@/services/upload', () => ({
  uploadService: {
    uploadFile: vi.fn(),
    batchUploadFiles: vi.fn(),
    getSupportedFileTypes: vi.fn(() => [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]),
    validateFile: vi.fn((file: File) => {
      const maxSize = 50 * 1024 * 1024
      if (file.size > maxSize) {
        return { valid: false, error: '文件大小不能超过50MB' }
      }
      const supportedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      ]
      if (!supportedTypes.includes(file.type)) {
        return { valid: false, error: '不支持的文件类型' }
      }
      return { valid: true }
    })
  }
}))

describe('Upload.vue', () => {
  let wrapper: VueWrapper<any>
  let uploadStore: ReturnType<typeof useUploadStore>

  beforeEach(() => {
    // 创建新的 Pinia 实例
    const pinia = createPinia()
    setActivePinia(pinia)
    uploadStore = useUploadStore()
    
    // 清理所有 mocks
    vi.clearAllMocks()
    
    // 挂载组件
    wrapper = mount(Upload, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-icon': true,
          'el-button': true,
          'el-upload': true,
          'el-progress': {
            template: '<div class="el-progress" :percentage="percentage">{{ percentage }}%</div>'
          }
        }
      }
    })
  })

  afterEach(() => {
    wrapper.unmount()
  })

  // ========================================
  // 1. 组件渲染测试
  // ========================================
  
  describe('组件渲染', () => {
    it('应该正确渲染上传区域', () => {
      expect(wrapper.find('.upload-dropzone').exists()).toBe(true)
      expect(wrapper.text()).toContain('拖拽文件到此处上传')
      expect(wrapper.text()).toContain('支持 PDF、DOC、DOCX、XLS、XLSX、PPT、PPTX')
      expect(wrapper.text()).toContain('单个文件不超过 50MB')
    })

    it('应该隐藏上传控制按钮当没有文件时', () => {
      const controls = wrapper.find('.upload-controls')
      expect(controls.isVisible()).toBe(false)
    })

    it('应该显示上传控制按钮当有文件时', async () => {
      const testFile = new File(['test'], 'test.pdf', { type: 'application/pdf' })
      uploadStore.addFile(testFile)
      await wrapper.vm.$nextTick()
      
      const controls = wrapper.find('.upload-controls')
      expect(controls.isVisible()).toBe(true)
    })
  })

  // ========================================
  // 2. 文件选择测试
  // ========================================
  
  describe('文件选择功能', () => {
    it('应该正确处理文件选择事件', async () => {
      const fileInput = wrapper.find('input[type="file"]')
      const testFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      
      // 模拟文件选择
      Object.defineProperty(fileInput.element, 'files', {
        value: [testFile],
        writable: false
      })
      
      await fileInput.trigger('change')
      await wrapper.vm.$nextTick()
      
      expect(uploadStore.uploadQueue).toHaveLength(1)
      expect(uploadStore.uploadQueue[0].file.name).toBe('test.pdf')
    })

    it('应该验证文件类型', async () => {
      const invalidFile = new File(['test'], 'test.exe', { type: 'application/x-msdownload' })
      
      uploadStore.addFile(invalidFile)
      await wrapper.vm.$nextTick()
      
      expect(ElMessage.error).toHaveBeenCalledWith('不支持的文件类型')
      expect(uploadStore.uploadQueue).toHaveLength(0)
    })

    it('应该验证文件大小', async () => {
      const largeFile = new File(['test'], 'large.pdf', { type: 'application/pdf' })
      Object.defineProperty(largeFile, 'size', { value: 60 * 1024 * 1024 }) // 60MB
      
      uploadStore.addFile(largeFile)
      await wrapper.vm.$nextTick()
      
      expect(ElMessage.error).toHaveBeenCalledWith('文件大小不能超过50MB')
      expect(uploadStore.uploadQueue).toHaveLength(0)
    })

    it('应该接受有效的PDF文件', async () => {
      const validFile = new File(['test'], 'document.pdf', { type: 'application/pdf' })
      Object.defineProperty(validFile, 'size', { value: 10 * 1024 * 1024 }) // 10MB
      
      uploadStore.addFile(validFile)
      await wrapper.vm.$nextTick()
      
      expect(uploadStore.uploadQueue).toHaveLength(1)
      expect(uploadStore.uploadQueue[0].file.name).toBe('document.pdf')
    })
  })

  // ========================================
  // 3. 拖拽上传测试
  // ========================================
  
  describe('拖拽上传功能', () => {
    it('应该响应拖拽进入事件', async () => {
      const dropzone = wrapper.find('.upload-dropzone')
      
      await dropzone.trigger('dragover', {
        dataTransfer: { files: [] }
      })
      await wrapper.vm.$nextTick()
      
      expect(dropzone.classes()).toContain('is-dragover')
    })

    it('应该响应拖拽离开事件', async () => {
      const dropzone = wrapper.find('.upload-dropzone')
      
      await dropzone.trigger('dragover')
      await dropzone.trigger('dragleave')
      await wrapper.vm.$nextTick()
      
      expect(dropzone.classes()).not.toContain('is-dragover')
    })

    it('应该处理拖拽上传文件', async () => {
      const dropzone = wrapper.find('.upload-dropzone')
      const testFile = new File(['test'], 'drop.pdf', { type: 'application/pdf' })
      
      await dropzone.trigger('drop', {
        dataTransfer: { files: [testFile] }
      })
      await wrapper.vm.$nextTick()
      
      expect(uploadStore.uploadQueue).toHaveLength(1)
      expect(uploadStore.uploadQueue[0].file.name).toBe('drop.pdf')
    })
  })

  // ========================================
  // 4. 上传功能测试
  // ========================================
  
  describe('上传功能', () => {
    beforeEach(() => {
      // 添加测试文件
      const testFile = new File(['test'], 'upload.pdf', { type: 'application/pdf' })
      uploadStore.addFile(testFile)
    })

    it('应该调用uploadService.uploadFile', async () => {
      const mockResponse = {
        id: '123',
        name: 'upload.pdf',
        status: 'completed',
        url: 'http://example.com/upload.pdf'
      }
      
      vi.mocked(uploadService.uploadFile).mockResolvedValue(mockResponse)
      
      await wrapper.vm.startUpload()
      await wrapper.vm.$nextTick()
      
      expect(uploadService.uploadFile).toHaveBeenCalled()
      expect(uploadStore.uploadQueue[0].status).toBe('completed')
    })

    it('应该处理上传错误', async () => {
      vi.mocked(uploadService.uploadFile).mockRejectedValue(
        new Error('Upload failed')
      )
      
      await wrapper.vm.startUpload()
      await wrapper.vm.$nextTick()
      
      expect(uploadService.uploadFile).toHaveBeenCalled()
      expect(uploadStore.uploadQueue[0].status).toBe('error')
      expect(uploadStore.uploadQueue[0].error).toBe('Upload failed')
      expect(ElMessage.error).toHaveBeenCalledWith('上传失败')
    })

    it('应该显示上传进度', async () => {
      const mockResponse = {
        id: '123',
        name: 'upload.pdf',
        status: 'completed'
      }
      
      vi.mocked(uploadService.uploadFile).mockImplementation(
        (file, onProgress) => {
          // 模拟进度更新
          if (onProgress) {
            onProgress(25)
            onProgress(50)
            onProgress(75)
            onProgress(100)
          }
          return Promise.resolve(mockResponse)
        }
      )
      
      await wrapper.vm.startUpload()
      
      expect(uploadStore.uploadQueue[0].progress).toBe(100)
    })

    it('应该在所有文件上传完成后显示成功消息', async () => {
      vi.mocked(uploadService.uploadFile).mockResolvedValue({
        id: '123',
        name: 'upload.pdf',
        status: 'completed'
      })
      
      await wrapper.vm.startUpload()
      await wrapper.vm.$nextTick()
      
      expect(ElMessage.success).toHaveBeenCalledWith(
        '成功上传 1 个文件'
      )
    })
  })

  // ========================================
  // 5. 批量上传测试
  // ========================================
  
  describe('批量上传', () => {
    it('应该同时上传多个文件', async () => {
      const files = [
        new File(['test1'], 'file1.pdf', { type: 'application/pdf' }),
        new File(['test2'], 'file2.pdf', { type: 'application/pdf' }),
        new File(['test3'], 'file3.pdf', { type: 'application/pdf' })
      ]
      
      files.forEach(file => uploadStore.addFile(file))
      
      vi.mocked(uploadService.uploadFile).mockImplementation(
        (file) => Promise.resolve({
          id: Math.random().toString(),
          name: file.name,
          status: 'completed'
        })
      )
      
      await wrapper.vm.startUpload()
      
      expect(uploadService.uploadFile).toHaveBeenCalledTimes(3)
      expect(uploadStore.completedFiles).toHaveLength(3)
    })

    it('应该控制并发上传数量', async () => {
      uploadStore.setMaxConcurrentUploads(2)
      
      const files = [
        new File(['test1'], 'file1.pdf', { type: 'application/pdf' }),
        new File(['test2'], 'file2.pdf', { type: 'application/pdf' }),
        new File(['test3'], 'file3.pdf', { type: 'application/pdf' })
      ]
      
      files.forEach(file => uploadStore.addFile(file))
      
      vi.mocked(uploadService.uploadFile).mockImplementation(
        () => new Promise(resolve => {
          setTimeout(() => {
            resolve({
              id: Math.random().toString(),
              name: 'file.pdf',
              status: 'completed'
            })
          }, 100)
        })
      )
      
      await wrapper.vm.startUpload()
      
      // 验证并发控制
      expect(uploadStore.currentUploads).toBeLessThanOrEqual(2)
    })
  })

  // ========================================
  // 6. 错误处理测试
  // ========================================
  
  describe('错误处理', () => {
    beforeEach(() => {
      const testFile = new File(['test'], 'error.pdf', { type: 'application/pdf' })
      uploadStore.addFile(testFile)
    })

    it('应该处理网络错误', async () => {
      vi.mocked(uploadService.uploadFile).mockRejectedValue(
        new Error('Network error')
      )
      
      await wrapper.vm.startUpload()
      await wrapper.vm.$nextTick()
      
      expect(uploadStore.uploadQueue[0].status).toBe('error')
      expect(uploadStore.uploadQueue[0].error).toBe('Network error')
    })

    it('应该处理超时错误', async () => {
      vi.mocked(uploadService.uploadFile).mockRejectedValue({
        code: 'ECONNABORTED',
        message: 'timeout'
      })
      
      await wrapper.vm.startUpload()
      await wrapper.vm.$nextTick()
      
      expect(ElMessage.error).toHaveBeenCalledWith('上传超时，请检查网络连接')
    })

    it('应该处理服务器错误', async () => {
      vi.mocked(uploadService.uploadFile).mockRejectedValue({
        response: { status: 500, data: { message: 'Server error' } }
      })
      
      await wrapper.vm.startUpload()
      await wrapper.vm.$nextTick()
      
      expect(ElMessage.error).toHaveBeenCalled()
    })

    it('应该支持重试失败的上传', async () => {
      vi.mocked(uploadService.uploadFile)
        .mockRejectedValueOnce(new Error('First attempt failed'))
        .mockResolvedValueOnce({
          id: '123',
          name: 'error.pdf',
          status: 'completed'
        })
      
      // 第一次上传失败
      await wrapper.vm.startUpload()
      expect(uploadStore.uploadQueue[0].status).toBe('error')
      
      // 重置状态
      uploadStore.uploadQueue[0].status = 'pending'
      uploadStore.uploadQueue[0].error = undefined
      
      // 重试
      await wrapper.vm.startUpload()
      expect(uploadStore.uploadQueue[0].status).toBe('completed')
    })
  })

  // ========================================
  // 7. 文件管理测试
  // ========================================
  
  describe('文件管理', () => {
    beforeEach(() => {
      const files = [
        new File(['test1'], 'file1.pdf', { type: 'application/pdf' }),
        new File(['test2'], 'file2.pdf', { type: 'application/pdf' })
      ]
      files.forEach(file => uploadStore.addFile(file))
    })

    it('应该正确移除文件', async () => {
      const fileId = uploadStore.uploadQueue[0].id
      
      uploadStore.removeFile(fileId)
      await wrapper.vm.$nextTick()
      
      expect(uploadStore.uploadQueue).toHaveLength(1)
      expect(uploadStore.uploadQueue[0].id).not.toBe(fileId)
    })

    it('应该清空所有文件', async () => {
      // Mock确认对话框
      vi.mocked(ElMessageBox.confirm).mockResolvedValue(undefined)
      
      await wrapper.vm.clearAllFiles()
      await wrapper.vm.$nextTick()
      
      expect(ElMessageBox.confirm).toHaveBeenCalled()
      expect(uploadStore.uploadQueue).toHaveLength(0)
    })

    it('应该取消清空操作', async () => {
      // Mock取消对话框
      vi.mocked(ElMessageBox.confirm).mockRejectedValue(new Error('cancel'))
      
      await wrapper.vm.clearAllFiles().catch(() => {})
      await wrapper.vm.$nextTick()
      
      expect(uploadStore.uploadQueue).toHaveLength(2)
    })
  })

  // ========================================
  // 8. 与Store集成测试
  // ========================================
  
  describe('Store集成', () => {
    it('应该正确从Store获取文件列表', async () => {
      const testFile = new File(['test'], 'store.pdf', { type: 'application/pdf' })
      uploadStore.addFile(testFile)
      
      await wrapper.vm.$nextTick()
      
      const fileItems = wrapper.findAll('.file-item')
      expect(fileItems.length).toBeGreaterThan(0)
    })

    it('应该正确显示上传进度', async () => {
      const testFile = new File(['test'], 'progress.pdf', { type: 'application/pdf' })
      uploadStore.addFile(testFile)
      
      // 模拟进度更新
      uploadStore.uploadQueue[0].progress = 50
      uploadStore.uploadQueue[0].status = 'uploading'
      
      await wrapper.vm.$nextTick()
      
      const progressBar = wrapper.find('.el-progress')
      expect(progressBar.exists()).toBe(true)
    })

    it('应该响应Store状态变化', async () => {
      const testFile = new File(['test'], 'reactive.pdf', { type: 'application/pdf' })
      uploadStore.addFile(testFile)
      
      await wrapper.vm.$nextTick()
      
      // 修改Store状态
      uploadStore.uploadQueue[0].status = 'completed'
      
      await wrapper.vm.$nextTick()
      
      const statusText = wrapper.find('.file-status')
      expect(statusText.exists()).toBe(true)
      expect(statusText.text()).toContain('已完成')
    })
  })

  // ========================================
  // 9. 辅助函数测试
  // ========================================
  
  describe('辅助函数', () => {
    it('应该正确格式化文件大小', () => {
      expect(wrapper.vm.formatFileSize(0)).toBe('0 B')
      expect(wrapper.vm.formatFileSize(1024)).toBe('1 KB')
      expect(wrapper.vm.formatFileSize(1024 * 1024)).toBe('1 MB')
      expect(wrapper.vm.formatFileSize(1024 * 1024 * 1024)).toBe('1 GB')
    })

    it('应该正确获取文件图标', () => {
      expect(wrapper.vm.getFileIcon('test.pdf')).toBe('file-pdf')
      expect(wrapper.vm.getFileIcon('test.docx')).toBe('file-word')
      expect(wrapper.vm.getFileIcon('test.xlsx')).toBe('file-excel')
      expect(wrapper.vm.getFileIcon('test.pptx')).toBe('file-ppt')
    })

    it('应该正确获取文件图标颜色', () => {
      expect(wrapper.vm.getFileColor('test.pdf')).toBe('#dc2626')
      expect(wrapper.vm.getFileColor('test.docx')).toBe('#2563eb')
      expect(wrapper.vm.getFileColor('test.xlsx')).toBe('#16a34a')
      expect(wrapper.vm.getFileColor('test.pptx')).toBe('#ea580c')
    })
  })
})
