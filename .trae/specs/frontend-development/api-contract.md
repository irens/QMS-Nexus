# QMS-Nexus 前端 API 契约文档

## Base URL
- 开发环境: `http://localhost:8000/api/v1`
- 生产环境: `/api/v1`

## 认证方式
- 当前阶段: 无认证 (开发阶段)
- 后续阶段: Bearer Token (Authorization: Bearer {token})

## 通用响应格式
```typescript
interface ApiResponse<T> {
  code: number;      // 状态码
  message: string;   // 响应消息
  data: T;          // 响应数据
  timestamp: string; // 时间戳
}
```

## 接口详情

### 1. 文件上传接口

#### POST /upload
上传单个文件，支持 PDF、Word、Excel、PPT 格式

**请求格式**: `multipart/form-data`

**请求参数**:
```typescript
interface UploadRequest {
  file: File;  // 文件对象 (最大 50MB)
}
```

**成功响应** (200):
```typescript
interface UploadResponse {
  task_id: string;      // 任务ID，用于查询处理状态
  status: 'Pending' | 'Processing' | 'Completed' | 'Failed';
  filename: string;     // 原始文件名
  message: string;      // 状态描述
}
```

**错误响应**:
- `413`: 文件太大 (文件 > 50MB)
- `415`: 不支持的文件格式
- `400`: 请求参数错误

**使用示例**:
```typescript
const formData = new FormData();
formData.append('file', file);

const response = await axios.post('/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
  onUploadProgress: (progressEvent) => {
    const percentCompleted = Math.round(
      (progressEvent.loaded * 100) / progressEvent.total
    );
    console.log(`上传进度: ${percentCompleted}%`);
  }
});
```

### 2. 任务状态查询接口

#### GET /tasks/{task_id}
查询文件上传和处理状态

**路径参数**:
- `task_id`: string - 上传任务返回的任务ID

**成功响应** (200):
```typescript
interface TaskStatusResponse {
  task_id: string;
  status: 'Pending' | 'Processing' | 'Completed' | 'Failed';
  progress: number;        // 处理进度 (0-100)
  current_step?: string;    // 当前处理步骤
  estimated_time?: number; // 预估剩余时间(秒)
  error_msg?: string;       // 错误信息(失败时)
  result?: {
    document_id: string;
    filename: string;
    chunks_count: number;
    parse_time: number;
  }; // 处理结果(完成时)
}
```

**轮询策略**:
- 建议轮询间隔: 1秒
- 最大轮询时间: 5分钟
- 状态为 `Completed` 或 `Failed` 时停止轮询

### 3. 智能问答接口

#### POST /ask
发送问题并获取AI回答

**请求体**:
```typescript
interface AskRequest {
  question: string;        // 用户问题 (必填, 最少1个字符)
  context?: string[];     // 对话上下文 (可选)
  filter_tags?: string[]; // 标签筛选 (可选)
  top_k?: number;         // 返回结果数量 (可选, 默认5, 最大100)
}
```

**响应格式** (流式SSE):
```typescript
// 事件类型: "answer" | "source" | "done" | "error"
interface AskStreamEvent {
  event: string;
  data: string; // JSON字符串
}

// answer 事件数据
interface AnswerEvent {
  content: string;      // 回答内容片段
  is_complete: boolean; // 是否完成
}

// source 事件数据
interface SourceEvent {
  sources: Array<{
    document_name: string;
    page?: number;
    table?: string;
    score: number;
  }>;
}

// done 事件数据
interface DoneEvent {
  total_tokens: number;
  response_time: number;
}
```

**客户端处理示例**:
```typescript
const eventSource = new EventSource('/ask');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (event.type) {
    case 'answer':
      appendAnswer(data.content);
      if (data.is_complete) {
        eventSource.close();
      }
      break;
    case 'source':
      displaySources(data.sources);
      break;
    case 'error':
      handleError(data.message);
      eventSource.close();
      break;
  }
};
```

### 4. 文档检索接口

#### GET /search
语义检索文档内容

**查询参数**:
```typescript
interface SearchParams {
  q: string;              // 搜索关键词 (必填)
  filter_tags?: string[];   // 标签筛选 (可选)
  top_k?: number;         // 返回结果数量 (默认5, 最大100)
}
```

**成功响应** (200):
```typescript
interface SearchResponse {
  results: Array<{
    text: string;           // 匹配的文本内容
    source: string;         // 来源标识 [文档名, 第X页/表名]
    tags: string[];         // 关联标签
    score: number;          // 相似度分数 (0-1)
    metadata?: {
      page?: number;
      table?: string;
      chunk_id?: string;
    };
  }>;
  total: number;            // 总结果数
  query_time: number;       // 查询耗时(ms)
}
```

### 5. 标签管理接口

#### GET /tags
获取所有标签列表

**成功响应** (200):
```typescript
interface TagsResponse {
  tags: Array<{
    tag: string;           // 标签名称
    description: string;   // 标签描述
    color?: string;        // 标签颜色 (HEX)
    usage_count: number;   // 使用次数
    created_at: string;   // 创建时间
  }>;
}
```

#### POST /tags
创建新标签

**请求体**:
```typescript
interface CreateTagRequest {
  tag: string;           // 标签名称 (必填)
  description?: string;  // 标签描述 (可选)
  color?: string;        // 标签颜色 (可选, HEX格式)
}
```

#### PUT /tags/{tag}
更新标签信息

**请求体**:
```typescript
interface UpdateTagRequest {
  description?: string;  // 新描述
  color?: string;       // 新颜色
}
```

#### DELETE /tags/{tag}
删除标签

**注意事项**:
- 只能删除未被使用的标签
- 删除前会检查关联文档数量

### 6. 系统健康检查接口

#### GET /health
检查系统运行状态

**成功响应** (200):
```typescript
interface HealthResponse {
  status: 'ok' | 'degraded' | 'error';
  services: {
    database: 'connected' | 'disconnected';
    redis: 'connected' | 'disconnected';
    vector_db: 'connected' | 'disconnected';
  };
  version: string;
  timestamp: string;
}
```

## 错误码定义

| 状态码 | 错误类型 | 前端处理建议 |
|--------|----------|--------------|
| 400 | Bad Request | 显示具体错误信息，引导用户修正输入 |
| 401 | Unauthorized | 跳转到登录页面或刷新Token |
| 403 | Forbidden | 显示权限不足提示，联系管理员 |
| 404 | Not Found | 显示资源不存在提示 |
| 413 | Payload Too Large | 提示文件过大，建议压缩或分批上传 |
| 415 | Unsupported Media Type | 提示不支持的文件格式，列出支持的格式 |
| 429 | Too Many Requests | 显示请求过于频繁，稍后重试 |
| 500 | Internal Server Error | 显示服务器错误，提供重试按钮 |
| 502 | Bad Gateway | 显示服务暂时不可用，自动重试 |
| 503 | Service Unavailable | 显示服务维护中，预计恢复时间 |

## 前端错误处理规范

### 统一错误处理
```typescript
// axios 响应拦截器
axios.interceptors.response.use(
  response => response,
  error => {
    const status = error.response?.status;
    const message = error.response?.data?.message || error.message;
    
    switch (status) {
      case 413:
        ElMessage.error('文件大小不能超过50MB，请压缩后重新上传');
        break;
      case 415:
        ElMessage.error('仅支持PDF、Word、Excel、PPT格式文件');
        break;
      case 429:
        ElMessage.warning('操作过于频繁，请稍后再试');
        break;
      case 500:
      case 502:
      case 503:
        ElMessage.error('服务器暂时不可用，请稍后重试');
        break;
      default:
        ElMessage.error(message || '操作失败，请重试');
    }
    
    return Promise.reject(error);
  }
);
```

### 重试机制
```typescript
// 自动重试配置
const retryConfig = {
  retries: 3,           // 最大重试次数
  retryDelay: 1000,     // 重试间隔(ms)
  retryCondition: (error) => {
    // 只对网络错误和5xx错误重试
    return !error.response || error.response.status >= 500;
  }
};
```

## 数据缓存策略

### 缓存规则
- **文档列表**: 缓存5分钟，上传/删除操作后刷新
- **标签数据**: 缓存10分钟，标签变更后刷新
- **搜索结果**: 缓存2分钟，相同查询参数复用
- **问答历史**: 本地存储，长期保存

### 缓存实现
```typescript
// 使用 Pinia 插件实现缓存
import { createPersistedState } from 'pinia-plugin-persistedstate';

export const useDocumentStore = defineStore('document', {
  state: () => ({
    documents: [],
    lastFetchTime: 0,
  }),
  
  actions: {
    async fetchDocuments() {
      const now = Date.now();
      const cacheTimeout = 5 * 60 * 1000; // 5分钟
      
      if (now - this.lastFetchTime < cacheTimeout && this.documents.length > 0) {
        return this.documents; // 使用缓存
      }
      
      const response = await api.getDocuments();
      this.documents = response.data;
      this.lastFetchTime = now;
      return this.documents;
    }
  }
});
```

## 版本兼容性

### 浏览器支持
- Chrome ≥ 90
- Firefox ≥ 88
- Safari ≥ 14
- Edge ≥ 90

### 移动端支持
- iOS Safari ≥ 12
- Chrome for Android ≥ 90
- 主要支持平板和桌面端，移动端为基础功能

## 安全要求

### 前端安全措施
1. **XSS防护**: 所有用户输入进行转义
2. **CSRF防护**: 使用SameSite Cookie
3. **文件上传**: 客户端文件类型和大小预检查
4. **敏感信息**: 不在前端存储敏感数据

### 数据脱敏
```typescript
// 敏感信息脱敏函数
function desensitizeText(text: string, sensitiveWords: string[]): string {
  let result = text;
  sensitiveWords.forEach(word => {
    const regex = new RegExp(word, 'gi');
    result = result.replace(regex, '*'.repeat(word.length));
  });
  return result;
}
```