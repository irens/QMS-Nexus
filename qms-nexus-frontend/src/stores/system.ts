// 系统状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  SystemConfig, 
  SystemStatus, 
  ApiKey, 
  SystemStats, 
  SystemMetrics,
  PermissionConfig,
  UserPermission
} from '@/types/system'
import { systemService } from '@/services/system'


export interface SystemState {
  config: SystemConfig | null
  status: SystemStatus | null
  apiKeys: ApiKey[]
  stats: SystemStats | null
  metrics: SystemMetrics | null
  permissionConfig: PermissionConfig | null
  userPermissions: UserPermission | null
  loading: boolean
  error: string | null
}

export const useSystemStore = defineStore('system', () => {
  // 状态
  const config = ref<SystemConfig | null>(null)
  const status = ref<SystemStatus | null>(null)
  const apiKeys = ref<ApiKey[]>([])
  const stats = ref<SystemStats | null>(null)
  const metrics = ref<SystemMetrics | null>(null)
  const permissionConfig = ref<PermissionConfig | null>(null)
  const userPermissions = ref<UserPermission | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const isSystemHealthy = computed(() => {
    if (!status.value) return false
    return status.value.status === 'ok'
  })

  const hasPermission = computed(() => (permission: string): boolean => {
    if (!userPermissions.value) return false
    return userPermissions.value.effectivePermissions.includes(permission)
  })

  const hasRole = computed(() => (role: string): boolean => {
    if (!userPermissions.value) return false
    return userPermissions.value.role === role
  })

  /**
   * 获取系统配置
   */
  async function getSystemConfig(): Promise<SystemConfig | null> {
    loading.value = true
    error.value = null
    
    try {
      const response = await systemService.getSystemConfig()
      config.value = response
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取系统配置失败'
      console.error('获取系统配置失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新系统配置
   */
  async function updateSystemConfig(configData: Partial<SystemConfig>): Promise<SystemConfig | null> {
    loading.value = true
    error.value = null
    
    try {
      const response = await systemService.updateSystemConfig(configData)
      config.value = { ...config.value, ...response }
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新系统配置失败'
      console.error('更新系统配置失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取系统状态
   */
  async function getSystemStatus(): Promise<SystemStatus | null> {
    loading.value = true
    error.value = null
    
    try {
      const response = await systemService.getSystemStatus()
      status.value = response
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取系统状态失败'
      console.error('获取系统状态失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取API密钥列表
   */
  async function getApiKeys(page: number = 1, pageSize: number = 20): Promise<ApiKey[]> {
    loading.value = true
    error.value = null
    
    try {
      const response = await systemService.getApiKeys(page, pageSize)
      apiKeys.value = response.items
      return response.items
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取API密钥失败'
      console.error('获取API密钥失败:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建API密钥
   */
  async function createApiKey(name: string, permissions: string[], expiresAt?: string, description?: string): Promise<ApiKey | null> {
    loading.value = true
    error.value = null
    
    try {
      const response = await systemService.createApiKey({
        name,
        permissions,
        expiresAt,
        description
      })
      apiKeys.value.unshift(response)
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '创建API密钥失败'
      console.error('创建API密钥失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新API密钥
   */
  async function updateApiKey(keyId: string, updates: Partial<ApiKey>): Promise<ApiKey | null> {
    loading.value = true
    error.value = null
    
    try {
      const response = await systemService.updateApiKey(keyId, updates)
      const index = apiKeys.value.findIndex(key => key.id === keyId)
      if (index !== -1) {
        apiKeys.value[index] = { ...apiKeys.value[index], ...response }
      }
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新API密钥失败'
      console.error('更新API密钥失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 删除API密钥
   */
  async function deleteApiKey(keyId: string): Promise<boolean> {
    loading.value = true
    error.value = null
    
    try {
      await systemService.deleteApiKey(keyId)
      const index = apiKeys.value.findIndex(key => key.id === keyId)
      if (index !== -1) {
        apiKeys.value.splice(index, 1)
      }
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除API密钥失败'
      console.error('删除API密钥失败:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取系统统计信息
   */
  async function getSystemStats(): Promise<SystemStats | null> {
    loading.value = true
    error.value = null
    
    try {
      const response = await systemService.getSystemStats()
      stats.value = response
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取系统统计失败'
      console.error('获取系统统计失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取系统监控指标
   */
  async function getSystemMetrics(): Promise<SystemMetrics | null> {
    loading.value = true
    error.value = null
    
    try {
      const response = await systemService.getSystemMetrics()
      metrics.value = response
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取系统监控指标失败'
      console.error('获取系统监控指标失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取权限配置
   */
  async function getPermissionConfig(): Promise<PermissionConfig | null> {
    loading.value = true
    error.value = null
    
    try {
      const response = await systemService.getPermissionConfig()
      permissionConfig.value = response
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取权限配置失败'
      console.error('获取权限配置失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取用户权限
   */
  async function getUserPermissions(userId?: string): Promise<UserPermission | null> {
    loading.value = true
    error.value = null
    
    try {
      const response = await systemService.getUserPermissions(userId)
      userPermissions.value = response
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取用户权限失败'
      console.error('获取用户权限失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 清理系统缓存
   */
  async function clearCache(cacheType?: string): Promise<boolean> {
    loading.value = true
    error.value = null
    
    try {
      await systemService.clearCache(cacheType)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '清理缓存失败'
      console.error('清理缓存失败:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 重启系统服务
   */
  async function restartService(service: string): Promise<boolean> {
    loading.value = true
    error.value = null
    
    try {
      await systemService.restartService(service)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '重启服务失败'
      console.error('重启服务失败:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * 添加通知
   */
  function addNotification(notification: {
    type: 'success' | 'error' | 'warning' | 'info'
    title: string
    message: string
    duration?: number
    read?: boolean
  }): void {
    // 这里可以实现通知系统
    console.log('Notification:', notification)
  }

  /**
   * 重置状态
   */
  function reset(): void {
    config.value = null
    status.value = null
    apiKeys.value = []
    stats.value = null
    metrics.value = null
    permissionConfig.value = null
    userPermissions.value = null
    loading.value = false
    error.value = null
  }

  return {
    // 状态
    config,
    status,
    apiKeys,
    stats,
    metrics,
    permissionConfig,
    userPermissions,
    loading,
    error,
    
    // 计算属性
    isSystemHealthy,
    hasPermission,
    hasRole,
    
    // 方法
    getSystemConfig,
    updateSystemConfig,
    getSystemStatus,
    getApiKeys,
    createApiKey,
    updateApiKey,
    deleteApiKey,
    getSystemStats,
    getSystemMetrics,
    getPermissionConfig,
    getUserPermissions,
    clearCache,
    restartService,
    addNotification,
    reset
  }
})