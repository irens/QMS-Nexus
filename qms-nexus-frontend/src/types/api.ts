// API通用响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp: string
}

// 分页响应类型
export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// API错误类型
export interface ApiError {
  code: number
  message: string
  details?: any
  timestamp: string
}

// 文件上传相关类型
export interface UploadTask {
  taskId: string
  status: 'Pending' | 'Processing' | 'Completed' | 'Failed'
  filename: string
  progress: number
  currentStep?: string
  estimatedTime?: number
  errorMessage?: string
  result?: {
    documentId: string
    chunksCount: number
    parseTime: number
  }
}

// 文档相关类型
export interface Document {
  id: string
  filename: string
  fileType: 'pdf' | 'doc' | 'docx' | 'xls' | 'xlsx' | 'ppt' | 'pptx'
  fileSize: number
  uploadTime: string
  status: 'Pending' | 'Processing' | 'Completed' | 'Failed'
  tags: string[]
  metadata: {
    pages?: number
    author?: string
    creationDate?: string
    lastModified?: string
  }
  chunksCount?: number
  parseTime?: number
  errorMessage?: string
}

// 标签相关类型
export interface Tag {
  id: string
  name: string
  description?: string
  color?: string
  usageCount: number
  createdAt: string
  updatedAt: string
}

// 问答相关类型
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Array<{
    documentName: string
    page?: number
    table?: string
    score: number
  }>
  timestamp: number
  status: 'sending' | 'thinking' | 'streaming' | 'complete' | 'error'
  error?: string
}

export interface AskRequest {
  question: string
  context?: string[]
  filterTags?: string[]
  topK?: number
}

export interface AskResponse {
  answer: string
  sources: Array<{
    documentName: string
    page?: number
    table?: string
    score: number
  }>
  totalTokens: number
  responseTime: number
}

// 搜索相关类型
export interface SearchRequest {
  query: string
  filterTags?: string[]
  topK?: number
  page?: number
  pageSize?: number
}

export interface SearchResult {
  text: string
  source: string
  tags: string[]
  score: number
  metadata?: {
    page?: number
    table?: string
    chunkId?: string
  }
}

// 用户相关类型
export interface User {
  id: string
  name: string
  email: string
  role: 'admin' | 'user' | 'guest'
  department?: string
  phone?: string
  status: 'active' | 'inactive'
  createdAt: string
  lastLogin?: string
  lastLoginIp?: string
  permissions: string[]
}

export interface CreateUserRequest {
  name: string
  email: string
  role: 'admin' | 'user' | 'guest'
  department?: string
  phone?: string
}

export interface UpdateUserRequest {
  name?: string
  role?: 'admin' | 'user' | 'guest'
  department?: string
  phone?: string
  status?: 'active' | 'inactive'
}

// 日志相关类型
export interface LogItem {
  id: string
  timestamp: string
  userName: string
  userId: string
  operation: string
  description: string
  details?: string
  objectName?: string
  objectType?: string
  ipAddress: string
  location: string
  status: 'success' | 'failed'
  duration: number
  requestId: string
  errorMessage?: string
  errorStack?: string
  errorDetails?: string
}

// 系统状态相关类型
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

// 系统配置相关类型
export interface SystemConfig {
  maxFileSize: number
  supportedFileTypes: string[]
  maxChunksPerDocument: number
  vectorDimension: number
  similarityThreshold: number
  maxSearchResults: number
  sessionTimeout: number
  enableAnonymousAccess: boolean
  requireApproval: boolean
}

// 通用枚举类型
export enum FileType {
  PDF = 'application/pdf',
  DOC = 'application/msword',
  DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  XLS = 'application/vnd.ms-excel',
  XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  PPT = 'application/vnd.ms-powerpoint',
  PPTX = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
}

export enum UploadStatus {
  PENDING = 'Pending',
  PROCESSING = 'Processing',
  COMPLETED = 'Completed',
  FAILED = 'Failed'
}

export enum DocumentStatus {
  PENDING = 'Pending',
  PROCESSING = 'Processing',
  COMPLETED = 'Completed',
  FAILED = 'Failed'
}

export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  GUEST = 'guest'
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive'
}

export enum LogStatus {
  SUCCESS = 'success',
  FAILED = 'failed'
}

// 上传文件类型
export interface UploadFile {
  id: string
  file: File
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  progress: number
  taskId?: string
  error?: string
  currentStep?: string
  estimatedTime?: number
  result?: {
    documentId: string
    chunksCount: number
    parseTime: number
  }
}