<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">文档列表</h1>
      <p class="text-gray-600">管理和查看已上传的文档</p>
    </div>

    <!-- 搜索和筛选 -->
    <div class="mb-6">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索文档名称..."
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="selectedType" placeholder="文件类型" clearable @change="handleSearch">
            <el-option
              v-for="type in fileTypeOptions"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="selectedTag" placeholder="标签筛选" clearable @change="handleSearch">
            <el-option
              v-for="tag in availableTags"
              :key="tag.value"
              :label="tag.label"
              :value="tag.value"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            clearable
            @change="handleSearch"
          />
        </el-col>
        <el-col :span="4">
          <div class="flex space-x-2">
            <el-button type="primary" @click="handleSearch">
              <el-icon class="mr-1"><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="resetFilters">
              重置
            </el-button>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 批量操作 -->
    <div class="mb-4" v-if="selectedDocuments.length > 0">
      <el-space>
        <el-button type="danger" size="small" @click="batchDelete">
          <el-icon class="mr-1"><Delete /></el-icon>
          批量删除 ({{ selectedDocuments.length }})
        </el-button>
        <el-button type="warning" size="small" @click="batchDownload">
          <el-icon class="mr-1"><Download /></el-icon>
          批量下载
        </el-button>
        <el-button type="info" size="small" @click="batchUpdateTags">
          <el-icon class="mr-1"><Edit /></el-icon>
          批量编辑标签
        </el-button>
      </el-space>
    </div>

    <!-- 文档列表 -->
    <div class="mb-6">
      <el-table 
        :data="documents" 
        style="width: 100%"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="文档信息" min-width="250">
          <template #default="{ row }">
            <div class="flex items-center space-x-3">
              <el-icon size="20" :class="getFileIconColor(row.fileType)">
                <component :is="getFileIcon(row.fileType)" />
              </el-icon>
              <div>
                <p class="text-sm font-medium text-gray-800">{{ row.filename }}</p>
                <p class="text-xs text-gray-500">{{ formatFileSize(row.fileSize) }}</p>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="上传时间" width="150">
          <template #default="{ row }">
            {{ new Date(row.uploadTime).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        
        <el-table-column label="标签" width="200">
          <template #default="{ row }">
            <div class="flex flex-wrap gap-1">
              <el-tag
                v-for="tag in row.tags"
                :key="tag"
                size="small"
                :type="getTagType(tag) as any"
                class="cursor-pointer"
                @click="filterByTag(tag)"
              >
                {{ getTagText(tag) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status) as any" 
              size="small"
              class="capitalize"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-2">
              <el-button
                type="primary"
                link
                size="small"
                @click="viewDocument(row)"
              >
                查看
              </el-button>
              <el-button
                type="primary"
                link
                size="small"
                @click="downloadDocument(row)"
              >
                下载
              </el-button>
              <el-dropdown>
                <el-button type="primary" link size="small">
                  更多<el-icon class="ml-1"><CaretBottom /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="editTags(row)">
                      <el-icon><Edit /></el-icon>
                      编辑标签
                    </el-dropdown-item>
                    <el-dropdown-item @click="shareDocument(row)">
                      <el-icon><Share /></el-icon>
                      分享
                    </el-dropdown-item>
                    <el-dropdown-item divided @click="deleteDocument(row)">
                      <el-icon><Delete /></el-icon>
                      删除文档
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="flex justify-between items-center">
      <div class="text-sm text-gray-600">
        共 {{ totalDocuments }} 个文档，已选择 {{ selectedDocuments.length }} 个
      </div>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalDocuments"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 编辑标签对话框 -->
    <el-dialog
      v-model="editTagsDialog.visible"
      title="编辑标签"
      width="500px"
    >
      <div class="space-y-4">
        <div>
          <p class="text-sm text-gray-600 mb-2">文件名：{{ editTagsDialog.document?.filename }}</p>
          <p class="text-sm text-gray-600">当前标签：</p>
          <div class="flex flex-wrap gap-2 mt-2">
            <el-tag
              v-for="tag in editTagsDialog.document?.tags"
              :key="tag"
              closable
              @close="removeTag(tag)"
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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useDocumentStore } from '@/stores/document'
import { formatFileSize } from '@/utils/format'
import {
  Search,
  Document,
  DocumentCopy,
  Tickets,
  Notebook,
  CaretBottom,
  Edit,
  Share,
  Delete,
  Download
} from '@element-plus/icons-vue'
import type { Document as DocumentType } from '@/types/api'

const router = useRouter()
const documentStore = useDocumentStore()

// 搜索和筛选
const searchQuery = ref('')
const selectedType = ref('')
const selectedTag = ref('')
const dateRange = ref<[Date, Date] | null>(null)

// 表格数据
const selectedDocuments = ref<DocumentType[]>([])

// 编辑标签对话框
const editTagsDialog = reactive({
  visible: false,
  document: null as DocumentType | null,
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

// 文件类型选项
const fileTypeOptions = [
  { value: 'pdf', label: 'PDF文档' },
  { value: 'doc', label: 'Word文档' },
  { value: 'docx', label: 'Word文档' },
  { value: 'xls', label: 'Excel表格' },
  { value: 'xlsx', label: 'Excel表格' },
  { value: 'ppt', label: 'PPT演示文稿' },
  { value: 'pptx', label: 'PPT演示文稿' }
]

// 计算属性
const documents = computed(() => documentStore.documents)
const loading = computed(() => documentStore.loading)
const totalDocuments = computed(() => documentStore.total)
const currentPage = computed({
  get: () => documentStore.currentPage,
  set: (value) => fetchDocuments({ page: value })
})
const pageSize = computed({
  get: () => documentStore.pageSize,
  set: (value) => fetchDocuments({ pageSize: value, page: 1 })
})

// 获取文档数据
const fetchDocuments = async (query = {}) => {
  try {
    await documentStore.fetchDocuments({
      search: searchQuery.value || undefined,
      fileType: selectedType.value ? [selectedType.value] : undefined,
      tags: selectedTag.value ? [selectedTag.value] : undefined,
      ...query
    })
  } catch (error) {
    ElMessage.error('获取文档列表失败')
  }
}

// 生命周期
onMounted(() => {
  fetchDocuments()
})

// 监听筛选条件变化
watch([searchQuery, selectedType, selectedTag], () => {
  fetchDocuments({ page: 1 })
})

// 处理搜索
const handleSearch = () => {
  fetchDocuments({ page: 1 })
}

// 处理选择变化
const handleSelectionChange = (val: DocumentType[]) => {
  selectedDocuments.value = val
}

// 处理分页
const handleSizeChange = (val: number) => {
  fetchDocuments({ pageSize: val, page: 1 })
}

const handleCurrentChange = (val: number) => {
  fetchDocuments({ page: val })
}

// 按标签筛选
const filterByTag = (tag: string) => {
  selectedTag.value = tag
  handleSearch()
}

// 获取文件图标
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

// 获取文件图标颜色
const getFileIconColor = (type: string) => {
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

// 获取标签类型
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

// 获取标签文本
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

// 获取状态类型
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    Processing: 'warning',
    Completed: 'success',
    Failed: 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    Processing: '解析中',
    Completed: '已完成',
    Failed: '失败'
  }
  return textMap[status] || '未知'
}

// 查看文档
const viewDocument = (row: DocumentType) => {
  router.push(`/system/documents/${row.id}`)
}

// 下载文档
const downloadDocument = async (row: DocumentType) => {
  try {
    const success = await documentStore.downloadDocument(row.id, row.filename)
    if (success) {
      ElMessage.success(`开始下载: ${row.filename}`)
    } else {
      ElMessage.error('下载失败')
    }
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// 编辑标签
const editTags = (row: DocumentType) => {
  editTagsDialog.document = row
  editTagsDialog.newTags = [...row.tags]
  editTagsDialog.visible = true
}

// 分享文档
const shareDocument = (row: DocumentType) => {
  const shareUrl = `${window.location.origin}/documents/${row.id}`
  navigator.clipboard.writeText(shareUrl).then(() => {
    ElMessage.success('分享链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动复制链接')
  })
}

// 删除文档
const deleteDocument = async (row: DocumentType) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${row.filename}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const success = await documentStore.deleteDocument(row.id)
    if (success) {
      ElMessage.success('删除成功')
    } else {
      ElMessage.error('删除失败')
    }
  } catch {
    // 用户取消删除
  }
}

// 移除标签
const removeTag = (tag: string) => {
  if (editTagsDialog.newTags) {
    const index = editTagsDialog.newTags.indexOf(tag)
    if (index > -1) {
      editTagsDialog.newTags.splice(index, 1)
    }
  }
}

// 保存标签
const saveTags = async () => {
  if (editTagsDialog.document && editTagsDialog.newTags) {
    const success = await documentStore.updateDocumentTags(
      editTagsDialog.document.id,
      editTagsDialog.newTags
    )
    if (success) {
      editTagsDialog.visible = false
      ElMessage.success('标签更新成功')
    } else {
      ElMessage.error('标签更新失败')
    }
  }
}

// 重置筛选条件
const resetFilters = () => {
  searchQuery.value = ''
  selectedType.value = ''
  selectedTag.value = ''
  dateRange.value = null
  fetchDocuments({ page: 1 })
}

// 批量删除
const batchDelete = async () => {
  if (selectedDocuments.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedDocuments.value.length} 个文档吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const documentIds = selectedDocuments.value.map(doc => doc.id)
    const success = await documentStore.deleteDocuments(documentIds)
    if (success) {
      ElMessage.success('批量删除成功')
      selectedDocuments.value = []
    } else {
      ElMessage.error('批量删除失败')
    }
  } catch {
    // 用户取消删除
  }
}

// 批量下载
const batchDownload = async () => {
  if (selectedDocuments.value.length === 0) return
  
  ElMessage.info('开始批量下载，请稍候...')
  
  for (const doc of selectedDocuments.value) {
    try {
      await documentStore.downloadDocument(doc.id, doc.filename)
      // 添加短暂延迟避免同时下载过多文件
      await new Promise(resolve => setTimeout(resolve, 500))
    } catch (error) {
      ElMessage.error(`下载失败: ${doc.filename}`)
    }
  }
  
  ElMessage.success('批量下载完成')
}

// 批量编辑标签
const batchUpdateTags = () => {
  if (selectedDocuments.value.length === 0) return
  
  ElMessage.info('批量编辑标签功能开发中...')
}
</script>

<style scoped>
/* 自定义样式 */
</style>