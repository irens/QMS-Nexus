// 测试工具函数
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * 模拟 Element Plus 组件
 */
export function mockElementPlus() {
  vi.mock('element-plus', () => ({
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn().mockResolvedValue(true),
      alert: vi.fn().mockResolvedValue(true),
      prompt: vi.fn().mockResolvedValue({ value: 'test' })
    },
    ElLoading: {
      service: vi.fn(() => ({
        close: vi.fn()
      }))
    }
  }))
}

/**
 * 模拟 API 响应
 */
export function mockApiResponse<T>(data: T, delay = 0): Promise<T> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(data), delay)
  })
}

/**
 * 模拟 API 错误
 */
export function mockApiError(message = 'API Error', code = 500): Promise<never> {
  return Promise.reject({
    response: {
      status: code,
      data: { message }
    },
    message
  })
}

/**
 * 创建测试数据
 */
export function createTestData<T>(factory: () => T, count = 1): T[] {
  return Array.from({ length: count }, factory)
}

/**
 * 等待 Vue 更新
 */
export async function waitForVueUpdate() {
  await nextTick()
  // 额外等待确保所有异步操作完成
  await new Promise(resolve => setTimeout(resolve, 100))
}

/**
 * 模拟文件上传
 */
export function mockFileUpload(file: File, progress = 100): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(() => resolve(), 100)
  })
}

/**
 * 创建测试文件
 */
export function createTestFile(name: string, size = 1024, type = 'text/plain'): File {
  const content = new Array(size).fill('a').join('')
  return new File([content], name, { type })
}

/**
 * 创建测试文件列表
 */
export function createTestFiles(count = 5): File[] {
  return Array.from({ length: count }, (_, index) => 
    createTestFile(`test-file-${index + 1}.txt`, 1024 * (index + 1))
  )
}

/**
 * 模拟本地存储
 */
export function mockLocalStorage() {
  const storage = new Map<string, string>()
  
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: vi.fn((key: string) => storage.get(key) || null),
      setItem: vi.fn((key: string, value: string) => storage.set(key, value)),
      removeItem: vi.fn((key: string) => storage.delete(key)),
      clear: vi.fn(() => storage.clear()),
      length: storage.size,
      key: vi.fn((index: number) => Array.from(storage.keys())[index] || null)
    },
    writable: true
  })
  
  return storage
}

/**
 * 模拟会话存储
 */
export function mockSessionStorage() {
  const storage = new Map<string, string>()
  
  Object.defineProperty(window, 'sessionStorage', {
    value: {
      getItem: vi.fn((key: string) => storage.get(key) || null),
      setItem: vi.fn((key: string, value: string) => storage.set(key, value)),
      removeItem: vi.fn((key: string) => storage.delete(key)),
      clear: vi.fn(() => storage.clear()),
      length: storage.size,
      key: vi.fn((index: number) => Array.from(storage.keys())[index] || null)
    },
    writable: true
  })
  
  return storage
}

/**
 * 模拟剪贴板
 */
export function mockClipboard() {
  const clipboardData = ref('')
  
  Object.defineProperty(navigator, 'clipboard', {
    value: {
      writeText: vi.fn(async (text: string) => {
        clipboardData.value = text
      }),
      readText: vi.fn(async () => clipboardData.value)
    },
    writable: true
  })
  
  return clipboardData
}

/**
 * 模拟文件读取器
 */
export function mockFileReader() {
  const FileReaderMock = vi.fn(() => ({
    readAsText: vi.fn(),
    readAsDataURL: vi.fn(),
    readAsArrayBuffer: vi.fn(),
    abort: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
    result: null,
    error: null,
    readyState: 0
  }))
  
  Object.defineProperty(window, 'FileReader', {
    value: FileReaderMock,
    writable: true
  })
  
  return FileReaderMock
}

/**
 * 模拟拖放事件
 */
export function mockDragEvent(type: string, files: File[] = []): DragEvent {
  return new DragEvent(type, {
    dataTransfer: {
      files: files,
      items: files.map(file => ({
        kind: 'file',
        type: file.type,
        getAsFile: () => file
      })),
      types: ['Files'],
      dropEffect: 'copy',
      effectAllowed: 'all',
      clearData: vi.fn(),
      getData: vi.fn(),
      setData: vi.fn(),
      setDragImage: vi.fn()
    } as any
  })
}

/**
 * 模拟窗口大小变化
 */
export function mockWindowResize(width: number, height: number) {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width
  })
  
  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: height
  })
  
  // 触发 resize 事件
  window.dispatchEvent(new Event('resize'))
}

/**
 * 模拟网络请求延迟
 */
export function mockNetworkDelay(delay = 100): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, delay))
}

/**
 * 模拟网络错误
 */
export function mockNetworkError() {
  return Promise.reject(new Error('Network Error'))
}

/**
 * 模拟超时
 */
export function mockTimeout(delay = 5000): Promise<never> {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new Error('Request Timeout')), delay)
  })
}

/**
 * 创建模拟用户
 */
export function createMockUser(overrides = {}) {
  return {
    id: '1',
    username: 'testuser',
    email: 'test@example.com',
    role: 'user',
    status: 'active',
    createdAt: '2024-01-01T00:00:00Z',
    lastLoginAt: '2024-01-15T00:00:00Z',
    ...overrides
  }
}

/**
 * 创建模拟文档
 */
export function createMockDocument(overrides = {}) {
  return {
    id: '1',
    name: 'test-document.pdf',
    size: 1024000,
    type: 'application/pdf',
    uploadTime: '2024-01-15T00:00:00Z',
    status: 'completed',
    tags: ['test'],
    ...overrides
  }
}

/**
 * 创建模拟标签
 */
export function createMockTag(overrides = {}) {
  return {
    id: '1',
    name: 'test-tag',
    color: 'blue',
    description: 'Test tag',
    usageCount: 5,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-15T00:00:00Z',
    ...overrides
  }
}

/**
 * 创建模拟API密钥
 */
export function createMockApiKey(overrides = {}) {
  return {
    id: '1',
    name: 'test-api-key',
    key: 'sk-1234567890abcdef',
    permissions: ['document:read', 'chat:use'],
    status: 'active',
    createdAt: '2024-01-01T00:00:00Z',
    lastUsedAt: '2024-01-15T00:00:00Z',
    ...overrides
  }
}

/**
 * 创建模拟系统日志
 */
export function createMockSystemLog(overrides = {}) {
  return {
    id: '1',
    timestamp: '2024-01-15T00:00:00Z',
    level: 'info',
    module: 'document',
    message: 'Test system log',
    details: 'Detailed log information',
    userId: '1',
    ipAddress: '192.168.1.1',
    requestId: 'req-123456',
    ...overrides
  }
}

/**
 * 测试工具函数导出
 */
export const TestUtils = {
  mockElementPlus,
  mockApiResponse,
  mockApiError,
  createTestData,
  waitForVueUpdate,
  mockFileUpload,
  createTestFile,
  createTestFiles,
  mockLocalStorage,
  mockSessionStorage,
  mockClipboard,
  mockFileReader,
  mockDragEvent,
  mockWindowResize,
  mockNetworkDelay,
  mockNetworkError,
  mockTimeout,
  createMockUser,
  createMockDocument,
  createMockTag,
  createMockApiKey,
  createMockSystemLog
} as const

export default TestUtils