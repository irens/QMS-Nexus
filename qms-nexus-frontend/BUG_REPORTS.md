# QMS-Nexus 前端集成测试Bug记录

**文档版本**: v1.0  
**创建日期**: 2026-02-15  
**维护人员**: QA Team  
**关联文档**: [集成测试计划和用例.md](./集成测试计划和用例.md)

---

## 📋 Bug记录清单

| Bug ID | 严重程度 | 模块 | 问题描述 | 状态 | 发现日期 | 修复日期 | 验证日期 |
|--------|---------|------|----------|------|----------|----------|----------|
| BUG-001 | P1 - 严重 | 文件上传 | 上传组件未实现API调用 | 待修复 | 2026-02-15 | - | - |
| BUG-002 | P1 - 严重 | 文档管理 | 文档列表未集成后端API | 待修复 | 2026-02-15 | - | - |
| BUG-003 | P1 - 严重 | 状态管理 | Pinia状态管理架构缺失 | 待修复 | 2026-02-15 | - | - |
| BUG-004 | P2 - 中等 | 问答功能 | 问答组件未实现API集成 | 待修复 | 2026-02-15 | - | - |
| BUG-005 | P2 - 中等 | 标签管理 | 标签管理功能未实现 | 待修复 | 2026-02-15 | - | - |
| BUG-006 | P3 - 轻微 | 路由配置 | 路由缺少权限守卫 | 待修复 | 2026-02-15 | - | - |
| BUG-007 | P3 - 轻微 | 错误处理 | 全局错误处理机制缺失 | 待修复 | 2026-02-15 | - | - |
| BUG-008 | P3 - 轻微 | 类型定义 | TypeScript类型定义不完整 | 待修复 | 2026-02-15 | - | - |

---

## 🔴 严重Bug（P1）

### BUG-001: 文件上传组件未实现API调用

**严重程度**: P1 - 严重  
**Bug类型**: API集成问题  
**发现日期**: 2026-02-15  
**发现人员**: QA Team  
**相关模块**: 文件上传  
**测试用例ID**: 4.1.1, 4.1.2, 4.1.3, 4.1.4

---

#### 问题描述

文件上传组件仅实现了前端界面和状态管理，**未实现与后端API的集成**。用户点击"开始上传"按钮后，文件仅在本地列表中状态变更，**实际上传请求从未发送到后端服务器**。

#### 复现步骤

1. **打开浏览器开发者工具**（F12）→ Network面板
2. **访问URL**: `http://localhost:5173/upload`
3. **拖拽任意PDF文件**到上传区域（如：ISO13485.pdf，2MB）
4. **点击"开始上传"按钮**
5. **观察Network面板**

#### 预期结果

- Network面板应显示POST请求到 `/api/upload` 接口
- 请求Header包含 `Content-Type: multipart/form-data`
- 请求Body包含文件数据
- 服务器返回文件ID和解析状态（status: 200）

#### 实际结果

- **Network面板无任何HTTP请求** ⚠️
- 控制台仅打印：`Upload started: [...]`
- 文件状态仅在本地变更为"上传成功"
- **实际上文件未发送到服务器** ❌

#### 问题代码定位

**文件路径**: `src/views/Upload.vue`

**问题行数**: 
- 第50-70行：`startUpload()` 函数
- 第80-100行：上传逻辑仅操作本地状态

```typescript
// === 问题代码 ===
// src/views/Upload.vue
const startUpload = () => {
  isUploading.value = true
  
  // ⚠️ 问题：仅循环处理本地状态，未调用API
  uploadFiles.value.forEach((file) => {
    if (file.status === 'pending') {
      file.status = 'uploading'
      // 模拟上传进度
      const interval = setInterval(() => {
        if (file.progress < 100) {
          file.progress += 10
        } else {
          clearInterval(interval)
          file.status = 'completed'
        }
      }, 200)
    }
  })
  
  // ⚠️ 问题：没有调用后端API
  setTimeout(() => {
    isUploading.value = false
    ElMessage.success('上传完成')
  }, 2000)
}
```

**缺失文件**:
- `src/services/upload.ts` - **API服务层未创建**
- `src/stores/upload.ts` - **状态管理Store未创建**

#### 根本原因分析

1. **缺少API服务层**：
   - 根据《FRONTEND_DEVELOPMENT_PLAN.md》第69-73页，应创建 `src/services/` 目录，包含 `upload.ts` 文件
   - 目前项目中**没有** `src/services/` 目录

2. **上传逻辑不完整**：
   - 只实现了前端UI交互和进度模拟
   - **未完成真正的HTTP请求调用**
   - 不符合《.trae/specs/frontend-development/tasks.md》中Task 2.1的要求

3. **状态管理缺失**：
   - 文件上传状态仅在组件内部管理
   - **未使用Pinia进行全局状态管理**
   - 无法在其他组件中共享上传状态

4. **错误处理缺失**：
   - 未实现网络错误处理
   - 未实现上传失败重试机制
   - 未处理后端返回的错误码

#### 影响范围

| 功能模块 | 影响程度 | 具体表现 |
|----------|---------|----------|
| 文件上传 | 严重 | 功能完全不可用 |
| 文档解析 | 严重 | 无法触发文档解析流程 |
| 知识库构建 | 严重 | 无法向知识库添加新文档 |
| 智能问答 | 严重 | 无法问答新上传文档的内容 |

#### 修改建议

**步骤1**: 创建API服务层

```typescript
// 新建文件: src/services/upload.ts
import axios from 'axios'
import type { UploadFileItem } from '@/types/upload'

/**
 * 上传文件到服务器
 * @param file - 要上传的文件对象
 * @param onProgress - 上传进度回调函数
 * @returns Promise<UploadResponse>
 */
export const uploadFile = async (
  file: File, 
  onProgress?: (progress: number) => void
): Promise<UploadFileItem> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('filename', file.name)
  formData.append('filesize', file.size.toString())
  formData.append('filetype', file.type)

  try {
    const response = await axios.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onProgress(progress)
        }
      },
      timeout: 300000 // 5分钟超时（大文件）
    })

    return response.data
  } catch (error: any) {
    // 统一的错误处理
    if (error.code === 'ECONNABORTED') {
      throw new Error('上传超时，请检查网络连接')
    }
    if (error.response?.status === 413) {
      throw new Error('文件大小超过服务器限制')
    }
    if (error.response?.status === 415) {
      throw new Error('不支持的文件格式')
    }
    throw new Error(error.response?.data?.message || '上传失败，请重试')
  }
}

/**
 * 批量上传文件
 * @param files - 文件数组
 * @param onProgress - 批量上传进度回调
 */
export const batchUploadFiles = async (
  files: File[],
  onProgress?: (index: number, progress: number) => void
): Promise<UploadFileItem[]> => {
  const results = []
  
  // 控制并发数，避免同时上传过多文件
  const concurrencyLimit = 3
  
  for (let i = 0; i < files.length; i += concurrencyLimit) {
    const batch = files.slice(i, i + concurrencyLimit)
    
    const batchPromises = batch.map((file, index) => 
      uploadFile(file, (progress) => {
        onProgress?.(i + index, progress)
      })
    )
    
    const batchResults = await Promise.allSettled(batchPromises)
    
    batchResults.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        results.push(result.value)
      } else {
        results.push({
          id: '',
          filename: batch[index].name,
          status: 'error',
          error: result.reason.message
        })
      }
    })
  }
  
  return results
}

/**
 * 检查文件是否已存在
 */
export const checkFileExists = async (filename: string): Promise<boolean> => {
  try {
    const response = await axios.get('/api/upload/check', {
      params: { filename }
    })
    return response.data.exists
  } catch (error) {
    console.error('检查文件失败:', error)
    return false
  }
}

/**
 * 获取支持的文件类型
 */
export const getSupportedFileTypes = (): string[] => {
  return [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation'
  ]
}
```

**步骤2**: 创建类型定义

```typescript
// 新建文件: src/types/upload.ts

/**
 * 上传文件项接口
 */
export interface UploadFileItem {
  id: string
  filename: string
  originalName: string
  size: number
  type: string
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error'
  progress: number
  uploadTime?: string
  error?: string
  metadata?: {
    pages?: number
    author?: string
    created?: string
  }
}

/**
 * 上传响应接口
 */
export interface UploadResponse {
  success: boolean
  data: UploadFileItem
  message?: string
}

/**
 * 批量上传响应接口
 */
export interface BatchUploadResponse {
  success: boolean
  data: UploadFileItem[]
  total: number
  successCount: number
  errorCount: number
}

/**
 * 上传配置接口
 */
export interface UploadConfig {
  maxFileSize: number // 最大文件大小（字节）
  maxConcurrentFiles: number // 最大并发上传数
  allowedTypes: string[] // 允许的文件类型
  timeout: number // 超时时间（毫秒）
}
```

**步骤3**: 创建Pinia Store

```typescript
// 新建文件: src/stores/upload.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UploadFileItem } from '@/types/upload'
import { uploadFile, batchUploadFiles } from '@/services/upload'

export const useUploadStore = defineStore('upload', () => {
  // 状态
  const uploadFiles = ref<UploadFileItem[]>([])
  const isUploading = ref(false)
  const currentUploadCount = ref(0)
  
  // 计算属性
  const pendingFiles = computed(() => 
    uploadFiles.value.filter(file => file.status === 'pending')
  )
  
  const uploadingFiles = computed(() => 
    uploadFiles.value.filter(file => file.status === 'uploading')
  )
  
  const completedFiles = computed(() => 
    uploadFiles.value.filter(file => file.status === 'completed')
  )
  
  const failedFiles = computed(() => 
    uploadFiles.value.filter(file => file.status === 'error')
  )
  
  const totalProgress = computed(() => {
    if (uploadFiles.value.length === 0) return 0
    const total = uploadFiles.value.reduce((sum, file) => sum + file.progress, 0)
    return Math.round(total / uploadFiles.value.length)
  })
  
  // 动作
  const addFile = (file: File) => {
    const uploadFileItem: UploadFileItem = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      filename: file.name,
      originalName: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      progress: 0
    }
    uploadFiles.value.push(uploadFileItem)
  }
  
  const removeFile = (id: string) => {
    const index = uploadFiles.value.findIndex(file => file.id === id)
    if (index > -1) {
      uploadFiles.value.splice(index, 1)
    }
  }
  
  const clearAllFiles = () => {
    uploadFiles.value = []
  }
  
  const startUpload = async () => {
    if (pendingFiles.value.length === 0) return
    
    isUploading.value = true
    currentUploadCount.value = pendingFiles.value.length
    
    try {
      const filesToUpload = pendingFiles.value.map(item => 
        new File([item as any], item.originalName, { type: item.type })
      )
      
      await batchUploadFiles(filesToUpload, (index, progress) => {
        const file = pendingFiles.value[index]
        if (file) {
          file.progress = progress
          file.status = progress === 100 ? 'processing' : 'uploading'
        }
      })
      
      // 更新最终状态
      pendingFiles.value.forEach(file => {
        file.status = 'completed'
        file.progress = 100
      })
      
      return { success: true }
    } catch (error: any) {
      pendingFiles.value.forEach(file => {
        file.status = 'error'
        file.error = error.message
      })
      throw error
    } finally {
      isUploading.value = false
      currentUploadCount.value = 0
    }
  }
  
  return {
    // 状态
    uploadFiles,
    isUploading,
    currentUploadCount,
    
    // 计算属性
    pendingFiles,
    uploadingFiles,
    completedFiles,
    failedFiles,
    totalProgress,
    
    // 动作
    addFile,
    removeFile,
    clearAllFiles,
    startUpload
  }
})
```

**步骤4**: 修改Upload.vue组件

```typescript
// 修改文件: src/views/Upload.vue
// 替换现有逻辑

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUploadStore } from '@/stores/upload'
import { getSupportedFileTypes } from '@/services/upload'
import type { UploadFileItem } from '@/types/upload'

// Store
const uploadStore = useUploadStore()

// 配置
const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
const MAX_CONCURRENT_FILES = 10

// 状态
const fileInputRef = ref<HTMLInputElement>()
const isDragOver = ref(false)

// 计算属性
const hasFiles = computed(() => uploadStore.uploadFiles.length > 0)
const canStartUpload = computed(() => 
  uploadStore.pendingFiles.length > 0 && !uploadStore.isUploading
)

// 文件类型验证
const isValidFileType = (file: File): boolean => {
  const supportedTypes = getSupportedFileTypes()
  return supportedTypes.includes(file.type)
}

// 文件大小验证
const isValidFileSize = (file: File): boolean => {
  return file.size <= MAX_FILE_SIZE
}

// 添加文件
const addFile = (file: File) => {
  // 验证文件类型
  if (!isValidFileType(file)) {
    ElMessage.error(`不支持的文件格式: ${file.name}`)
    return
  }
  
  // 验证文件大小
  if (!isValidFileSize(file)) {
    ElMessage.error(`文件大小超过50MB限制: ${file.name}`)
    return
  }
  
  // 添加到Store
  uploadStore.addFile(file)
}

// 拖拽处理
const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  const files = Array.from(event.dataTransfer?.files || [])
  files.forEach(addFile)
}

// 文件选择
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  files.forEach(addFile)
  
  // 清空input，允许重复选择相同文件
  target.value = ''
}

// 触发文件选择
const triggerFileSelect = () => {
  fileInputRef.value?.click()
}

// 开始上传
const startUpload = async () => {
  if (uploadStore.pendingFiles.length === 0) return
  
  try {
    await uploadStore.startUpload()
    ElMessage.success(`成功上传 ${uploadStore.completedFiles.length} 个文件`)
  } catch (error: any) {
    ElMessage.error(`上传失败: ${error.message}`)
  }
}

// 清空列表
const clearAllFiles = () => {
  ElMessageBox.confirm(
    '确定要清空所有上传文件吗？',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    uploadStore.clearAllFiles()
    ElMessage.success('已清空列表')
  }).catch(() => {
    // 用户取消
  })
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取文件图标和颜色
const getFileIcon = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'pdf': return 'Document'
    case 'doc':
    case 'docx': return 'DocumentCopy'
    case 'xls':
    case 'xlsx': return 'DataAnalysis'
    case 'ppt':
    case 'pptx': return 'DataBoard'
    default: return 'Document'
  }
}

const getFileColor = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'pdf': return '#FF6B6B'
    case 'doc':
    case 'docx': return '#4A90E2'
    case 'xls':
    case 'xlsx': return '#50C878'
    case 'ppt':
    case 'pptx': return '#FFA500'
    default: return '#999999'
  }
}
</script>
```

#### 验证步骤

1. 创建上述缺失的文件
2. 重启前端开发服务器
3. 重复测试步骤
4. 观察Network面板，确认有HTTP请求发出
5. 检查后端是否接收到文件
6. 验证文件是否能正常解析和入库

#### 相关文档

- [集成测试计划和用例.md - 测试用例4.1.1](./集成测试计划和用例.md)
- [FRONTEND_DEVELOPMENT_PLAN.md - 第69-73页](../FRONTEND_DEVELOPMENT_PLAN.md)
- [.trae/specs/frontend-development/tasks.md - Task 2.1](../.trae/specs/frontend-development/tasks.md)

---

## 🔴 下一个Bug...

[继续记录下一个Bug...]

---

**文档结束** | 最后更新: 2026-02-15
