// 上传状态管理
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

import { uploadService } from '@/services/upload'

export interface UploadFile {
  id: string
  file: File
  status: 'Pending' | 'Uploading' | 'Processing' | 'Completed' | 'Failed'
  progress: number
  taskId?: string
  error?: string
  currentStep?: string
  estimatedTime?: number
  retryCount?: number
  completedAt?: string
  result?: {
    documentId: string
    chunksCount: number
    parseTime: number
  }
}

export interface UploadHistoryItem {
  id: string
  fileName: string
  fileSize: number
  fileType: string
  status: 'completed' | 'failed'
  completedAt: string
  taskId?: string
  error?: string
  result?: {
    documentId: string
    chunksCount: number
    parseTime: number
  }
}

const STORAGE_KEY = 'qms_upload_history'

function loadHistoryFromStorage(): UploadHistoryItem[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (data) {
      return JSON.parse(data)
    }
  } catch (e) {
    console.error('Failed to load upload history:', e)
  }
  return []
}

function saveHistoryToStorage(history: UploadHistoryItem[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history))
  } catch (e) {
    console.error('Failed to save upload history:', e)
  }
}

export const useUploadStore = defineStore('upload', () => {
  const uploadQueue = ref<UploadFile[]>([])
  const completedUploads = ref<UploadHistoryItem[]>(loadHistoryFromStorage())
  const maxConcurrentUploads = ref(3)
  const currentUploads = ref(0)
  const autoRetry = ref(true)
  const retryCount = ref(3)
  const isProcessingQueue = ref(false)
  
  watch(completedUploads, (newVal) => {
    saveHistoryToStorage(newVal)
  }, { deep: true })
  
  const pendingUploads = computed(() => 
    uploadQueue.value.filter(file => file.status === 'Pending')
  )
  
  const activeUploads = computed(() => 
    uploadQueue.value.filter(file => 
      file.status === 'Uploading' || file.status === 'Processing'
    )
  )
  
  const failedUploads = computed(() => 
    uploadQueue.value.filter(file => file.status === 'Failed')
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
  
  function addFiles(files: File[]): void {
    const uploadFiles: UploadFile[] = files.map(file => ({
      id: generateFileId(),
      file,
      status: 'Pending' as const,
      progress: 0,
      retryCount: 0
    }))
    
    uploadQueue.value.push(...uploadFiles)
  }

  function addFile(file: File): void {
    addFiles([file])
  }
  
  async function processUploadQueue(): Promise<void> {
    // 重置机制：如果长时间没有活动，重置处理状态
    if (isProcessingQueue.value) {
      console.log('[UploadStore] 上传队列正在处理中，跳过重复调用')
      return
    }
    if (!canUploadMore.value) {
      console.log('[UploadStore] 当前上传数量已达上限，等待完成')
      return
    }
    if (pendingUploads.value.length === 0) {
      console.log('[UploadStore] 没有待上传的文件')
      return
    }

    isProcessingQueue.value = true

    try {
      const filesToUpload = pendingUploads.value.slice(0, maxConcurrentUploads.value - currentUploads.value)
      console.log(`[UploadStore] 开始处理 ${filesToUpload.length} 个文件上传`)

      const uploadPromises = filesToUpload.map(file => uploadFile(file))
      await Promise.allSettled(uploadPromises)
    } finally {
      isProcessingQueue.value = false

      // 检查是否还有更多待上传文件
      if (pendingUploads.value.length > 0 && canUploadMore.value) {
        console.log(`[UploadStore] 还有 ${pendingUploads.value.length} 个文件待上传，继续处理`)
        setTimeout(() => {
          processUploadQueue()
        }, 500)
      }
    }
  }
  
  const uploadingFileIds = new Set<string>()
  
  async function uploadFile(uploadFileItem: UploadFile): Promise<void> {
    if (uploadFileItem.status !== 'Pending') return
    if (uploadingFileIds.has(uploadFileItem.id)) return
    
    uploadingFileIds.add(uploadFileItem.id)
    
    try {
      uploadFileItem.status = 'Uploading'
      currentUploads.value++
      
      const validation = uploadService.validateFile(uploadFileItem.file)
      if (!validation.valid) {
        throw new Error(validation.error || '文件验证失败')
      }
      
      const task = await uploadService.uploadFile(
        uploadFileItem.file,
        (progress) => {
          uploadFileItem.progress = progress
        }
      )
      
      uploadFileItem.taskId = task.taskId
      uploadFileItem.status = 'Processing'
      uploadFileItem.progress = 80  // 上传完成占80%，解析占20%
      uploadFileItem.currentStep = '正在解析文档...'
      
      await pollTaskStatus(uploadFileItem)
      
    } catch (err) {
      uploadFileItem.status = 'Failed'
      uploadFileItem.error = err instanceof Error ? err.message : '上传失败'
      currentUploads.value--
      uploadingFileIds.delete(uploadFileItem.id)
      
      const currentRetryCount = uploadFileItem.retryCount || 0
      if (autoRetry.value && currentRetryCount < retryCount.value) {
        retryUpload(uploadFileItem)
      }
    }
  }
  
  async function pollTaskStatus(uploadFileItem: UploadFile): Promise<void> {
    if (!uploadFileItem.taskId) return
    
    try {
      const result = await uploadService.pollTaskStatus(
        uploadFileItem.taskId,
        (task) => {
          if (task.status === 'Processing') {
            uploadFileItem.currentStep = task.currentStep
            // 解析阶段从80%到99%
            const parseProgress = task.progress || 0
            uploadFileItem.progress = 80 + Math.min(19, parseProgress * 0.19)
          }
        }
      )
      
      uploadFileItem.status = 'Completed'
      uploadFileItem.result = result.result
      uploadFileItem.currentStep = '文档处理完成'
      
      moveToCompleted(uploadFileItem)
      
    } catch (err) {
      uploadFileItem.status = 'Failed'
      uploadFileItem.error = err instanceof Error ? err.message : '处理失败'
      
      const currentRetryCount = uploadFileItem.retryCount || 0
      if (autoRetry.value && currentRetryCount < retryCount.value) {
        retryUpload(uploadFileItem)
      }
    } finally {
      currentUploads.value--
      if (uploadFileItem.status !== 'Pending') {
        uploadingFileIds.delete(uploadFileItem.id)
      }
    }
  }
  
  async function retryUpload(uploadFileItem: UploadFile): Promise<void> {
    const currentRetryCount = uploadFileItem.retryCount || 0
    const maxRetries = retryCount.value
    
    if (currentRetryCount >= maxRetries) {
      uploadFileItem.status = 'Failed'
      uploadFileItem.error = `上传失败，已达到最大重试次数 (${maxRetries})`
      return
    }
    
    uploadFileItem.status = 'Pending'
    uploadFileItem.progress = 0
    uploadFileItem.error = undefined
    uploadFileItem.currentStep = undefined
    uploadFileItem.result = undefined
    uploadFileItem.retryCount = currentRetryCount + 1
    
    setTimeout(() => {
      if (!isProcessingQueue.value) {
        processUploadQueue()
      }
    }, 2000)
  }
  
  function moveToCompleted(uploadFileItem: UploadFile): void {
    const completedAt = new Date().toISOString()
    
    const historyItem: UploadHistoryItem = {
      id: uploadFileItem.id,
      fileName: uploadFileItem.file.name,
      fileSize: uploadFileItem.file.size,
      fileType: uploadFileItem.file.type,
      status: 'completed',
      completedAt,
      taskId: uploadFileItem.taskId,
      result: uploadFileItem.result
    }
    
    const index = uploadQueue.value.findIndex(file => file.id === uploadFileItem.id)
    if (index !== -1) {
      uploadQueue.value.splice(index, 1)
    }
    
    completedUploads.value.unshift(historyItem)
    
    if (completedUploads.value.length > 50) {
      completedUploads.value = completedUploads.value.slice(0, 50)
    }
  }
  
  function cancelUpload(fileId: string): void {
    const uploadFileItem = uploadQueue.value.find(file => file.id === fileId)
    if (!uploadFileItem) return
    
    if (uploadFileItem.status === 'Pending' || uploadFileItem.status === 'Uploading') {
      const wasUploading = uploadFileItem.status === 'Uploading'
      
      uploadFileItem.status = 'Failed'
      uploadFileItem.error = '用户取消上传'
      uploadFileItem.progress = 0
      
      if (wasUploading) {
        currentUploads.value--
      }
    }
  }
  
  function retryFailedUploads(): void {
    failedUploads.value.forEach(file => {
      file.status = 'Pending'
      file.error = undefined
      file.progress = 0
    })
    
    processUploadQueue()
  }

  function removeFile(fileId: string): void {
    const queueIndex = uploadQueue.value.findIndex(file => file.id === fileId)
    if (queueIndex !== -1) {
      const file = uploadQueue.value[queueIndex]
      if (file.status === 'uploading' || file.status === 'processing') {
        currentUploads.value--
      }
      uploadQueue.value.splice(queueIndex, 1)
      return
    }
    
    const completedIndex = completedUploads.value.findIndex(file => file.id === fileId)
    if (completedIndex !== -1) {
      completedUploads.value.splice(completedIndex, 1)
    }
  }
  
  function clearCompletedUploads(): void {
    completedUploads.value = []
  }
  
  function clearFailedUploads(): void {
    uploadQueue.value = uploadQueue.value.filter(file => file.status !== 'Failed')
  }
  
  function clearAllUploads(): void {
    uploadQueue.value = []
    currentUploads.value = 0
    isProcessingQueue.value = false
    uploadingFileIds.clear()
  }

  function resetUploadState(): void {
    // 重置所有上传状态，用于页面加载时初始化
    isProcessingQueue.value = false
    currentUploads.value = 0
    uploadingFileIds.clear()

    // 将正在上传或处理的文件重置为 Pending 状态
    uploadQueue.value.forEach(file => {
      if (file.status === 'Uploading' || file.status === 'Processing') {
        file.status = 'Pending'
        file.progress = 0
        file.currentStep = undefined
        file.error = undefined
      }
    })

    console.log('[UploadStore] 上传状态已重置')
  }
  
  function setMaxConcurrentUploads(max: number): void {
    maxConcurrentUploads.value = Math.max(1, Math.min(10, max))
  }
  
  function setAutoRetry(enabled: boolean): void {
    autoRetry.value = enabled
  }
  
  function generateFileId(): string {
    return `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }
  
  return {
    uploadQueue,
    completedUploads,
    maxConcurrentUploads,
    currentUploads,
    autoRetry,
    retryCount,
    isProcessingQueue,
    
    pendingUploads,
    activeUploads,
    failedUploads,
    completedUploadsList,
    uploadProgress,
    isUploading,
    canUploadMore,
    
    addFiles,
    addFile,
    cancelUpload,
    removeFile,
    processUploadQueue,
    retryFailedUploads,
    clearCompletedUploads,
    clearFailedUploads,
    clearAllUploads,
    resetUploadState,
    setMaxConcurrentUploads,
    setAutoRetry
  }
})
