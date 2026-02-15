<template>
  <div class="upload-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">文件上传</h1>
      <p class="text-gray-600">支持 PDF、DOC、DOCX、XLS、XLSX、PPT、PPTX 格式，单个文件不超过 50MB</p>
    </div>

    <!-- 拖拽上传区域 -->
    <div class="upload-area mb-8">
      <div 
        class="upload-dropzone"
        :class="{ 
          'is-dragover': isDragOver,
          'is-uploading': isUploading 
        }"
        @drop="handleDrop"
        @dragover="handleDragOver"
        @dragleave="handleDragLeave"
        @click="triggerFileSelect"
      >
        <div class="upload-content">
          <el-icon class="upload-icon" size="64">
            <UploadFilled />
          </el-icon>
          <div class="upload-text">
            <p class="upload-title">拖拽文件到此处上传</p>
            <p class="upload-subtitle">或者 <em>点击选择文件</em></p>
          </div>
          <div class="upload-info">
            <p class="text-sm text-gray-500">
              支持格式：PDF、DOC、DOCX、XLS、XLSX、PPT、PPTX
            </p>
            <p class="text-sm text-gray-500">
              单个文件不超过 50MB，最多可同时上传 {{ maxConcurrentFiles }} 个文件
            </p>
          </div>
        </div>
        <input
          ref="fileInputRef"
          type="file"
          multiple
          :accept="acceptFileTypes"
          @change="handleFileSelect"
          class="file-input"
        />
      </div>

      <!-- 上传控制按钮 -->
      <div class="upload-controls" v-if="hasFiles">
        <el-button 
          type="primary" 
          @click="startUpload"
          :loading="isUploading"
          :disabled="!canStartUpload"
          size="large"
        >
          <el-icon class="mr-2"><Upload /></el-icon>
          开始上传 ({{ pendingFilesCount }})
        </el-button>
        <el-button 
          @click="clearAllFiles"
          :disabled="!hasFiles || isUploading"
          size="large"
        >
          清空列表
        </el-button>
      </div>
    </div>

    <!-- 上传文件列表 -->
    <div class="upload-files-section" v-if="hasFiles">
      <div class="section-header">
        <h3 class="text-lg font-medium text-gray-800">上传文件列表</h3>
        <div class="file-stats">
          <span class="text-sm text-gray-500">
            总计 {{ totalFiles }} 个文件，{{ formatFileSize(totalSize) }}
          </span>
        </div>
      </div>

      <div class="files-list">
        <div 
          v-for="file in uploadFiles" 
          :key="file.id"
          class="file-item"
          :class="getFileItemClass(file)"
        >
          <!-- 文件图标 -->
          <div class="file-icon">
            <el-icon :size="32" :color="getFileColor(file.file.name)">
              <component :is="getFileIcon(file.file.name)" />
            </el-icon>
          </div>

          <!-- 文件信息 -->
          <div class="file-info">
            <div class="file-name">{{ file.file.name }}</div>
            <div class="file-meta">
              <span class="file-size">{{ formatFileSize(file.file.size) }}</span>
              <span class="file-type">{{ getFileExtension(file.file.name).toUpperCase() }}</span>
            </div>
            <div v-if="file.error" class="file-error">
              <el-icon size="12"><Warning /></el-icon>
              {{ file.error }}
            </div>
          </div>

          <!-- 进度显示 -->
          <div class="file-progress" v-if="file.status !== 'pending'">
            <el-progress
              :percentage="file.progress"
              :status="getProgressStatus(file.status)"
              :stroke-width="6"
              :show-text="file.status !== 'processing'"
            />
            <div v-if="file.currentStep" class="progress-step">
              {{ file.currentStep }}
            </div>
            <div v-if="file.estimatedTime" class="progress-time">
              预计剩余时间: {{ formatDuration(file.estimatedTime) }}
            </div>
          </div>

          <!-- 状态标签 -->
          <div class="file-status">
            <el-tag 
              :type="getStatusType(file.status) as any" 
              size="small"
              :effect="file.status === 'completed' ? 'light' : 'plain'"
            >
              <el-icon v-if="file.status === 'uploading' || file.status === 'processing'" size="12" class="animate-spin">
                <Loading />
              </el-icon>
              {{ getStatusText(file.status) }}
            </el-tag>
          </div>

          <!-- 操作按钮 -->
          <div class="file-actions">
            <el-button
              v-if="file.status === 'failed'"
              type="primary"
              link
              size="small"
              @click="retryFile(file)"
            >
              重试
            </el-button>
            <el-button
              v-if="file.status === 'pending' || file.status === 'failed'"
              type="danger"
              link
              size="small"
              @click="removeFile(file)"
            >
              删除
            </el-button>
            <el-button
              v-if="file.status === 'completed' && file.result?.documentId"
              type="primary"
              link
              size="small"
              @click="viewDocument(file)"
            >
              查看
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传历史 -->
    <div class="upload-history-section" v-if="completedUploads.length > 0">
      <div class="section-header">
        <h3 class="text-lg font-medium text-gray-800">上传历史</h3>
        <el-button 
          type="primary" 
          link 
          size="small"
          @click="clearHistory"
        >
          清空历史
        </el-button>
      </div>

      <el-table :data="completedUploads" style="width: 100%" stripe>
        <el-table-column label="文件" min-width="250">
          <template #default="{ row }">
            <div class="flex items-center space-x-3">
              <el-icon :size="24" :color="getFileColor(row.file.name)">
                <component :is="getFileIcon(row.file.name)" />
              </el-icon>
              <div>
                <div class="text-sm font-medium">{{ row.file.name }}</div>
                <div class="text-xs text-gray-500">{{ formatFileSize(row.file.size) }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status) as any" 
              size="small"
              effect="light"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="完成时间" width="180">
          <template #default="{ row }">
            <div class="text-sm">{{ formatDateTime(row.completedAt) }}</div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-2">
              <el-button
                v-if="row.result?.documentId"
                type="primary"
                link
                size="small"
                @click="viewDocument(row)"
              >
                查看文档
              </el-button>
              <el-button
                type="danger"
                link
                size="small"
                @click="deleteHistoryItem(row)"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 空状态 -->
    <div v-if="!hasFiles && completedUploads.length === 0" class="empty-state">
      <el-icon size="64" class="text-gray-300 mb-4">
        <UploadFilled />
      </el-icon>
      <p class="text-gray-500 mb-2">还没有上传任何文件</p>
      <p class="text-sm text-gray-400">拖拽文件到上方区域或点击选择文件开始上传</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessageBox } from 'element-plus'
import { useUploadStore } from '@/stores/upload'
import { useSystemStore } from '@/stores/system'
import { formatFileSize, formatDateTime, formatDuration } from '@/utils/format'
import { getFileExtension, getFileIcon, getFileColor, validateFileType, validateFileSize } from '@/utils/file'
import type { UploadFile as UploadFileType } from '@/types/api'

// 图标导入
import {
  UploadFilled,
  Upload,
  Warning,
  Loading
} from '@element-plus/icons-vue'

// Store
const uploadStore = useUploadStore()
const systemStore = useSystemStore()

// 常量
const acceptFileTypes = '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx'
const maxFileSize = 50 * 1024 * 1024 // 50MB
const maxConcurrentFiles = 10

// Refs
const fileInputRef = ref<HTMLInputElement>()
const isDragOver = ref(false)

// 计算属性
const uploadFiles = computed(() => uploadStore.uploadQueue)
const completedUploads = computed(() => uploadStore.completedUploads)
const isUploading = computed(() => uploadStore.isUploading)

const hasFiles = computed(() => uploadFiles.value.length > 0)
const pendingFilesCount = computed(() => uploadStore.pendingUploads.length)
const canStartUpload = computed(() => hasFiles.value && !isUploading.value && pendingFilesCount.value > 0)

const totalFiles = computed(() => uploadFiles.value.length)
const totalSize = computed(() => 
  uploadFiles.value.reduce((sum, file) => sum + file.file.size, 0)
)

// 生命周期
onMounted(() => {
  // 可以在这里加载上传历史
})

// 拖拽处理
const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  isDragOver.value = false
  
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    processFiles(Array.from(files))
  }
}

// 文件选择
const triggerFileSelect = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement
  const files = target.files
  if (files && files.length > 0) {
    processFiles(Array.from(files))
  }
  
  // 清空input，允许重复选择相同文件
  if (target.value) {
    target.value = ''
  }
}

// 处理文件
const processFiles = (files: File[]) => {
  // 检查文件数量限制
  if (files.length > maxConcurrentFiles) {
    systemStore.addNotification({
      type: 'warning',
      title: '文件数量过多',
      message: `一次最多只能上传 ${maxConcurrentFiles} 个文件`,
      read: false
    })
    files = files.slice(0, maxConcurrentFiles)
  }
  
  // 验证每个文件
  const validFiles: File[] = []
  const invalidFiles: string[] = []
  
  files.forEach(file => {
    // 验证文件类型
    if (!validateFileType(file, acceptFileTypes.split(','))) {
      invalidFiles.push(`${file.name}: 不支持的文件格式`)
      return
    }
    
    // 验证文件大小
    if (!validateFileSize(file, maxFileSize)) {
      invalidFiles.push(`${file.name}: 文件大小超过50MB限制`)
      return
    }
    
    validFiles.push(file)
  })
  
  // 显示无效文件警告
  if (invalidFiles.length > 0) {
    systemStore.addNotification({
      type: 'warning',
      title: '部分文件无法上传',
      message: invalidFiles.join('；'),
      read: false
    })
  }
  
  // 添加有效文件到上传队列
  if (validFiles.length > 0) {
    uploadStore.addFiles(validFiles)
    
    systemStore.addNotification({
      type: 'success',
      title: '文件添加成功',
      message: `已添加 ${validFiles.length} 个文件到上传队列`,
      read: false
    })
  }
}

// 上传控制
const startUpload = async () => {
  if (!canStartUpload.value) return
  
  try {
    await uploadStore.processUploadQueue()
    
    systemStore.addNotification({
      type: 'success',
      title: '上传开始',
      message: '文件上传已开始，请耐心等待',
      read: false
    })
  } catch (error) {
    systemStore.addNotification({
      type: 'error',
      title: '上传失败',
      message: error instanceof Error ? error.message : '上传过程中发生错误',
      read: false
    })
  }
}

const clearAllFiles = () => {
  uploadStore.clearAllUploads()
  
  systemStore.addNotification({
    type: 'info',
    title: '列表已清空',
    message: '已清空所有上传文件',
    read: false
  })
}

// 文件操作
const removeFile = (file: UploadFileType) => {
  try {
    // 从上传队列或历史记录中移除文件
    uploadStore.removeFile(file.id)
    
    systemStore.addNotification({
      type: 'info',
      title: '文件已移除',
      message: `已从列表中移除 ${file.file.name}`,
      read: false
    })
  } catch (error) {
    systemStore.addNotification({
      type: 'error',
      title: '移除失败',
      message: error instanceof Error ? error.message : '移除文件失败',
      read: false
    })
  }
}

const retryFile = async (file: UploadFileType) => {
  try {
    // 重置文件状态
    file.status = 'pending'
    file.progress = 0
    file.error = undefined
    file.currentStep = undefined
    
    // 重新处理上传队列
    await uploadStore.processUploadQueue()
    
    systemStore.addNotification({
      type: 'success',
      title: '重试开始',
      message: `正在重新上传 ${file.file.name}`,
      read: false
    })
  } catch (error) {
    systemStore.addNotification({
      type: 'error',
      title: '重试失败',
      message: error instanceof Error ? error.message : '重试上传失败',
      read: false
    })
  }
}

// 文档查看
const viewDocument = (file: UploadFileType) => {
  if (file.result?.documentId) {
    // 跳转到文档详情页
    // router.push(`/system/documents/${file.result.documentId}`)
    systemStore.addNotification({
      type: 'info',
      title: '功能开发中',
      message: '文档详情功能正在开发中',
      read: false
    })
  }
}

// 历史记录操作
const clearHistory = () => {
  ElMessageBox.confirm(
    '确定要清空所有上传历史记录吗？',
    '清空历史',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    uploadStore.clearCompletedUploads()
    
    systemStore.addNotification({
      type: 'success',
      title: '历史已清空',
      message: '已清空所有上传历史记录',
      read: false
    })
  }).catch(() => {
    // 用户取消
  })
}

const deleteHistoryItem = (file: UploadFileType) => {
  ElMessageBox.confirm(
    `确定要删除 "${file.file.name}" 的上传记录吗？`,
    '删除记录',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    try {
      // 从历史记录中删除文件
      uploadStore.removeFile(file.id)
      
      systemStore.addNotification({
        type: 'success',
        title: '记录已删除',
        message: '已从历史记录中删除',
        read: false
      })
    } catch (error) {
      systemStore.addNotification({
        type: 'error',
        title: '删除失败',
        message: error instanceof Error ? error.message : '删除记录失败',
        read: false
      })
    }
  }).catch(() => {
    // 用户取消
  })
}

// 工具函数
const getFileItemClass = (file: UploadFileType) => {
  return {
    'is-failed': file.status === 'failed',
    'is-completed': file.status === 'completed',
    'is-processing': file.status === 'processing' || file.status === 'uploading'
  }
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    pending: 'info',
    uploading: 'primary',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: string) => {
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
  @apply p-6 max-w-6xl mx-auto;
}

.page-header {
  @apply mb-8;
}

.upload-area {
  @apply mb-8;
}

.upload-dropzone {
  @apply relative border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer transition-all duration-300;
  @apply hover:border-blue-400 hover:bg-blue-50;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-dropzone.is-dragover {
  @apply border-blue-500 bg-blue-50;
  @apply border-solid;
}

.upload-dropzone.is-uploading {
  @apply border-gray-300 bg-gray-50;
  @apply cursor-not-allowed;
}

.upload-dropzone.is-uploading .upload-content {
  pointer-events: none;
  opacity: 0.7;
}

.upload-content {
  @apply space-y-4;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.upload-icon {
  @apply text-gray-400 mx-auto;
}

.upload-dropzone:hover .upload-icon {
  @apply text-blue-500;
}

.upload-title {
  @apply text-lg font-medium text-gray-700;
}

.upload-subtitle {
  @apply text-sm text-gray-500;
}

.upload-subtitle em {
  @apply text-blue-600 not-italic font-medium;
}

.upload-info {
  @apply space-y-1;
}

.upload-controls {
  @apply flex justify-center space-x-4 mt-6;
}

.file-input {
  @apply absolute inset-0 w-full h-full opacity-0 cursor-pointer;
}

.upload-files-section {
  @apply mb-8;
}

.section-header {
  @apply flex justify-between items-center mb-4;
}

.file-stats {
  @apply text-sm text-gray-500;
}

.files-list {
  @apply space-y-3;
}

.file-item {
  @apply bg-white rounded-lg border border-gray-200 p-4;
  @apply flex items-center space-x-4;
  @apply transition-all duration-200;
}

.file-item:hover {
  @apply shadow-md;
}

.file-item.is-failed {
  @apply border-red-200 bg-red-50;
}

.file-item.is-completed {
  @apply border-green-200 bg-green-50;
}

.file-item.is-processing {
  @apply border-blue-200 bg-blue-50;
}

.file-icon {
  @apply flex-shrink-0;
}

.file-info {
  @apply flex-1 min-w-0;
}

.file-name {
  @apply text-sm font-medium text-gray-800 truncate;
}

.file-meta {
  @apply flex items-center space-x-2 text-xs text-gray-500;
}

.file-size {
  @apply text-gray-500;
}

.file-type {
  @apply text-gray-400;
}

.file-error {
  @apply flex items-center space-x-1 text-xs text-red-600 mt-1;
}

.file-progress {
  @apply flex-1 max-w-xs;
}

.progress-step {
  @apply text-xs text-gray-500 mt-1;
}

.progress-time {
  @apply text-xs text-gray-400 mt-1;
}

.file-status {
  @apply flex-shrink-0;
}

.file-actions {
  @apply flex items-center space-x-2;
}

.upload-history-section {
  @apply mb-8;
}

.empty-state {
  @apply text-center py-12;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>