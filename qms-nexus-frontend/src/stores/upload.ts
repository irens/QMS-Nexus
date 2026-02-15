// 上传状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import { uploadService } from '@/services/upload'

export interface UploadFile {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  progress: number
  taskId?: string
  error?: string
  currentStep?: string
  estimatedTime?: number
  retryCount?: number  // 重试次数
  result?: {
    documentId: string
    chunksCount: number
    parseTime: number
  }
}

export interface UploadState {
  uploadQueue: UploadFile[]
  completedUploads: UploadFile[]
  maxConcurrentUploads: number
  currentUploads: number
  autoRetry: boolean
  retryCount: number
}

export const useUploadStore = defineStore('upload', () => {
  // 状态
  const uploadQueue = ref<UploadFile[]>([])
  const completedUploads = ref<UploadFile[]>([])
  const maxConcurrentUploads = ref(3)
  const currentUploads = ref(0)
  const autoRetry = ref(true)
  const retryCount = ref(3)
  const isProcessingQueue = ref(false)  // 防止重复执行的锁
  
  // 计算属性
  const pendingUploads = computed(() => 
    uploadQueue.value.filter(file => file.status === 'pending')
  )
  
  const activeUploads = computed(() => 
    uploadQueue.value.filter(file => 
      file.status === 'uploading' || file.status === 'processing'
    )
  )
  
  const failedUploads = computed(() => 
    uploadQueue.value.filter(file => file.status === 'failed')
  )
  
  const completedUploadsList = computed(() => completedUploads.value)
  
  const uploadProgress = computed(() => {
    if (uploadQueue.value.length === 0) return 0
    
    const totalProgress = uploadQueue.value.reduce((sum, file) => {
      return sum + file.progress
    }, 0)
    
    return Math.round(totalProgress / uploadQueue.value.length)
  })
  
  const isUploading = computed(() => activeUploads.value.length > 0)
  const canUploadMore = computed(() => currentUploads.value < maxConcurrentUploads.value)
  
  // 方法
  /**
   * 添加文件到上传队列
   */
  function addFiles(files: File[]): void {
    const uploadFiles: UploadFile[] = files.map(file => ({
      id: generateFileId(),
      file,
      status: 'pending',
      progress: 0,
      retryCount: 0
    }))
    
    uploadQueue.value.push(...uploadFiles)
    
    // 不再自动开始上传，需要用户手动点击"开始上传"按钮
    // 避免重复上传问题
  }

  /**
   * 添加单个文件到上传队列（兼容API）
   */
  function addFile(file: File): void {
    addFiles([file])
  }
  
  /**
   * 处理上传队列
   */
  async function processUploadQueue(): Promise<void> {
    // 防止重复执行
    if (isProcessingQueue.value) return
    if (!canUploadMore.value) return
    
    isProcessingQueue.value = true
    
    try {
      const filesToUpload = pendingUploads.value.slice(0, maxConcurrentUploads.value - currentUploads.value)
      
      // 使用异步方式避免递归调用问题
      const uploadPromises = filesToUpload.map(file => uploadFile(file))
      await Promise.allSettled(uploadPromises)
    } finally {
      isProcessingQueue.value = false
      
      // 检查是否还有待上传文件，如果有则继续处理（但最多只递归一次，避免无限循环）
      if (pendingUploads.value.length > 0 && canUploadMore.value && !isProcessingQueue.value) {
        setTimeout(() => {
          processUploadQueue()
        }, 500)  // 增加延迟，避免过快循环
      }
    }
  }
  
  // 跟踪正在上传的文件ID，防止重复
  const uploadingFileIds = new Set<string>()
  
  /**
   * 上传单个文件
   */
  async function uploadFile(uploadFile: UploadFile): Promise<void> {
    // 多重检查防止重复上传
    if (uploadFile.status !== 'pending') return
    if (uploadingFileIds.has(uploadFile.id)) return
    
    uploadingFileIds.add(uploadFile.id)
    
    try {
      uploadFile.status = 'uploading'
      currentUploads.value++
      
      // 验证文件
      const validation = uploadService.validateFile(uploadFile.file)
      if (!validation.valid) {
        throw new Error(validation.error || '文件验证失败')
      }
      
      // 开始上传
      const task = await uploadService.uploadFile(
        uploadFile.file,
        (progress) => {
          uploadFile.progress = progress
        }
      )
      
      uploadFile.taskId = task.taskId
      uploadFile.status = 'processing'
      uploadFile.progress = 100
      uploadFile.currentStep = '正在解析文档...'
      
      // 轮询任务状态
      await pollTaskStatus(uploadFile)
      
    } catch (err) {
      uploadFile.status = 'failed'
      uploadFile.error = err instanceof Error ? err.message : '上传失败'
      currentUploads.value--
      uploadingFileIds.delete(uploadFile.id)
      
      // 自动重试 - 通过 retryUpload 处理，它会重置状态并触发 processUploadQueue
      // 但只在未达到最大重试次数时才重试
      const currentRetryCount = uploadFile.retryCount || 0
      if (autoRetry.value && currentRetryCount < retryCount.value) {
        retryUpload(uploadFile)
      }
    }
    // 不再在这里调用 processUploadQueue，由外层统一管理
  }
  
  /**
   * 轮询任务状态
   */
  async function pollTaskStatus(uploadFile: UploadFile): Promise<void> {
    if (!uploadFile.taskId) return
    
    try {
      const result = await uploadService.pollTaskStatus(
        uploadFile.taskId,
        (task) => {
          // 更新进度和状态
          if (task.status === 'Processing') {
            uploadFile.currentStep = task.currentStep
            uploadFile.progress = Math.max(90, task.progress) // 解析阶段90-100%
          }
        }
      )
      
      // 更新文件状态
      uploadFile.status = 'completed'
      uploadFile.result = result.result
      uploadFile.currentStep = '文档处理完成'
      
      // 移动到已完成列表
      moveToCompleted(uploadFile)
      
    } catch (err) {
      uploadFile.status = 'failed'
      uploadFile.error = err instanceof Error ? err.message : '处理失败'
      
      // 自动重试 - 检查重试次数
      const currentRetryCount = uploadFile.retryCount || 0
      if (autoRetry.value && currentRetryCount < retryCount.value) {
        retryUpload(uploadFile)
      }
    } finally {
      currentUploads.value--
      // 只有文件没有被重试（状态不是 pending）时才清理 ID
      if (uploadFile.status !== 'pending') {
        uploadingFileIds.delete(uploadFile.id)
      }
      // 不再在这里调用 processUploadQueue，由外层统一管理
    }
  }
  
  /**
   * 重试上传
   */
  async function retryUpload(uploadFile: UploadFile): Promise<void> {
    // 检查重试次数限制
    const currentRetryCount = uploadFile.retryCount || 0
    const maxRetries = retryCount.value
    
    if (currentRetryCount >= maxRetries) {
      uploadFile.status = 'failed'
      uploadFile.error = `上传失败，已达到最大重试次数 (${maxRetries})`
      return
    }
    
    // 重置状态并增加重试计数
    uploadFile.status = 'pending'
    uploadFile.progress = 0
    uploadFile.error = undefined
    uploadFile.currentStep = undefined
    uploadFile.result = undefined
    uploadFile.retryCount = currentRetryCount + 1
    
    // 延迟后重试 - 通过触发 processUploadQueue 来处理
    setTimeout(() => {
      // 只有当前没有在处理队列时才触发
      if (!isProcessingQueue.value) {
        processUploadQueue()
      }
    }, 2000)
  }
  
  /**
   * 移动到已完成列表
   */
  function moveToCompleted(uploadFile: UploadFile): void {
    // 从队列中移除
    const index = uploadQueue.value.findIndex(file => file.id === uploadFile.id)
    if (index !== -1) {
      uploadQueue.value.splice(index, 1)
    }
    
    // 添加到已完成列表
    completedUploads.value.unshift(uploadFile)
    
    // 限制已完成列表长度
    if (completedUploads.value.length > 50) {
      completedUploads.value = completedUploads.value.slice(0, 50)
    }
  }
  
  /**
   * 取消上传
   */
  function cancelUpload(fileId: string): void {
    const uploadFile = uploadQueue.value.find(file => file.id === fileId)
    if (!uploadFile) return
    
    // 只有在等待或上传状态才能取消
    if (uploadFile.status === 'pending' || uploadFile.status === 'uploading') {
      const wasUploading = uploadFile.status === 'uploading'
      
      uploadFile.status = 'failed'
      uploadFile.error = '用户取消上传'
      uploadFile.progress = 0
      
      if (wasUploading) {
        currentUploads.value--
      }
    }
  }
  
  /**
   * 重新上传失败文件
   */
  function retryFailedUploads(): void {
    failedUploads.value.forEach(file => {
      file.status = 'pending'
      file.error = undefined
      file.progress = 0
    })
    
    processUploadQueue()
  }

  /**
   * 移除文件（从上传队列或历史记录中删除）
   */
  function removeFile(fileId: string): void {
    // 从上传队列中移除
    const queueIndex = uploadQueue.value.findIndex(file => file.id === fileId)
    if (queueIndex !== -1) {
      const file = uploadQueue.value[queueIndex]
      // 如果文件正在上传，需要先取消
      if (file.status === 'uploading' || file.status === 'processing') {
        currentUploads.value--
      }
      uploadQueue.value.splice(queueIndex, 1)
      return
    }
    
    // 从已完成列表中移除
    const completedIndex = completedUploads.value.findIndex(file => file.id === fileId)
    if (completedIndex !== -1) {
      completedUploads.value.splice(completedIndex, 1)
    }
  }
  
  /**
   * 清除已完成的上传
   */
  function clearCompletedUploads(): void {
    completedUploads.value = []
  }
  
  /**
   * 清除失败的上传
   */
  function clearFailedUploads(): void {
    uploadQueue.value = uploadQueue.value.filter(file => file.status !== 'failed')
  }
  
  /**
   * 清除所有上传
   */
  function clearAllUploads(): void {
    uploadQueue.value = []
    completedUploads.value = []
    currentUploads.value = 0
  }
  
  /**
   * 设置最大并发上传数
   */
  function setMaxConcurrentUploads(max: number): void {
    maxConcurrentUploads.value = Math.max(1, Math.min(10, max))
  }
  
  /**
   * 设置自动重试
   */
  function setAutoRetry(enabled: boolean): void {
    autoRetry.value = enabled
  }
  
  /**
   * 生成文件ID
   */
  function generateFileId(): string {
    return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }
  
  return {
    // 状态
    uploadQueue,
    completedUploads,
    maxConcurrentUploads,
    currentUploads,
    autoRetry,
    retryCount,
    isProcessingQueue,
    
    // 计算属性
    pendingUploads,
    activeUploads,
    failedUploads,
    completedUploadsList,
    uploadProgress,
    isUploading,
    canUploadMore,
    
    // 方法
    addFiles,
    addFile,
    cancelUpload,
    removeFile,
    processUploadQueue,
    retryFailedUploads,
    clearCompletedUploads,
    clearFailedUploads,
    clearAllUploads,
    setMaxConcurrentUploads,
    setAutoRetry
  }
})