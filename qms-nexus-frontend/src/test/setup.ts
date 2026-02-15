// 测试环境设置
import { vi, beforeEach, afterEach, beforeAll, afterAll } from 'vitest'
import { config } from '@vue/test-utils'

// 设置全局测试函数
global.beforeEach = beforeEach
global.afterEach = afterEach
global.beforeAll = beforeAll
global.afterAll = afterAll

// 设置全局window和document
if (typeof window === 'undefined') {
  global.window = global as any
}
if (typeof document === 'undefined') {
  global.document = {
    createElement: vi.fn(),
    createTextNode: vi.fn(),
    querySelector: vi.fn(),
    querySelectorAll: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    body: {
      appendChild: vi.fn(),
      removeChild: vi.fn(),
      style: {}
    }
  } as any
}

// 导入 Element Plus 模拟
import { createElementPlusMock } from './element-plus-mocks'

// 模拟 Element Plus 组件
vi.mock('element-plus', () => createElementPlusMock())

// 模拟 Element Plus 图标
vi.mock('@element-plus/icons-vue', () => ({
  Search: { name: 'Search' },
  Document: { name: 'Document' },
  DocumentCopy: { name: 'DocumentCopy' },
  Tickets: { name: 'Tickets' },
  Notebook: { name: 'Notebook' },
  CaretBottom: { name: 'CaretBottom' },
  Edit: { name: 'Edit' },
  Share: { name: 'Share' },
  Delete: { name: 'Delete' },
  Download: { name: 'Download' },
  Plus: { name: 'Plus' },
  Upload: { name: 'Upload' },
  Refresh: { name: 'Refresh' },
  Setting: { name: 'Setting' },
  User: { name: 'User' },
  Lock: { name: 'Lock' },
  View: { name: 'View' },
  Hide: { name: 'Hide' },
  ArrowLeft: { name: 'ArrowLeft' },
  ArrowRight: { name: 'ArrowRight' },
  ArrowUp: { name: 'ArrowUp' },
  ArrowDown: { name: 'ArrowDown' },
  Close: { name: 'Close' },
  Check: { name: 'Check' },
  CircleCheck: { name: 'CircleCheck' },
  CircleClose: { name: 'CircleClose' },
  InfoFilled: { name: 'InfoFilled' },
  WarningFilled: { name: 'WarningFilled' },
  CircleCheckFilled: { name: 'CircleCheckFilled' },
  CircleCloseFilled: { name: 'CircleCloseFilled' },
  Loading: { name: 'Loading' },
  Menu: { name: 'Menu' },
  HomeFilled: { name: 'HomeFilled' },
  Avatar: { name: 'Avatar' },
  HelpFilled: { name: 'HelpFilled' },
  Message: { name: 'Message' },
  Bell: { name: 'Bell' },
  Calendar: { name: 'Calendar' },
  Clock: { name: 'Clock' },
  Location: { name: 'Location' },
  Phone: { name: 'Phone' },
  Mail: { name: 'Mail' },
  Star: { name: 'Star' },
  StarFilled: { name: 'StarFilled' },
  Heart: { name: 'Heart' },
  HeartFilled: { name: 'HeartFilled' },
  ChatDotRound: { name: 'ChatDotRound' },
  ChatLineRound: { name: 'ChatLineRound' },
  ChatDotSquare: { name: 'ChatDotSquare' },
  ChatLineSquare: { name: 'ChatLineSquare' }
}))

// 全局测试配置
config.global.mocks = {
  $t: (msg: string) => msg,
  $tc: (msg: string, count: number) => msg,
  $d: (date: Date) => date.toISOString(),
  $n: (num: number) => num.toString()
}

// 模拟全局对象
global.ResizeObserver = vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

global.IntersectionObserver = vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// 模拟 window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  }))
})

// 模拟滚动行为
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: vi.fn()
})

// 模拟 Element Plus 组件
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
  },
  ElNotification: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  }
}))

// 模拟 Element Plus 图标
vi.mock('@element-plus/icons-vue', () => ({
  House: vi.fn(),
  Document: vi.fn(),
  Upload: vi.fn(),
  DocumentCopy: vi.fn(),
  CollectionTag: vi.fn(),
  ChatDotRound: vi.fn(),
  Search: vi.fn(),
  Setting: vi.fn(),
  User: vi.fn(),
  DocumentChecked: vi.fn(),
  Operation: vi.fn(),
  InfoFilled: vi.fn(),
  Bell: vi.fn(),
  CaretBottom: vi.fn(),
  Fold: vi.fn(),
  Expand: vi.fn(),
  Plus: vi.fn(),
  Edit: vi.fn(),
  Delete: vi.fn(),
  View: vi.fn(),
  Hide: vi.fn(),
  CopyDocument: vi.fn(),
  Refresh: vi.fn(),
  Download: vi.fn(),
  Menu: vi.fn(),
  Close: vi.fn()
}))

// 模拟 Axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      },
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn()
    }))
  }
}))

// 模拟本地存储
const mockStorage = new Map<string, string>()

Object.defineProperty(window, 'localStorage', {
  value: {
    getItem: vi.fn((key: string) => mockStorage.get(key) || null),
    setItem: vi.fn((key: string, value: string) => mockStorage.set(key, value)),
    removeItem: vi.fn((key: string) => mockStorage.delete(key)),
    clear: vi.fn(() => mockStorage.clear()),
    length: mockStorage.size,
    key: vi.fn((index: number) => Array.from(mockStorage.keys())[index] || null)
  },
  writable: true
})

// 模拟会话存储
const mockSessionStorage = new Map<string, string>()

Object.defineProperty(window, 'sessionStorage', {
  value: {
    getItem: vi.fn((key: string) => mockSessionStorage.get(key) || null),
    setItem: vi.fn((key: string, value: string) => mockSessionStorage.set(key, value)),
    removeItem: vi.fn((key: string) => mockSessionStorage.delete(key)),
    clear: vi.fn(() => mockSessionStorage.clear()),
    length: mockSessionStorage.size,
    key: vi.fn((index: number) => Array.from(mockSessionStorage.keys())[index] || null)
  },
  writable: true
})

// 模拟剪贴板
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: vi.fn().mockResolvedValue(undefined),
    readText: vi.fn().mockResolvedValue('')
  },
  writable: true
})

// 模拟 crypto.subtle
Object.defineProperty(global, 'crypto', {
  value: {
    subtle: {
      digest: vi.fn().mockImplementation((algorithm: string, data: ArrayBuffer) => {
        // 简单的MD5模拟
        const buffer = new Uint8Array(data)
        const hash = new Uint8Array(16)
        for (let i = 0; i < buffer.length; i++) {
          hash[i % 16] ^= buffer[i]
        }
        return Promise.resolve(hash.buffer)
      })
    }
  },
  writable: true
})

// 模拟 EventSource
class MockEventSource {
  url: string
  readyState: number = 0
  onmessage: ((event: any) => void) | null = null
  onerror: ((event: any) => void) | null = null
  
  constructor(url: string) {
    this.url = url
    this.readyState = 1 // CONNECTING
    
    // 模拟连接成功
    setTimeout(() => {
      this.readyState = 2 // OPEN
      
      // 模拟消息流
      setTimeout(() => {
        if (this.onmessage) {
          this.onmessage({ data: '{"type": "chunk", "content": "测试回答"}' })
        }
        
        setTimeout(() => {
          if (this.onmessage) {
            this.onmessage({ data: '{"type": "complete", "totalTokens": 10, "responseTime": 1000}' })
          }
          this.readyState = 3 // CLOSED
        }, 200)
      }, 100)
    }, 0)
  }
  
  close() {
    this.readyState = 3 // CLOSED
  }
  
  addEventListener(event: string, handler: Function) {
    if (event === 'message') {
      this.onmessage = handler as any
    } else if (event === 'error') {
      this.onerror = handler as any
    }
  }
  
  removeEventListener() {
    this.onmessage = null
    this.onerror = null
  }
  
  dispatchEvent() {
    // 空实现
  }
}

Object.defineProperty(global, 'EventSource', {
  value: MockEventSource,
  writable: true
})

// 模拟 FileReader
Object.defineProperty(global, 'FileReader', {
  value: vi.fn(() => ({
    readAsText: vi.fn(),
    readAsDataURL: vi.fn(function(this: any) {
      // 模拟异步读取完成
      setTimeout(() => {
        this.result = 'data:text/plain;base64,dGVzdA=='
        if (this.onload) this.onload()
      }, 0)
    }),
    readAsArrayBuffer: vi.fn(),
    abort: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
    result: null,
    error: null,
    readyState: 0,
    onload: null,
    onerror: null
  })),
  writable: true
})

// 模拟拖放事件
Object.defineProperty(window, 'DragEvent', {
  value: class DragEvent extends Event {
    dataTransfer: DataTransfer
    constructor(type: string, eventInitDict?: EventInit) {
      super(type, eventInitDict)
      this.dataTransfer = {
        files: [],
        items: [],
        types: [],
        dropEffect: 'none',
        effectAllowed: 'none',
        clearData: vi.fn(),
        getData: vi.fn(),
        setData: vi.fn(),
        setDragImage: vi.fn()
      } as any
    }
  },
  writable: true
})

// 控制台错误处理
const originalConsoleError = console.error
console.error = (...args: any[]) => {
  // 忽略特定的 Vue 警告
  if (args[0]?.includes?.('Vue warn')) return
  originalConsoleError.apply(console, args)
}