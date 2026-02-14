<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">文件上传</h1>
      <p class="text-gray-600">支持 PDF、DOC、DOCX、XLS、XLSX、PPT、PPTX 格式</p>
    </div>

    <!-- 上传区域 -->
    <div class="mb-8">
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        drag
        :action="uploadAction"
        :headers="uploadHeaders"
        :data="uploadData"
        :multiple="true"
        :limit="10"
        :file-list="fileList"
        :accept="acceptFileTypes"
        :before-upload="beforeUpload"
        :on-progress="handleProgress"
        :on-success="handleSuccess"
        :on-error="handleError"
        :on-remove="handleRemove"
        :on-exceed="handleExceed"
        :auto-upload="false"
      >
        <el-icon class="el-icon--upload" size="48"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            <p class="text-sm text-gray-500 mb-2">
              支持格式：PDF、DOC、DOCX、XLS、XLSX、PPT、PPTX
            </p>
            <p class="text-sm text-gray-500">
              单个文件不超过 50MB，最多可同时上传 10 个文件
            </p>
          </div>
        </template>
      </el-upload>

      <!-- 上传按钮 -->
      <div class="mt-4 flex justify-center space-x-4">
        <el-button 
          type="primary" 
          @click="submitUpload"
          :loading="isUploading"
          :disabled="fileList.length === 0"
        >
          <el-icon class="mr-2"><Upload /></el-icon>
          开始上传
        </el-button>
        <el-button 
          @click="clearFiles"
          :disabled="fileList.length === 0"
        >
          清空列表
        </el-button>
      </div>
    </div>

    <!-- 上传状态列表 -->
    <div v-if="uploadTasks.length > 0" class="mb-8">
      <h3 class="text-lg font-medium text-gray-800 mb-4">上传进度</h3>
      <div class="space-y-4">
        <div 
          v-for="task in uploadTasks" 
          :key="task.taskId"
          class="bg-white rounded-lg border border-gray-200 p-4"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center space-x-3">
              <el-icon size="20" :class="getFileIconColor(task.fileName)">
                <component :is="getFileIcon(getFileType(task.fileName))" />
              </el-icon>
              <div>
                <p class="text-sm font-medium text-gray-800">{{ task.fileName }}</p>
                <p class="text-xs text-gray-500">{{ formatFileSize(task.fileSize) }}</p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <el-tag 
                :type="getUploadStatusType(task.status) as any" 
                size="small"
                class="capitalize"
              >
                {{ getUploadStatusText(task.status) }}
              </el-tag>
              <el-button
                v-if="task.status === 'failed'"
                type="primary"
                link
                size="small"
                @click="retryUpload(task)"
              >
                重试
              </el-button>
            </div>
          </div>

          <!-- 进度条 -->
          <div v-if="task.status === 'uploading' || task.status === 'processing'" class="mb-2">
            <el-progress 
              :percentage="task.progress" 
              :status="getProgressStatus(task.status)"
              :stroke-width="8"
              :text-inside="true"
            />
          </div>

          <!-- 状态信息 -->
          <div v-if="task.statusMessage" class="text-xs text-gray-600">
            {{ task.statusMessage }}
          </div>

          <!-- 错误信息 -->
          <div v-if="task.error" class="text-xs text-red-600 mt-2">
            {{ task.error }}
          </div>
        </div>
      </div>
    </div>

    <!-- 上传历史 -->
    <div>
      <h3 class="text-lg font-medium text-gray-800 mb-4">最近上传</h3>
      <el-table :data="uploadHistory" style="width: 100%">
        <el-table-column prop="fileName" label="文件名" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center space-x-2">
              <el-icon size="16" :class="getFileIconColor(row.fileName)">
                <component :is="getFileIcon(getFileType(row.fileName))" />
              </el-icon>
              <span class="text-sm">{{ row.fileName }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="fileSize" label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.fileSize) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getUploadStatusType(row.status) as any" 
              size="small"
              class="capitalize"
            >
              {{ getUploadStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="uploadTime" label="上传时间" width="150" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed'"
              type="primary"
              link
              size="small"
              @click="viewDocument(row)"
            >
              查看
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="deleteHistory(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadProps, UploadUserFile } from 'element-plus'
import {
  UploadFilled,
  Upload,
  Document,
  DocumentCopy,
  Tickets,
  Notebook
} from '@element-plus/icons-vue'

interface UploadTask {
  taskId: string
  fileName: string
  fileSize: number
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  progress: number
  statusMessage: string
  error?: string
}

interface UploadHistoryItem {
  id: string
  fileName: string
  fileSize: number
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed'
  uploadTime: string
}

// 文件类型配置
const acceptFileTypes = '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx'
const maxFileSize = 50 * 1024 * 1024 // 50MB

// 上传相关状态
const uploadRef = ref()
const fileList = ref<UploadUserFile[]>([])
const isUploading = ref(false)
const uploadTasks = reactive<UploadTask[]>([])
const uploadHistory = ref<UploadHistoryItem[]>([
  {
    id: '1',
    fileName: '医疗质量管理规范.pdf',
    fileSize: 2345678,
    status: 'completed',
    uploadTime: '2024-01-15 14:30'
  },
  {
    id: '2',
    fileName: '2024年度质量报告.docx',
    fileSize: 1876543,
    status: 'completed',
    uploadTime: '2024-01-15 10:15'
  },
  {
    id: '3',
    fileName: '质量指标统计表.xlsx',
    fileSize: 856432,
    status: 'completed',
    uploadTime: '2024-01-14 16:45'
  }
])

// 上传配置
const uploadAction = '/api/upload'
const uploadHeaders = {
  'Authorization': 'Bearer ' + localStorage.getItem('token')
}
const uploadData = {
  userId: '1'
}

// 文件上传前检查
const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  // 检查文件类型
  const fileType = file.name.split('.').pop()?.toLowerCase()
  const allowedTypes = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
  
  if (!fileType || !allowedTypes.includes(fileType)) {
    ElMessage.error('不支持的文件格式')
    return false
  }

  // 检查文件大小
  if (file.size > maxFileSize) {
    ElMessage.error('文件大小不能超过 50MB')
    return false
  }

  return true
}

// 处理上传进度
const handleProgress: UploadProps['onProgress'] = (event, file) => {
  const task = uploadTasks.find(t => t.fileName === file.name)
  if (task) {
    task.status = 'uploading'
    task.progress = Math.round(event.percent)
    task.statusMessage = `上传中... ${task.progress}%`
  }
}

// 处理上传成功
const handleSuccess: UploadProps['onSuccess'] = (_response, file) => {
  const task = uploadTasks.find(t => t.fileName === file.name)
  if (task) {
    task.status = 'processing'
    task.progress = 100
    task.statusMessage = '文件解析中...'
    
    // 模拟解析过程
    setTimeout(() => {
      task.status = 'completed'
      task.statusMessage = '上传完成'
      
      // 添加到历史记录
      uploadHistory.value.unshift({
        id: Date.now().toString(),
        fileName: file.name,
        fileSize: file.size || 0,
        status: 'completed',
        uploadTime: new Date().toLocaleString('zh-CN')
      })
      
      ElMessage.success('文件上传成功')
    }, 3000)
  }
}

// 处理上传失败
const handleError: UploadProps['onError'] = (error, file) => {
  const task = uploadTasks.find(t => t.fileName === file.name)
  if (task) {
    task.status = 'failed'
    task.error = error.message || '上传失败'
    task.statusMessage = '上传失败'
  }
  ElMessage.error('文件上传失败')
}

// 处理文件移除
const handleRemove: UploadProps['onRemove'] = (file) => {
  const index = uploadTasks.findIndex(t => t.fileName === file.name)
  if (index > -1) {
    uploadTasks.splice(index, 1)
  }
}

// 处理文件超出限制
const handleExceed: UploadProps['onExceed'] = () => {
  ElMessage.warning('最多只能上传 10 个文件')
}

// 开始上传
const submitUpload = () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }

  isUploading.value = true
  
  // 创建上传任务
  fileList.value.forEach(file => {
    const task: UploadTask = {
      taskId: Date.now().toString() + Math.random(),
      fileName: file.name,
      fileSize: file.size || 0,
      status: 'pending',
      progress: 0,
      statusMessage: '等待上传'
    }
    uploadTasks.push(task)
  })

  // 开始上传
  uploadRef.value?.submit()
  
  setTimeout(() => {
    isUploading.value = false
  }, 1000)
}

// 清空文件列表
const clearFiles = () => {
  fileList.value = []
  uploadTasks.length = 0
  uploadRef.value?.clearFiles()
}

// 重试上传
const retryUpload = (task: UploadTask) => {
  task.status = 'pending'
  task.progress = 0
  task.statusMessage = '等待重试'
  task.error = undefined
  
  // 重新添加到文件列表
  const file = fileList.value.find(f => f.name === task.fileName)
  if (file) {
    setTimeout(() => {
      // 模拟重试上传
      task.status = 'uploading'
      task.progress = 50
      task.statusMessage = '重新上传中...'
      
      setTimeout(() => {
        task.status = 'completed'
        task.progress = 100
        task.statusMessage = '上传完成'
        ElMessage.success('文件重传成功')
      }, 2000)
    }, 1000)
  }
}

// 查看文档
const viewDocument = (row: UploadHistoryItem) => {
  ElMessage.info(`查看文档: ${row.fileName}`)
}

// 删除历史记录
const deleteHistory = async (row: UploadHistoryItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${row.fileName}" 的记录吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = uploadHistory.value.findIndex(item => item.id === row.id)
    if (index > -1) {
      uploadHistory.value.splice(index, 1)
    }
    ElMessage.success('删除成功')
  } catch {
    // 用户取消删除
  }
}

// 工具函数
const getFileType = (fileName: string): string => {
  return fileName.split('.').pop()?.toLowerCase() || ''
}

const getFileIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    pdf: Document,
    doc: DocumentCopy,
    docx: DocumentCopy,
    xls: Tickets,
    xlsx: Tickets,
    ppt: Notebook,
    pptx: Notebook
  }
  return iconMap[type] || Document
}

const getFileIconColor = (fileName: string) => {
  const type = getFileType(fileName)
  const colorMap: Record<string, string> = {
    pdf: 'text-red-600',
    doc: 'text-blue-600',
    docx: 'text-blue-600',
    xls: 'text-green-600',
    xlsx: 'text-green-600',
    ppt: 'text-orange-600',
    pptx: 'text-orange-600'
  }
  return colorMap[type] || 'text-gray-600'
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getUploadStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    pending: 'info',
    uploading: 'primary',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getUploadStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    pending: '等待中',
    uploading: '上传中',
    processing: '解析中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || status
}

const getProgressStatus = (status: string) => {
  return status === 'failed' ? 'exception' : undefined
}
</script>

<style scoped>
.upload-container {
  @apply p-6;
}

.upload-demo :deep(.el-upload-dragger) {
  @apply w-full h-48 flex flex-col items-center justify-center;
}

.upload-demo :deep(.el-upload-dragger:hover) {
  @apply border-primary-500;
}

:deep(.el-progress-bar__outer) {
  @apply bg-gray-200;
}

:deep(.el-progress-bar__inner) {
  @apply bg-primary-500;
}
</style>