// 系统管理服务
import { apiClient } from './api'
import type { SystemConfig, ApiKey, ApiKeyForm, SystemStatus } from '@/types/system'
import type { PaginatedResponse } from '@/types/api'

/**
 * 系统服务类
 */
export class SystemService {
  /**
   * 获取系统配置
   */
  async getSystemConfig(): Promise<SystemConfig> {
    return apiClient.get<SystemConfig>('/system/config')
  }

  /**
   * 更新系统配置
   */
  async updateSystemConfig(config: Partial<SystemConfig>): Promise<SystemConfig> {
    return apiClient.put<SystemConfig>('/config', config)
  }

  /**
   * 获取系统状态
   */
  async getSystemStatus(): Promise<SystemStatus> {
    return apiClient.get<SystemStatus>('/system/status')
  }

  /**
   * 获取API密钥列表
   */
  async getApiKeys(page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<ApiKey>> {
    const params = new URLSearchParams({
      page: page.toString(),
      pageSize: pageSize.toString()
    })
    
    return apiClient.get<PaginatedResponse<ApiKey>>(`/system/api-keys?${params.toString()}`)
  }

  /**
   * 创建API密钥
   */
  async createApiKey(form: ApiKeyForm): Promise<ApiKey> {
    return apiClient.post<ApiKey>('/system/api-keys', form)
  }

  /**
   * 更新API密钥
   */
  async updateApiKey(keyId: string, updates: Partial<ApiKeyForm>): Promise<ApiKey> {
    return apiClient.put<ApiKey>(`/system/api-keys/${keyId}`, updates)
  }

  /**
   * 删除API密钥
   */
  async deleteApiKey(keyId: string): Promise<void> {
    return apiClient.delete(`/system/api-keys/${keyId}`)
  }

  /**
   * 获取API密钥日志
   */
  async getApiKeyLogs(keyId: string, page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<any>> {
    const params = new URLSearchParams({
      page: page.toString(),
      pageSize: pageSize.toString()
    })
    
    return apiClient.get<PaginatedResponse<any>>(`/system/api-keys/${keyId}/logs?${params.toString()}`)
  }

  /**
   * 获取系统日志
   */
  async getSystemLogs(
    page: number = 1,
    pageSize: number = 20,
    filters?: {
      level?: string
      module?: string
      startTime?: string
      endTime?: string
    }
  ): Promise<PaginatedResponse<any>> {
    const params = new URLSearchParams({
      page: page.toString(),
      pageSize: pageSize.toString()
    })
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params.append(key, value)
        }
      })
    }
    
    return apiClient.get<PaginatedResponse<any>>(`/system/logs?${params.toString()}`)
  }

  /**
   * 导出系统日志
   */
  async exportSystemLogs(filters?: {
    level?: string
    module?: string
    startTime?: string
    endTime?: string
  }): Promise<Blob> {
    const params = new URLSearchParams()
    
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params.append(key, value)
        }
      })
    }
    
    return apiClient.get<Blob>(`/system/logs/export?${params.toString()}`, {
      responseType: 'blob'
    })
  }

  /**
   * 获取系统统计信息
   */
  async getSystemStats(): Promise<{
    totalDocuments: number
    totalUsers: number
    totalApiKeys: number
    systemUptime: string
    memoryUsage: {
      used: number
      total: number
      percentage: number
    }
    diskUsage: {
      used: number
      total: number
      percentage: number
    }
  }> {
    return apiClient.get('/system/stats')
  }

  /**
   * 重启系统服务
   */
  async restartService(service: string): Promise<void> {
    return apiClient.post(`/system/restart/${service}`)
  }

  /**
   * 清理系统缓存
   */
  async clearCache(cacheType?: string): Promise<void> {
    const params = cacheType ? `?type=${cacheType}` : ''
    return apiClient.post(`/system/clear-cache${params}`)
  }

  /**
   * 备份系统数据
   */
  async backupData(): Promise<{
    backupId: string
    filename: string
    size: number
    createdAt: string
  }> {
    return apiClient.post('/system/backup')
  }

  /**
   * 获取备份列表
   */
  async getBackups(): Promise<PaginatedResponse<any>> {
    return apiClient.get('/system/backups')
  }

  /**
   * 恢复系统数据
   */
  async restoreData(backupId: string): Promise<void> {
    return apiClient.post(`/system/restore/${backupId}`)
  }

  /**
   * 删除备份
   */
  async deleteBackup(backupId: string): Promise<void> {
    return apiClient.delete(`/system/backups/${backupId}`)
  }
}

// 创建系统服务实例
export const systemService = new SystemService()