// 系统相关类型定义

/**
 * 系统配置
 */
export interface SystemConfig {
  appName: string
  version: string
  sessionTimeout: number // 分钟
  maxFileSize: number // MB
  enableAnonymousAccess: boolean
  requireApproval: boolean
  similarityThreshold: number // 0-1
}

/**
 * 系统状态
 */
export interface SystemStatus {
  status: 'ok' | 'degraded' | 'error'
  services: {
    database: 'connected' | 'disconnected'
    redis: 'connected' | 'disconnected'
    vectorDb: 'connected' | 'disconnected'
  }
  version: string
  timestamp: string
}

/**
 * API密钥
 */
export interface ApiKey {
  id: string
  name: string
  key: string
  permissions: string[]
  status: 'active' | 'inactive'
  createdAt: string
  updatedAt: string
  lastUsedAt?: string
  expiresAt?: string
  description?: string
}

/**
 * API密钥表单
 */
export interface ApiKeyForm {
  id?: string
  name: string
  permissions: string[]
  expiresAt?: string
  description?: string
}

/**
 * 系统统计信息
 */
export interface SystemStats {
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
}

/**
 * 系统日志
 */
export interface SystemLog {
  id: string
  timestamp: string
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical'
  module: string
  message: string
  details?: string
  requestId?: string
  userId?: string
  ipAddress?: string
}

/**
 * 系统备份
 */
export interface SystemBackup {
  backupId: string
  filename: string
  size: number
  createdAt: string
  description?: string
  type: 'full' | 'incremental'
  status: 'completed' | 'failed' | 'in_progress'
}

/**
 * 系统监控指标
 */
export interface SystemMetrics {
  cpu: {
    usage: number // 百分比
    cores: number
    loadAverage: number[]
  }
  memory: {
    total: number // MB
    used: number // MB
    free: number // MB
    percentage: number
  }
  disk: {
    total: number // GB
    used: number // GB
    free: number // GB
    percentage: number
  }
  network: {
    bytesIn: number
    bytesOut: number
    packetsIn: number
    packetsOut: number
  }
  uptime: number // 秒
}

/**
 * 权限配置
 */
export interface PermissionConfig {
  roles: {
    [key: string]: {
      name: string
      description: string
      permissions: string[]
    }
  }
  permissions: {
    [key: string]: {
      name: string
      description: string
      module: string
    }
  }
}

/**
 * 用户权限
 */
export interface UserPermission {
  userId: string
  role: string
  permissions: string[]
  effectivePermissions: string[]
  restrictedPermissions: string[]
}