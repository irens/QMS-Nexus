<template>
  <div class="p-6">
    <!-- 页面头部 -->
    <div class="mb-6">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/documents' }">文档管理</el-breadcrumb-item>
        <el-breadcrumb-item>文档详情</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 文档信息卡片 -->
    <div class="bg-white rounded-lg shadow-sm border p-6 mb-6">
      <div class="flex items-start justify-between mb-4">
        <div class="flex items-center space-x-4">
          <el-icon size="32" :class="getFileIconColor(document?.fileType)">
            <component :is="getFileIcon(document?.fileType)" />
          </el-icon>
          <div>
            <h1 class="text-xl font-bold text-gray-800">{{ document?.filename }}</h1>
            <p class="text-sm text-gray-500">
              大小: {{ formatFileSize(document?.fileSize || 0) }} | 
              上传时间: {{ formatDate(document?.uploadTime) }} | 
              状态: <el-tag :type="getStatusType(document?.status) as any" size="small">{{ getStatusText(document?.status) }}</el-tag>
            </p>
          </div>
        </div>
        <div class="flex space-x-2">
          <el-button type="primary" @click="downloadDocument">
            <el-icon class="mr-1"><Download /></el-icon>
            下载
          </el-button>
          <el-button @click="shareDocument">
            <el-icon class="mr-1"><Share /></el-icon>
            分享
          </el-button>
          <el-dropdown>
            <el-button>
              更多<el-icon class="ml-1"><CaretBottom /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="editTags">
                  <el-icon><Edit /></el-icon>
                  编辑标签
                </el-dropdown-item>
                <el-dropdown-item @click="previewDocument">
                  <el-icon><View /></el-icon>
                  预览
                </el-dropdown-item>
                <el-dropdown-item divided @click="deleteDocument">
                  <el-icon><Delete /></el-icon>
                  删除文档
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 标签 -->
      <div class="mb-4">
        <p class="text-sm text-gray-600 mb-2">标签:</p>
        <div class="flex flex-wrap gap-2">
          <el-tag
              v-for="tag in document?.tags"
              :key="tag"
              :type="getTagType(tag) as any"
              size="small"
              closable
              @close="removeTag(tag)"
            >
            {{ getTagText(tag) }}
          </el-tag>
          <el-button size="small" @click="addTag" v-if="!showTagInput">
            <el-icon class="mr-1"><Plus /></el-icon>
            添加标签
          </el-button>
          <el-select
            v-else
            v-model="newTag"
            size="small"
            placeholder="选择标签"
            class="w-32"
            @change="handleAddTag"
            @blur="showTagInput = false"
          >
            <el-option
              v-for="tag in availableTags"
              :key="tag.value"
              :label="tag.label"
              :value="tag.value"
            />
          </el-select>
        </div>
      </div>

      <!-- 文档元信息 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <p class="text-gray-500">文件类型</p>
          <p class="font-medium">{{ document?.fileType?.toUpperCase() }}</p>
        </div>
        <div>
          <p class="text-gray-500">页数</p>
          <p class="font-medium">{{ document?.metadata?.pages || '未知' }}</p>
        </div>
        <div>
          <p class="text-gray-500">作者</p>
          <p class="font-medium">{{ document?.metadata?.author || '未知' }}</p>
        </div>
        <div>
          <p class="text-gray-500">创建时间</p>
          <p class="font-medium">{{ formatDate(document?.metadata?.creationDate) || '未知' }}</p>
        </div>
      </div>
    </div>

    <!-- 文档内容预览 -->
    <div class="bg-white rounded-lg shadow-sm border p-6 mb-6" v-if="document?.status === 'Completed'">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-800">内容预览</h2>
        <div class="flex space-x-2">
          <el-input
            v-model="searchQuery"
            placeholder="在文档中搜索..."
            clearable
            size="small"
            class="w-64"
            @keyup.enter="searchInDocument"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button size="small" @click="togglePreview">
            {{ showPreview ? '隐藏预览' : '显示预览' }}
          </el-button>
        </div>
      </div>

      <!-- 预览内容 -->
      <div v-if="showPreview && previewContent" class="border rounded-lg p-4 bg-gray-50 max-h-96 overflow-y-auto">
        <div class="prose prose-sm max-w-none" v-html="previewContent"></div>
      </div>
      
      <div v-else-if="showPreview && loadingPreview" class="text-center py-8">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p class="text-gray-500 mt-2">正在加载预览...</p>
      </div>
      
      <div v-else-if="showPreview" class="text-center py-8 text-gray-500">
        <el-icon size="32"><Document /></el-icon>
        <p class="mt-2">预览内容不可用</p>
      </div>
    </div>

    <!-- 相关文档 -->
    <div class="bg-white rounded-lg shadow-sm border p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-800">相关文档</h2>
        <el-button link type="primary" @click="loadMoreRelated">查看更多</el-button>
      </div>
      
      <div v-if="relatedDocuments.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="doc in relatedDocuments"
          :key="doc.id"
          class="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
          @click="viewRelatedDocument(doc)"
        >
          <div class="flex items-center space-x-3 mb-2">
            <el-icon size="20" :class="getFileIconColor(doc.fileType)">
              <component :is="getFileIcon(doc.fileType)" />
            </el-icon>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-800 truncate">{{ doc.filename }}</p>
              <p class="text-xs text-gray-500">{{ formatFileSize(doc.fileSize) }}</p>
            </div>
          </div>
          <div class="flex flex-wrap gap-1">
            <el-tag
                v-for="tag in doc.tags.slice(0, 2)"
                :key="tag"
                :type="getTagType(tag) as any"
                size="small"
              >
              {{ getTagText(tag) }}
            </el-tag>
            <el-tag v-if="doc.tags.length > 2" size="small">+{{ doc.tags.length - 2 }}</el-tag>
          </div>
        </div>
      </div>
      
      <div v-else-if="loadingRelated" class="text-center py-8">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p class="text-gray-500 mt-2">正在加载相关文档...</p>
      </div>
      
      <div v-else class="text-center py-8 text-gray-500">
        <el-icon size="32"><Document /></el-icon>
        <p class="mt-2">暂无相关文档</p>
      </div>
    </div>

    <!-- 编辑标签对话框 -->
    <el-dialog
      v-model="editTagsDialog.visible"
      title="编辑标签"
      width="500px"
    >
      <div class="space-y-4">
        <div>
          <p class="text-sm text-gray-600 mb-2">文件名：{{ document?.filename }}</p>
          <p class="text-sm text-gray-600">当前标签：</p>
          <div class="flex flex-wrap gap-2 mt-2">
            <el-tag
              v-for="tag in editTagsDialog.currentTags"
              :key="tag"
              closable
              @close="removeEditTag(tag)"
            >
              {{ getTagText(tag) }}
            </el-tag>
          </div>
        </div>
        
        <div>
          <p class="text-sm text-gray-600 mb-2">添加标签：</p>
          <el-select
            v-model="editTagsDialog.newTags"
            multiple
            filterable
            allow-create
            placeholder="选择或输入新标签"
            class="w-full"
          >
            <el-option
              v-for="tag in availableTags"
              :key="tag.value"
              :label="tag.label"
              :value="tag.value"
            />
          </el-select>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editTagsDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="saveTags">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useDocumentStore } from '@/stores/document'
import { formatFileSize, formatDate } from '@/utils/format'
import {
  Document,
  Download,
  Share,
  Edit,
  Delete,
  CaretBottom,
  View,
  Search,
  Loading,
  Plus
} from '@element-plus/icons-vue'
import type { Document as DocumentType } from '@/types/api'

const route = useRoute()
const router = useRouter()
const documentStore = useDocumentStore()

// 状态
const document = ref<DocumentType | null>(null)
const relatedDocuments = ref<DocumentType[]>([])
const loadingDocument = ref(false)
const loadingRelated = ref(false)
const loadingPreview = ref(false)
const previewContent = ref('')
const showPreview = ref(false)
const searchQuery = ref('')
const showTagInput = ref(false)
const newTag = ref('')

// 编辑标签对话框
const editTagsDialog = reactive({
  visible: false,
  currentTags: [] as string[],
  newTags: [] as string[]
})

// 可用标签
const availableTags = [
  { value: 'quality', label: '质量管理' },
  { value: 'medical', label: '医疗规范' },
  { value: 'training', label: '培训资料' },
  { value: 'policy', label: '政策法规' },
  { value: 'standard', label: '标准规范' }
]

// 获取文档详情
const fetchDocument = async () => {
  const documentId = route.params.id as string
  if (!documentId) return
  
  try {
    loadingDocument.value = true
    const doc = await documentStore.fetchDocument(documentId)
    if (doc) {
      document.value = doc
      // 获取相关文档
      fetchRelatedDocuments()
      // 获取预览内容
      fetchPreviewContent()
    } else {
      ElMessage.error('获取文档详情失败')
      router.push('/system/documents')
    }
  } catch (error) {
    ElMessage.error('获取文档详情失败')
    router.push('/system/documents')
  } finally {
    loadingDocument.value = false
  }
}

// 获取相关文档
const fetchRelatedDocuments = async () => {
  if (!document.value) return
  
  try {
    loadingRelated.value = true
    const related = await documentStore.getRelatedDocuments(document.value.id, 6)
    relatedDocuments.value = related
  } catch (error) {
    console.error('获取相关文档失败:', error)
  } finally {
    loadingRelated.value = false
  }
}

// 获取预览内容
const fetchPreviewContent = async () => {
  if (!document.value) return
  
  try {
    loadingPreview.value = true
    const content = await documentStore.previewDocument(document.value.id)
    if (content) {
      previewContent.value = content
      showPreview.value = true
    }
  } catch (error) {
    console.error('获取预览内容失败:', error)
  } finally {
    loadingPreview.value = false
  }
}

// 文件图标相关函数
const getFileIcon = (type?: string) => {
  const iconMap: Record<string, any> = {
    pdf: Document,
    doc: Document,
    docx: Document,
    xls: Document,
    xlsx: Document,
    ppt: Document,
    pptx: Document
  }
  return iconMap[type || ''] || Document
}

const getFileIconColor = (type?: string) => {
  const colorMap: Record<string, string> = {
    pdf: 'text-red-600',
    doc: 'text-blue-600',
    docx: 'text-blue-600',
    xls: 'text-green-600',
    xlsx: 'text-green-600',
    ppt: 'text-orange-600',
    pptx: 'text-orange-600'
  }
  return colorMap[type || ''] || 'text-gray-600'
}

// 标签相关函数
const getTagType = (tag: string) => {
  const typeMap: Record<string, string> = {
    quality: 'primary',
    medical: 'success',
    training: 'warning',
    policy: 'info',
    standard: 'danger'
  }
  return typeMap[tag] || 'info'
}

const getTagText = (tag: string) => {
  const textMap: Record<string, string> = {
    quality: '质量管理',
    medical: '医疗规范',
    training: '培训资料',
    policy: '政策法规',
    standard: '标准规范'
  }
  return textMap[tag] || tag
}

// 状态相关函数
const getStatusType = (status?: string) => {
  const typeMap: Record<string, string> = {
    Processing: 'warning',
    Completed: 'success',
    Failed: 'danger'
  }
  return typeMap[status || ''] || 'info'
}

const getStatusText = (status?: string) => {
  const textMap: Record<string, string> = {
    Processing: '解析中',
    Completed: '已完成',
    Failed: '失败'
  }
  return textMap[status || ''] || '未知'
}

// 操作方法
const downloadDocument = async () => {
  if (!document.value) return
  
  try {
    const success = await documentStore.downloadDocument(document.value.id, document.value.filename)
    if (success) {
      ElMessage.success('开始下载文档')
    } else {
      ElMessage.error('下载失败')
    }
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

const shareDocument = () => {
  if (!document.value) return
  
  const shareUrl = `${window.location.origin}/documents/${document.value.id}`
  navigator.clipboard.writeText(shareUrl).then(() => {
    ElMessage.success('分享链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动复制链接')
  })
}

const editTags = () => {
  if (!document.value) return
  
  editTagsDialog.currentTags = [...document.value.tags]
  editTagsDialog.newTags = [...document.value.tags]
  editTagsDialog.visible = true
}

const previewDocument = () => {
  showPreview.value = !showPreview.value
  if (showPreview.value && !previewContent.value) {
    fetchPreviewContent()
  }
}

const deleteDocument = async () => {
  if (!document.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${document.value.filename}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const success = await documentStore.deleteDocument(document.value.id)
    if (success) {
      ElMessage.success('删除成功')
      router.push('/system/documents')
    } else {
      ElMessage.error('删除失败')
    }
  } catch {
    // 用户取消删除
  }
}

const searchInDocument = () => {
  if (!searchQuery.value || !document.value) return
  
  // 这里可以实现文档内搜索功能
  ElMessage.info(`搜索: ${searchQuery.value}`)
}

const togglePreview = () => {
  showPreview.value = !showPreview.value
}

const loadMoreRelated = () => {
  // 加载更多相关文档
  fetchRelatedDocuments()
}

const viewRelatedDocument = (doc: DocumentType) => {
  router.push(`/system/documents/${doc.id}`)
}

// 标签操作方法
const removeTag = async (tag: string) => {
  if (!document.value) return
  
  const newTags = document.value.tags.filter(t => t !== tag)
  const success = await documentStore.updateDocumentTags(document.value.id, newTags)
  if (success) {
    document.value.tags = newTags
    ElMessage.success('标签已删除')
  }
}

const addTag = () => {
  showTagInput.value = true
}

const handleAddTag = async (value: string) => {
  if (!document.value || !value) return
  
  if (document.value.tags.includes(value)) {
    ElMessage.warning('标签已存在')
    showTagInput.value = false
    newTag.value = ''
    return
  }
  
  const newTags = [...document.value.tags, value]
  const success = await documentStore.updateDocumentTags(document.value.id, newTags)
  if (success) {
    document.value.tags = newTags
    ElMessage.success('标签已添加')
  }
  
  showTagInput.value = false
  newTag.value = ''
}

const removeEditTag = (tag: string) => {
  const index = editTagsDialog.newTags.indexOf(tag)
  if (index > -1) {
    editTagsDialog.newTags.splice(index, 1)
  }
}

const saveTags = async () => {
  if (!document.value) return
  
  const success = await documentStore.updateDocumentTags(document.value.id, editTagsDialog.newTags)
  if (success) {
    document.value.tags = [...editTagsDialog.newTags]
    editTagsDialog.visible = false
    ElMessage.success('标签更新成功')
  } else {
    ElMessage.error('标签更新失败')
  }
}

// 生命周期
onMounted(() => {
  fetchDocument()
})

watch(() => route.params.id, () => {
  fetchDocument()
})
</script>

<style scoped>
.prose {
  max-width: none;
}

.prose :deep(h1) {
  @apply text-2xl font-bold mb-4;
}

.prose :deep(h2) {
  @apply text-xl font-semibold mb-3;
}

.prose :deep(h3) {
  @apply text-lg font-medium mb-2;
}

.prose :deep(p) {
  @apply mb-4 leading-relaxed;
}

.prose :deep(ul), .prose :deep(ol) {
  @apply mb-4 ml-6;
}

.prose :deep(li) {
  @apply mb-1;
}
</style>