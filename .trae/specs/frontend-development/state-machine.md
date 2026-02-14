# QMS-Nexus 前端状态机与交互逻辑规范

## 1. 文件上传状态机

### 状态流转图
```
Idle → Uploading → Processing → Success
  ↓        ↓           ↓         ↓
Failed ←  Failed  ←  Failed  ←  Failed
```

### 状态定义
```typescript
enum UploadStatus {
  IDLE = 'idle',           // 初始状态，等待用户操作
  UPLOADING = 'uploading', // 正在上传到服务器
  PROCESSING = 'processing', // 服务器正在解析文档
  SUCCESS = 'success',     // 上传和解析完成
  FAILED = 'failed'        // 上传或解析失败
}

interface UploadState {
  status: UploadStatus;
  file: File | null;
  progress: number;         // 0-100
  taskId: string | null;    // 后端任务ID
  error: string | null;     // 错误信息
  currentStep: string;      // 当前处理步骤描述
  estimatedTime: number;    // 预估剩余时间(秒)
}
```

### 状态转换逻辑
```typescript
// 状态转换函数
const uploadMachine = {
  // 用户选择文件
  [UploadStatus.IDLE]: {
    selectFile: (file: File) => ({
      status: UploadStatus.UPLOADING,
      file,
      progress: 0,
      error: null
    })
  },
  
  // 上传中
  [UploadStatus.UPLOADING]: {
    progress: (percentage: number) => ({
      progress: percentage
    }),
    uploadSuccess: (taskId: string) => ({
      status: UploadStatus.PROCESSING,
      taskId,
      progress: 100,
      currentStep: '正在解析文档...'
    }),
    uploadFailed: (error: string) => ({
      status: UploadStatus.FAILED,
      error,
      progress: 0
    })
  },
  
  // 解析中
  [UploadStatus.PROCESSING]: {
    updateProgress: (step: string, progress: number, timeLeft: number) => ({
      currentStep: step,
      progress: Math.max(90, progress), // 解析阶段90-100%
      estimatedTime: timeLeft
    }),
    processingComplete: () => ({
      status: UploadStatus.SUCCESS,
      progress: 100,
      currentStep: '文档处理完成'
    }),
    processingFailed: (error: string) => ({
      status: UploadStatus.FAILED,
      error
    })
  }
};
```

### UI组件状态映射
```typescript
// 组件状态映射
const getUploadUIConfig = (status: UploadStatus) => {
  const configs = {
    [UploadStatus.IDLE]: {
      showDropzone: true,
      showProgress: false,
      showResult: false,
      buttonText: '选择文件',
      buttonType: 'primary'
    },
    [UploadStatus.UPLOADING]: {
      showDropzone: false,
      showProgress: true,
      showResult: false,
      buttonText: '上传中...',
      buttonType: 'default',
      progressColor: '#1890ff'
    },
    [UploadStatus.PROCESSING]: {
      showDropzone: false,
      showProgress: true,
      showResult: false,
      buttonText: '解析中...',
      buttonType: 'default',
      progressColor: '#52c41a'
    },
    [UploadStatus.SUCCESS]: {
      showDropzone: false,
      showProgress: false,
      showResult: true,
      buttonText: '继续上传',
      buttonType: 'success'
    },
    [UploadStatus.FAILED]: {
      showDropzone: true,
      showProgress: false,
      showResult: true,
      buttonText: '重新上传',
      buttonType: 'danger'
    }
  };
  return configs[status];
};
```

## 2. 智能问答交互流程

### 对话状态管理
```typescript
enum ChatStatus {
  IDLE = 'idle',           // 等待输入
  TYPING = 'typing',       // 用户正在输入
  SENDING = 'sending',     // 正在发送请求
  THINKING = 'thinking',   // AI正在思考
  STREAMING = 'streaming', // 正在接收流式响应
  COMPLETE = 'complete',   // 回答完成
  ERROR = 'error'          // 发生错误
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{
    document_name: string;
    page?: number;
    table?: string;
    score: number;
  }>;
  timestamp: number;
  status: ChatStatus;
  error?: string;
}

interface ChatState {
  messages: ChatMessage[];
  currentInput: string;
  status: ChatStatus;
  isWaitingForFirstResponse: boolean;
  streamingContent: string;
}
```

### 问答交互时序图
```
用户输入 → 本地验证 → 发送请求 → 显示思考状态 → 接收流式数据 → 渲染回答 → 显示来源
   ↓         ↓          ↓           ↓            ↓           ↓         ↓
空输入   长度超限   网络错误   超时处理     解析错误    格式化    引用标注
```

### 流式数据处理逻辑
```typescript
// 流式数据处理
class ChatStreamHandler {
  private buffer: string = '';
  private sources: any[] = [];
  private isComplete: boolean = false;
  
  handleStreamEvent(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data);
      
      switch (data.event) {
        case 'answer':
          this.handleAnswer(data.data);
          break;
        case 'source':
          this.handleSource(data.data);
          break;
        case 'done':
          this.handleComplete();
          break;
        case 'error':
          this.handleError(data.data);
          break;
      }
    } catch (error) {
      console.error('解析流式数据失败:', error);
    }
  }
  
  private handleAnswer(answerData: AnswerEvent) {
    // 处理回答内容
    if (answerData.is_complete) {
      this.isComplete = true;
    }
    
    // 打字机效果实现
    this.typeWriterEffect(answerData.content);
  }
  
  private typeWriterEffect(content: string) {
    // 模拟打字机效果，逐字显示
    const chars = content.split('');
    let index = 0;
    
    const timer = setInterval(() => {
      if (index < chars.length) {
        this.streamingContent += chars[index];
        index++;
        this.updateUI();
      } else {
        clearInterval(timer);
      }
    }, 30); // 30ms间隔，可调节速度
  }
  
  private handleSource(sourceData: SourceEvent) {
    this.sources = sourceData.sources;
    // 延迟显示来源，等回答完成后再显示
    if (this.isComplete) {
      this.updateSources();
    }
  }
  
  private handleComplete() {
    this.isComplete = true;
    // 最终更新UI状态
    this.updateUI();
    this.closeStream();
  }
}
```

## 3. 文档管理状态逻辑

### 文档列表状态
```typescript
enum DocumentListStatus {
  LOADING = 'loading',     // 正在加载
  LOADED = 'loaded',     // 加载完成
  EMPTY = 'empty',       // 无数据
  ERROR = 'error',       // 加载失败
  REFRESHING = 'refreshing' // 正在刷新
}

interface DocumentListState {
  status: DocumentListStatus;
  documents: Document[];
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
  filters: {
    search: string;
    type: string[];
    tags: string[];
    dateRange: [Date, Date] | null;
  };
  sort: {
    field: string;
    order: 'asc' | 'desc';
  };
  selectedIds: string[];
}
```

### 文档操作状态机
```typescript
// 单个文档操作状态
enum DocumentOperation {
  IDLE = 'idle',
  PREVIEWING = 'previewing',
  DOWNLOADING = 'downloading',
  DELETING = 'deleting',
  TAGGING = 'tagging'
}

interface DocumentOperationState {
  operation: DocumentOperation;
  targetId: string | null;
  progress: number;      // 下载进度
  error: string | null;
}
```

## 4. 标签管理状态逻辑

### 标签操作状态
```typescript
enum TagOperationStatus {
  IDLE = 'idle',
  CREATING = 'creating',
  EDITING = 'editing',
  DELETING = 'deleting',
  APPLYING = 'applying'  // 应用到文档
}

interface TagState {
  tags: Tag[];
  status: TagOperationStatus;
  selectedTagIds: string[];
  searchQuery: string;
  isLoading: boolean;
}
```

## 5. 全局状态管理架构

### Pinia Store 结构
```typescript
// 主状态树
interface RootState {
  upload: UploadState;
  chat: ChatState;
  documents: DocumentListState;
  documentOps: DocumentOperationState;
  tags: TagState;
  user: UserState;
  system: SystemState;
}

// 用户状态
interface UserState {
  profile: UserProfile | null;
  permissions: string[];
  isLoggedIn: boolean;
}

// 系统状态
interface SystemState {
  isOnline: boolean;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
  systemInfo: {
    version: string;
    buildTime: string;
  };
  notifications: Notification[];
}
```

### 状态同步机制
```typescript
// 状态同步策略
const stateSyncStrategy = {
  // 实时同步 (立即生效)
  realTime: ['chat.messages', 'upload.progress'],
  
  // 延迟同步 (防抖处理)
  debounced: ['documents.filters', 'chat.currentInput'],
  
  // 批量同步 (定时同步)
  batched: ['documents.selectedIds', 'tags.selectedTagIds'],
  
  // 持久化同步 (localStorage)
  persistent: ['user.profile', 'chat.history', 'system.preferences']
};
```

## 6. 错误处理状态逻辑

### 错误状态分类
```typescript
enum ErrorLevel {
  INFO = 'info',        // 用户可恢复的信息
  WARNING = 'warning',  // 需要注意但不影响使用
  ERROR = 'error',     // 影响当前操作
  FATAL = 'fatal'      // 系统级错误，需要重启
}

enum ErrorType {
  NETWORK = 'network',      // 网络错误
  VALIDATION = 'validation', // 输入验证错误
  BUSINESS = 'business',     // 业务逻辑错误
  SYSTEM = 'system',        // 系统错误
  TIMEOUT = 'timeout'       // 超时错误
}

interface AppError {
  type: ErrorType;
  level: ErrorLevel;
  message: string;
  code?: string;
  details?: any;
  timestamp: number;
  context?: string;  // 错误发生上下文
}
```

### 错误恢复策略
```typescript
// 自动恢复机制
const errorRecovery = {
  [ErrorType.NETWORK]: {
    retry: true,
    maxRetries: 3,
    retryDelay: 1000,
    fallback: 'offline-mode'
  },
  
  [ErrorType.TIMEOUT]: {
    retry: true,
    maxRetries: 2,
    retryDelay: 500,
    fallback: 'cached-data'
  },
  
  [ErrorType.VALIDATION]: {
    retry: false,
    userAction: 'correct-input'
  }
};
```

## 7. 性能优化状态逻辑

### 加载状态管理
```typescript
enum LoadingStrategy {
  SKELETON = 'skeleton',    // 骨架屏
  SPINNER = 'spinner',      // 加载动画
  PROGRESSIVE = 'progressive', // 渐进式加载
  LAZY = 'lazy'            // 懒加载
}

interface LoadingState {
  strategy: LoadingStrategy;
  priority: 'high' | 'medium' | 'low';
  timeout: number;         // 加载超时时间
  retryCount: number;
  isCritical: boolean;     // 是否关键资源
}
```

### 缓存策略
```typescript
// 缓存层级
const cacheStrategy = {
  MEMORY: {
    duration: 5 * 60 * 1000,  // 5分钟
    capacity: 100,             // 最大缓存数量
    priority: 'high'
  },
  
  LOCAL_STORAGE: {
    duration: 24 * 60 * 60 * 1000, // 24小时
    capacity: 1000,
    priority: 'medium'
  },
  
  SESSION_STORAGE: {
    duration: -1, // 会话级别
    capacity: 500,
    priority: 'low'
  }
};
```

这个状态机设计确保了前端应用的稳定性和可预测性，为复杂的业务逻辑提供了清晰的状态管理方案。