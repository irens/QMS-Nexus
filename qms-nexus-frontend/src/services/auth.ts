// 认证服务
import { apiClient } from './api'

export interface ApiKey {
  id: string
  name: string
  key_preview: string
  created_at: string
  last_used?: string
  is_active: boolean
  request_count: number
}

export interface ApiKeyCreate {
  name: string
}

export interface ApiKeyCreateResponse {
  id: string
  name: string
  api_key: string
  message: string
}

export interface IpWhitelist {
  id: number
  ip_address: string
  description: string
  created_at: string
  is_active: boolean
}

export interface IpWhitelistCreate {
  ip_address: string
  description?: string
}

export interface AuthConfig {
  auth_enabled: boolean
  whitelist_enabled: boolean
}

export interface AuthCheckResult {
  client_ip: string
  ip_allowed: boolean
  auth_enabled: boolean
  has_api_key: boolean
  api_key_valid: boolean
  is_authenticated: boolean
}

/**
 * 认证服务
 */
export class AuthService {
  /**
   * 创建 API Key
   * @param name - API Key 名称
   * @returns 包含 API Key 的响应（只显示一次）
   */
  async createApiKey(name: string): Promise<ApiKeyCreateResponse> {
    return apiClient.post('/api-keys', { name })
  }

  /**
   * 获取 API Key 列表
   * @param includeInactive - 是否包含已吊销的
   */
  async listApiKeys(includeInactive: boolean = false): Promise<ApiKey[]> {
    return apiClient.get<ApiKey[]>(`/api-keys?include_inactive=${includeInactive}`)
  }

  /**
   * 吊销 API Key
   * @param keyId - API Key ID
   */
  async revokeApiKey(keyId: string): Promise<{ message: string }> {
    return apiClient.post(`/api-keys/${keyId}/revoke`)
  }

  /**
   * 删除 API Key
   * @param keyId - API Key ID
   */
  async deleteApiKey(keyId: string): Promise<{ message: string }> {
    return apiClient.delete(`/api-keys/${keyId}`)
  }

  /**
   * 添加 IP 到白名单
   * @param ipAddress - IP 地址或网段
   * @param description - 描述
   */
  async addIpWhitelist(ipAddress: string, description?: string): Promise<{ message: string }> {
    return apiClient.post('/ip-whitelist', { ip_address: ipAddress, description })
  }

  /**
   * 获取 IP 白名单列表
   */
  async listIpWhitelist(): Promise<IpWhitelist[]> {
    return apiClient.get<IpWhitelist[]>('/ip-whitelist')
  }

  /**
   * 从白名单移除 IP
   * @param ipId - IP 记录ID
   */
  async removeIpWhitelist(ipId: number): Promise<{ message: string }> {
    return apiClient.delete(`/ip-whitelist/${ipId}`)
  }

  /**
   * 获取认证配置
   */
  async getAuthConfig(): Promise<AuthConfig> {
    return apiClient.get<AuthConfig>('/auth/config')
  }

  /**
   * 更新认证配置
   * @param config - 配置项
   */
  async updateAuthConfig(config: Partial<AuthConfig>): Promise<AuthConfig> {
    return apiClient.put('/auth/config', config)
  }

  /**
   * 检查当前认证状态
   */
  async checkAuth(): Promise<AuthCheckResult> {
    return apiClient.get<AuthCheckResult>('/auth/check')
  }

  /**
   * 保存 API Key 到本地存储
   * @param apiKey - API Key
   */
  saveApiKeyToStorage(apiKey: string): void {
    localStorage.setItem('qms_api_key', apiKey)
  }

  /**
   * 从本地存储获取 API Key
   */
  getApiKeyFromStorage(): string | null {
    return localStorage.getItem('qms_api_key')
  }

  /**
   * 从本地存储移除 API Key
   */
  removeApiKeyFromStorage(): void {
    localStorage.removeItem('qms_api_key')
  }

  /**
   * 设置请求头中的 API Key
   * @param apiKey - API Key
   */
  setApiKeyHeader(apiKey: string): void {
    // 这个在 api.ts 的请求拦截器中处理
    localStorage.setItem('token', apiKey)
  }
}

// 创建服务实例
export const authService = new AuthService()
