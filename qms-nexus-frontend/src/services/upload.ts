// 文件上传服务
import { apiClient } from './api'
import type { 
  UploadTask
} from '@/types/api'

/**
 * 文件上传服务
 */
export class UploadService {
  /**
   * 上传文件
   * @param file - 文件对象
   * @param onProgress - 进度回调函数
   * @returns 上传任务信息
   */
  async uploadFile(file: File, onProgress?: (progress: number) => void): Promise<UploadTask> {
    return apiClient.upload<UploadTask>('/upload', file, onProgress)
  }
  
  /**
   * 获取上传任务状态
   * @param taskId - 任务ID
   * @returns 任务状态信息
   */
  async getTaskStatus(taskId: string): Promise<UploadTask> {
    return apiClient.get<UploadTask>(`/tasks/${taskId}`)
  }
  
  /**
   * 轮询任务状态直到完成
   * @param taskId - 任务ID
   * @param onProgress - 进度回调函数
   * @param timeout - 超时时间（毫秒）
   * @returns 最终任务状态
   */
  async pollTaskStatus(
    taskId: string, 
    onProgress?: (task: UploadTask) => void,
    timeout: number = 300000 // 5分钟
  ): Promise<UploadTask> {
    const startTime = Date.now()
    const pollInterval = 1000 // 1秒
    
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const task = await this.getTaskStatus(taskId)
          
          // 调用进度回调
          if (onProgress) {
            onProgress(task)
          }
          
          // 检查是否完成
          if (task.status === 'Completed' || task.status === 'Failed') {
            if (task.status === 'Failed') {
              reject(new Error(task.errorMessage || '文件处理失败'))
            } else {
              resolve(task)
            }
            return
          }
          
          // 检查超时
          if (Date.now() - startTime > timeout) {
            reject(new Error('文件处理超时'))
            return
          }
          
          // 继续轮询
          setTimeout(poll, pollInterval)
        } catch (error) {
          reject(error)
        }
      }
      
      // 开始轮询
      poll()
    })
  }
  
  /**
   * 批量上传文件
   * @param files - 文件列表
   * @param onProgress - 每个文件的进度回调
   * @returns 上传任务列表
   */
  async uploadFiles(
    files: File[], 
    onProgress?: (file: File, progress: number) => void
  ): Promise<UploadTask[]> {
    const tasks: UploadTask[] = []
    
    for (const file of files) {
      try {
        const task = await this.uploadFile(file, (progress) => {
          if (onProgress) {
            onProgress(file, progress)
          }
        })
        tasks.push(task)
      } catch (error) {
        console.error(`文件 ${file.name} 上传失败:`, error)
        // 继续上传其他文件
      }
    }
    
    return tasks
  }
  
  /**
   * 获取支持的文件类型
   * @returns 支持的文件类型列表
   */
  getSupportedFileTypes(): string[] {
    return [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-powerpoint',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    ]
  }
  
  /**
   * 验证文件是否支持上传
   * @param file - 文件对象
   * @returns 验证结果
   */
  validateFile(file: File): { valid: boolean; error?: string } {
    const supportedTypes = this.getSupportedFileTypes()
    
    // 检查文件类型
    if (!supportedTypes.includes(file.type)) {
      return {
        valid: false,
        error: '不支持的文件类型'
      }
    }
    
    // 检查文件大小（50MB限制）
    const maxSize = 50 * 1024 * 1024 // 50MB
    if (file.size > maxSize) {
      return {
        valid: false,
        error: '文件大小不能超过50MB'
      }
    }
    
    return { valid: true }
  }
}

// 创建服务实例
export const uploadService = new UploadService()

// 默认导出
export default uploadService