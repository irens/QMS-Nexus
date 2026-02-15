// API客户端配置
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse, ApiError } from '@/types/api'
import { API_CONFIG, ERROR_CODES } from '@/constants'

// API错误类
export class ApiRequestError extends Error {
  code: number
  details?: any
  
  constructor(message: string, code: number, details?: any) {
    super(message)
    this.name = 'ApiRequestError'
    this.code = code
    this.details = details
  }
}

// API客户端配置
class ApiClient {
  private instance: AxiosInstance
  
  constructor() {
    this.instance = axios.create({
      baseURL: API_CONFIG.BASE_URL,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    this.setupInterceptors()
  }
  
  /**
   * 设置请求和响应拦截器
   */
  private setupInterceptors(): void {
    // 请求拦截器
    this.instance.interceptors.request.use(
      (config) => {
        // 添加认证token
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        // 添加请求ID用于追踪
        config.headers['X-Request-ID'] = generateRequestId()
        
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )
    
    // 响应拦截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse<ApiResponse>) => {
        const { data } = response
        
        // 处理成功的响应
        if (data.code === ERROR_CODES.SUCCESS) {
          return response
        }
        
        // 处理业务错误
        throw new ApiRequestError(data.message, data.code, data.data)
      },
      (error: AxiosError<ApiError>) => {
        return this.handleError(error)
      }
    )
  }
  
  /**
   * 错误处理
   */
  private handleError(error: AxiosError<ApiError>): Promise<never> {
    if (error.response) {
      // 服务器响应错误
      const { status, data } = error.response
      
      switch (status) {
        case ERROR_CODES.UNAUTHORIZED:
          // 清除token并跳转到登录页
          localStorage.removeItem('token')
          // 这里可以添加跳转到登录页的逻辑
          ElMessage.error('登录已过期，请重新登录')
          break
          
        case ERROR_CODES.FORBIDDEN:
          ElMessage.error('权限不足，无法访问该资源')
          break
          
        case ERROR_CODES.NOT_FOUND:
          ElMessage.error('请求的资源不存在')
          break
          
        case ERROR_CODES.TOO_MANY_REQUESTS:
          ElMessage.warning('请求过于频繁，请稍后再试')
          break
          
        case ERROR_CODES.INTERNAL_SERVER_ERROR:
        case ERROR_CODES.BAD_GATEWAY:
        case ERROR_CODES.SERVICE_UNAVAILABLE:
          ElMessage.error('服务器暂时不可用，请稍后重试')
          break
          
        default:
          ElMessage.error(data?.message || '请求失败，请重试')
      }
      
      throw new ApiRequestError(
        data?.message || '请求失败',
        status,
        data?.details
      )
    } else if (error.request) {
      // 网络错误
      ElMessage.error('网络连接失败，请检查网络设置')
      throw new ApiRequestError('网络连接失败', ERROR_CODES.SERVICE_UNAVAILABLE)
    } else {
      // 其他错误
      ElMessage.error('请求配置错误')
      throw new ApiRequestError(error.message || '请求配置错误', ERROR_CODES.BAD_REQUEST)
    }
  }
  
  /**
   * GET请求
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<ApiResponse<T>>(url, config)
    return response.data.data
  }
  
  /**
   * POST请求
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<ApiResponse<T>>(url, data, config)
    return response.data.data
  }
  
  /**
   * PUT请求
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<ApiResponse<T>>(url, data, config)
    return response.data.data
  }
  
  /**
   * DELETE请求
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<ApiResponse<T>>(url, config)
    return response.data.data
  }
  
  /**
   * 上传文件
   */
  async upload<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await this.instance.post<ApiResponse<T>>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      }
    })
    
    return response.data.data
  }
  
  /**
   * 下载文件
   */
  async download(url: string, filename?: string): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob'
    })
    
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }
}

/**
 * 生成请求ID
 */
function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// 创建API客户端实例
export const apiClient = new ApiClient()

// 默认导出
export default apiClient