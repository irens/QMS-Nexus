// 常量定义

// API配置
export const API_CONFIG = {
  // 基础URL - 开发环境使用代理，生产环境使用相对路径
  BASE_URL: import.meta.env.PROD ? '/api/v1' : 'http://localhost:8000/api/v1',
  
  // 请求超时时间（毫秒）
  TIMEOUT: 30000,
  
  // 重试配置
  RETRY_COUNT: 3,
  RETRY_DELAY: 1000,
  
  // 分页配置
  DEFAULT_PAGE_SIZE: 20,
  DEFAULT_MAX_PAGE_SIZE: 100,
  MAX_PAGE_SIZE: 100,
  
  // 文件上传配置
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
  CHUNK_SIZE: 5 * 1024 * 1024, // 5MB
  
  // 支持的文件类型
  SUPPORTED_FILE_TYPES: [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation'
  ],
  
  // 支持的文件扩展名
  SUPPORTED_FILE_EXTENSIONS: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
} as const

// 应用配置
export const APP_CONFIG = {
  // 应用名称
  APP_NAME: 'QMS-Nexus',
  
  // 应用版本
  APP_VERSION: '1.0.0',
  
  // 会话超时时间（毫秒）
  SESSION_TIMEOUT: 30 * 60 * 1000, // 30分钟
  
  // 本地存储键名
  STORAGE_KEYS: {
    TOKEN: 'qms_token',
    USER_INFO: 'qms_user_info',
    PREFERENCES: 'qms_preferences',
    CHAT_HISTORY: 'qms_chat_history'
  },
  
  // 缓存配置
  CACHE_CONFIG: {
    DOCUMENT_LIST: 5 * 60 * 1000, // 5分钟
    TAG_LIST: 10 * 60 * 1000, // 10分钟
    SEARCH_RESULTS: 2 * 60 * 1000, // 2分钟
    SYSTEM_STATUS: 30 * 1000, // 30秒
    USER_INFO: 60 * 60 * 1000 // 1小时
  },
  
  // 消息配置
  MESSAGE_CONFIG: {
    DURATION: 3000, // 消息显示时长（毫秒）
    MAX_COUNT: 3 // 最大消息数量
  }
} as const

// 路由配置
export const ROUTE_CONFIG = {
  // 登录页
  LOGIN: '/login',
  
  // 首页
  HOME: '/system',
  
  // 系统功能路由（统一添加/system前缀）
  DASHBOARD: '/system/dashboard',
  UPLOAD: '/system/upload',
  DOCUMENTS: '/system/documents',
  DOCUMENT_DETAIL: (id: string) => `/system/documents/${id}`,
  SEARCH: '/system/search',
  CHAT: '/system/chat',
  TAGS: '/system/tags',
  
  // 系统管理路由
  USERS: '/system/users',
  LOGS: '/system/logs',
  SETTINGS: '/system/settings',
  
  // 系统路由
  NOT_FOUND: '/404',
  ERROR: '/error'
} as const

// 权限配置
export const PERMISSION_CONFIG = {
  // 角色定义
  ROLES: {
    ADMIN: 'admin',
    USER: 'user',
    GUEST: 'guest'
  },
  
  // 权限定义
  PERMISSIONS: {
    // 文档权限
    DOCUMENT_VIEW: 'document:view',
    DOCUMENT_UPLOAD: 'document:upload',
    DOCUMENT_DOWNLOAD: 'document:download',
    DOCUMENT_DELETE: 'document:delete',
    DOCUMENT_EDIT: 'document:edit',
    
    // 标签权限
    TAG_VIEW: 'tag:view',
    TAG_CREATE: 'tag:create',
    TAG_EDIT: 'tag:edit',
    TAG_DELETE: 'tag:delete',
    
    // 问答权限
    CHAT_USE: 'chat:use',
    CHAT_HISTORY: 'chat:history',
    
    // 用户权限
    USER_VIEW: 'user:view',
    USER_CREATE: 'user:create',
    USER_EDIT: 'user:edit',
    USER_DELETE: 'user:delete',
    USER_ROLE: 'user:role',
    
    // 系统权限
    SYSTEM_VIEW: 'system:view',
    SYSTEM_CONFIG: 'system:config',
    SYSTEM_LOGS: 'system:logs'
  }
} as const

// 文件类型配置
export const FILE_TYPE_CONFIG = {
  // MIME类型映射
  MIME_TYPES: {
    pdf: 'application/pdf',
    doc: 'application/msword',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    xls: 'application/vnd.ms-excel',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ppt: 'application/vnd.ms-powerpoint',
    pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
  },
  
  // 文件类型图标
  FILE_ICONS: {
    pdf: 'file-pdf',
    doc: 'file-word',
    docx: 'file-word',
    xls: 'file-excel',
    xlsx: 'file-excel',
    ppt: 'file-ppt',
    pptx: 'file-ppt'
  },
  
  // 文件类型颜色
  FILE_COLORS: {
    pdf: '#dc2626', // 红色
    doc: '#2563eb', // 蓝色
    docx: '#2563eb',
    xls: '#16a34a', // 绿色
    xlsx: '#16a34a',
    ppt: '#ea580c', // 橙色
    pptx: '#ea580c'
  }
} as const

// 状态配置
export const STATUS_CONFIG = {
  // 上传状态
  UPLOAD_STATUS: {
    PENDING: { text: '待处理', color: '#6b7280' },
    PROCESSING: { text: '处理中', color: '#f59e0b' },
    COMPLETED: { text: '已完成', color: '#22c55e' },
    FAILED: { text: '失败', color: '#ef4444' }
  },
  
  // 用户状态
  USER_STATUS: {
    ACTIVE: { text: '活跃', color: '#22c55e' },
    INACTIVE: { text: '禁用', color: '#6b7280' }
  },
  
  // 用户角色
  USER_ROLE: {
    ADMIN: { text: '管理员', color: '#ef4444' },
    USER: { text: '普通用户', color: '#2563eb' },
    GUEST: { text: '访客', color: '#6b7280' }
  }
} as const

// 错误码配置
export const ERROR_CODES = {
  // 通用错误
  SUCCESS: 200,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  METHOD_NOT_ALLOWED: 405,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  
  // 文件相关错误
  FILE_TOO_LARGE: 413,
  UNSUPPORTED_FILE_TYPE: 415,
  FILE_UPLOAD_FAILED: 1001,
  FILE_PARSE_FAILED: 1002,
  
  // 用户相关错误
  USER_NOT_FOUND: 2001,
  INVALID_CREDENTIALS: 2002,
  USER_ALREADY_EXISTS: 2003,
  INSUFFICIENT_PERMISSIONS: 2004,
  
  // 系统相关错误
  SYSTEM_MAINTENANCE: 3001,
  DATABASE_ERROR: 3002,
  VECTOR_DB_ERROR: 3003,
  LLM_SERVICE_ERROR: 3004
} as const