/**
 * 路由映射工具
 * 用于将路由路径统一添加/system前缀
 * @module utils/route
 */

/**
 * 为路由路径添加/system前缀
 * @param path - 原始路由路径（以/开头）
 * @returns 带/system前缀的路径
 * @example
 *   addSystemPrefix('/dashboard')  // 返回 '/system/dashboard'
 *   addSystemPrefix('/documents/1') // 返回 '/system/documents/1'
 * @throws 当路径不是以/开头时抛出错误
 */
export const addSystemPrefix = (path: string): string => {
  if (!path.startsWith('/')) {
    throw new Error('Path must start with "/"')
  }
  // 如果已经包含/system前缀，直接返回
  if (path.startsWith('/system/')) {
    return path
  }
  return `/system${path}`
}

/**
 * 移除路由路径的/system前缀
 * @param path - 带/system前缀的路径
 * @returns 原始路径
 * @example
 *   removeSystemPrefix('/system/dashboard')  // 返回 '/dashboard'
 *   removeSystemPrefix('/dashboard')         // 返回 '/dashboard'
 */
export const removeSystemPrefix = (path: string): string => {
  if (path.startsWith('/system/')) {
    return path.slice(7) // 移除 '/system'
  }
  return path
}

/**
 * 检查路径是否已包含/system前缀
 * @param path - 路由路径
 * @returns 是否包含/system前缀
 * @example
 *   hasSystemPrefix('/system/dashboard')  // 返回 true
 *   hasSystemPrefix('/dashboard')         // 返回 false
 */
export const hasSystemPrefix = (path: string): boolean => {
  return path.startsWith('/system/')
}

/**
 * 获取文档详情路由
 * @param documentId - 文档ID
 * @returns 文档详情路由路径
 * @example
 *   getDocumentDetailRoute('123')  // 返回 '/system/documents/123'
 */
export const getDocumentDetailRoute = (documentId: string): string => {
  return addSystemPrefix(`/documents/${documentId}`)
}

/**
 * 获取文档列表路由
 * @returns 文档列表路由路径
 * @example
 *   getDocumentsRoute()  // 返回 '/system/documents'
 */
export const getDocumentsRoute = (): string => {
  return addSystemPrefix('/documents')
}

/**
 * 路由路径常量
 * 包含所有常用路由路径
 */
export const ROUTE_PATHS = {
  // 基础路由（已添加/system前缀）
  ROOT: addSystemPrefix('/'),
  DASHBOARD: addSystemPrefix('/dashboard'),
  UPLOAD: addSystemPrefix('/upload'),
  DOCUMENTS: addSystemPrefix('/documents'),
  DOCUMENT_DETAIL: getDocumentDetailRoute,
  TAGS: addSystemPrefix('/tags'),
  CHAT: addSystemPrefix('/chat'),
  SEARCH: addSystemPrefix('/search'),
  
  // 系统管理路由
  SYSTEM_USERS: addSystemPrefix('/system/users'),
  SYSTEM_LOGS: addSystemPrefix('/system/logs'),
  SYSTEM_SETTINGS: addSystemPrefix('/system/settings'),
  
  // 错误页面
  NOT_FOUND: '/404',
  
  // 工具函数
  addSystemPrefix,
  removeSystemPrefix,
  hasSystemPrefix
} as const

// TypeScript类型导出
type RoutePathsType = typeof ROUTE_PATHS

export type { RoutePathsType }
