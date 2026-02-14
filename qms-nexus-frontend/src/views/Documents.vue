<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">文档列表</h1>
      <p class="text-gray-600">管理和查看已上传的文档</p>
    </div>

    <!-- 搜索和筛选 -->
    <div class="mb-6">
      <el-row :gutter="20">
        <el-col :span="12">
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
        <el-col :span="6">
          <el-select v-model="selectedType" placeholder="文件类型" clearable @change="handleSearch">
            <el-option label="PDF" value="pdf" />
            <el-option label="Word" value="doc" />
            <el-option label="Excel" value="xls" />
            <el-option label="PowerPoint" value="ppt" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="selectedTag" placeholder="标签筛选" clearable @change="handleSearch">
            <el-option label="质量管理" value="quality" />
            <el-option label="医疗规范" value="medical" />
            <el-option label="培训资料" value="training" />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <!-- 文档列表 -->
    <div class="mb-6">
      <el-table 
        :data="filteredDocuments" 
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
                <p class="text-sm font-medium text-gray-800">{{ row.fileName }}</p>
                <p class="text-xs text-gray-500">{{ row.fileSize }}</p>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="uploadTime" label="上传时间" width="150" />
        
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
          <p class="text-sm text-gray-600 mb-2">文件名：{{ editTagsDialog.document?.fileName }}</p>
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
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Document,
  DocumentCopy,
  Tickets,
  Notebook,
  CaretBottom,
  Edit,
  Share,
  Delete
} from '@element-plus/icons-vue'

interface DocumentItem {
  id: string
  fileName: string
  fileType: string
  fileSize: string
  uploadTime: string
  tags: string[]
  status: 'processing' | 'completed' | 'failed'
}

// 搜索和筛选
const searchQuery = ref('')
const selectedType = ref('')
const selectedTag = ref('')

// 表格数据
const loading = ref(false)
const selectedDocuments = ref<DocumentItem[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const totalDocuments = ref(100)

// 模拟文档数据
const documents = ref<DocumentItem[]>([
  {
    id: '1',
    fileName: '医疗质量管理规范.pdf',
    fileType: 'pdf',
    fileSize: '2.3 MB',
    uploadTime: '2024-01-15 14:30',
    tags: ['quality', 'medical'],
    status: 'completed'
  },
  {
    id: '2',
    fileName: '2024年度质量报告.docx',
    fileType: 'docx',
    fileSize: '1.8 MB',
    uploadTime: '2024-01-15 10:15',
    tags: ['quality'],
    status: 'completed'
  },
  {
    id: '3',
    fileName: '质量指标统计表.xlsx',
    fileType: 'xlsx',
    fileSize: '856 KB',
    uploadTime: '2024-01-14 16:45',
    tags: ['quality', 'training'],
    status: 'completed'
  },
  {
    id: '4',
    fileName: '培训计划.pptx',
    fileType: 'pptx',
    fileSize: '3.2 MB',
    uploadTime: '2024-01-14 09:30',
    tags: ['training'],
    status: 'processing'
  }
])

// 编辑标签对话框
const editTagsDialog = reactive({
  visible: false,
  document: null as DocumentItem | null,
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

// 筛选后的文档
const filteredDocuments = computed(() => {
  let result = documents.value

  // 搜索筛选
  if (searchQuery.value) {
    result = result.filter(doc => 
      doc.fileName.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }

  // 类型筛选
  if (selectedType.value) {
    result = result.filter(doc => doc.fileType === selectedType.value)
  }

  // 标签筛选
  if (selectedTag.value) {
    result = result.filter(doc => doc.tags.includes(selectedTag.value))
  }

  return result
})

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1
  // 这里可以调用API重新获取数据
}

// 处理选择变化
const handleSelectionChange = (val: DocumentItem[]) => {
  selectedDocuments.value = val
}

// 处理分页
const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
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
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    processing: '解析中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || '未知'
}

// 查看文档
const viewDocument = (row: DocumentItem) => {
  ElMessage.info(`查看文档: ${row.fileName}`)
}

// 下载文档
const downloadDocument = (row: DocumentItem) => {
  ElMessage.success(`开始下载: ${row.fileName}`)
}

// 编辑标签
const editTags = (row: DocumentItem) => {
  editTagsDialog.document = row
  editTagsDialog.newTags = [...row.tags]
  editTagsDialog.visible = true
}

// 分享文档
const shareDocument = (row: DocumentItem) => {
  ElMessage.info(`分享文档: ${row.fileName}`)
}

// 删除文档
const deleteDocument = async (row: DocumentItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${row.fileName}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = documents.value.findIndex(item => item.id === row.id)
    if (index > -1) {
      documents.value.splice(index, 1)
    }
    ElMessage.success('删除成功')
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
const saveTags = () => {
  if (editTagsDialog.document && editTagsDialog.newTags) {
    editTagsDialog.document.tags = [...editTagsDialog.newTags]
    editTagsDialog.visible = false
    ElMessage.success('标签更新成功')
  }
}
</script>

<style scoped>
/* 自定义样式 */
</style>