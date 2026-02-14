<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">文档搜索</h1>
      <p class="text-gray-600">在知识库中搜索相关文档内容</p>
    </div>

    <!-- 搜索区域 -->
    <div class="mb-6">
      <el-card>
        <div class="flex space-x-4">
          <el-input
            v-model="searchQuery"
            placeholder="请输入搜索关键词..."
            class="flex-1"
            size="large"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button
            type="primary"
            size="large"
            @click="handleSearch"
            :loading="isSearching"
          >
            <el-icon class="mr-2"><Search /></el-icon>
            搜索
          </el-button>
        </div>
        
        <!-- 高级搜索选项 -->
        <div class="mt-4 flex flex-wrap gap-4">
          <el-select v-model="searchType" placeholder="搜索类型" size="small">
            <el-option label="全文搜索" value="all" />
            <el-option label="标题搜索" value="title" />
            <el-option label="内容搜索" value="content" />
          </el-select>
          
          <el-select v-model="fileType" placeholder="文件类型" size="small" clearable>
            <el-option label="PDF" value="pdf" />
            <el-option label="Word" value="doc" />
            <el-option label="Excel" value="xls" />
            <el-option label="PowerPoint" value="ppt" />
          </el-select>
          
          <el-select v-model="selectedTags" placeholder="标签筛选" size="small" multiple clearable>
            <el-option label="质量管理" value="quality" />
            <el-option label="医疗规范" value="medical" />
            <el-option label="培训资料" value="training" />
            <el-option label="政策法规" value="policy" />
          </el-select>
          
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            style="width: 240px"
          />
        </div>
      </el-card>
    </div>

    <!-- 搜索结果统计 -->
    <div v-if="hasSearched" class="mb-4">
      <div class="flex items-center justify-between">
        <div class="text-sm text-gray-600">
          找到 <span class="font-medium text-gray-800">{{ totalResults }}</span> 个相关结果
          <span v-if="searchTime">，用时 {{ searchTime }} 秒</span>
        </div>
        <div class="flex items-center space-x-4">
          <el-select v-model="sortBy" size="small" @change="handleSort">
            <el-option label="相关性排序" value="relevance" />
            <el-option label="时间排序" value="time" />
            <el-option label="文件大小" value="size" />
          </el-select>
          
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button label="list">
              <el-icon><Tickets /></el-icon>
            </el-radio-button>
            <el-radio-button label="card">
              <el-icon><Grid /></el-icon>
            </el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="hasSearched" class="space-y-4">
      <!-- 列表视图 -->
      <div v-if="viewMode === 'list'">
        <el-card>
          <el-table :data="searchResults" style="width: 100%">
            <el-table-column label="文档信息" min-width="300">
              <template #default="{ row }">
                <div class="flex items-center space-x-3">
                  <el-icon size="20" :class="getFileIconColor(row.fileType)">
                    <component :is="getFileIcon(row.fileType)" />
                  </el-icon>
                  <div>
                    <p class="text-sm font-medium text-gray-800">{{ row.fileName }}</p>
                    <p class="text-xs text-gray-500">{{ row.fileSize }} • {{ row.uploadTime }}</p>
                  </div>
                </div>
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
                  >
                    {{ getTagText(tag) }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="相关性" width="100">
              <template #default="{ row }">
                <el-progress 
                  :percentage="row.relevance" 
                  :color="getRelevanceColor(row.relevance)"
                  :stroke-width="6"
                  :show-text="false"
                />
                <div class="text-xs text-gray-500 text-center mt-1">
                  {{ row.relevance }}%
                </div>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <div class="flex space-x-2">
                  <el-button
                    type="primary"
                    link
                    size="small"
                    @click="previewDocument(row)"
                  >
                    预览
                  </el-button>
                  <el-button
                    type="primary"
                    link
                    size="small"
                    @click="viewDetails(row)"
                  >
                    详情
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <!-- 卡片视图 -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <el-card 
          v-for="result in searchResults" 
          :key="result.id"
          class="hover:shadow-lg transition-shadow cursor-pointer"
          @click="previewDocument(result)"
        >
          <div class="flex items-start space-x-3 mb-3">
            <el-icon size="24" :class="getFileIconColor(result.fileType)">
              <component :is="getFileIcon(result.fileType)" />
            </el-icon>
            <div class="flex-1">
              <h3 class="text-sm font-medium text-gray-800 mb-1">
                {{ result.fileName }}
              </h3>
              <p class="text-xs text-gray-500 mb-2">
                {{ result.fileSize }} • {{ result.uploadTime }}
              </p>
              <div class="flex flex-wrap gap-1 mb-2">
                <el-tag
                  v-for="tag in result.tags.slice(0, 3)"
                  :key="tag"
                  size="small"
                  :type="getTagType(tag) as any"
                >
                  {{ getTagText(tag) }}
                </el-tag>
                <el-tag
                  v-if="result.tags.length > 3"
                  size="small"
                  type="info"
                >
                  +{{ result.tags.length - 3 }}
                </el-tag>
              </div>
            </div>
          </div>
          
          <div class="mb-3">
            <div class="text-xs text-gray-600 mb-1">相关性：</div>
            <el-progress 
              :percentage="result.relevance" 
              :color="getRelevanceColor(result.relevance)"
              :stroke-width="4"
              :show-text="false"
            />
          </div>
          
          <div class="text-xs text-gray-600">
            <div class="mb-1">匹配内容：</div>
            <div class="bg-gray-50 p-2 rounded text-xs">
              {{ result.excerpt }}
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="text-center py-12">
      <el-icon size="48" class="text-gray-300 mb-4">
        <Search />
      </el-icon>
      <h3 class="text-lg font-medium text-gray-600 mb-2">开始搜索</h3>
      <p class="text-gray-500">输入关键词，在医疗文档知识库中查找相关内容</p>
    </div>

    <!-- 文档详情对话框 -->
    <el-dialog
      v-model="detailDialog.visible"
      title="文档详情"
      width="800px"
      top="5vh"
    >
      <div v-if="detailDialog.document" class="space-y-4">
        <div class="flex items-center space-x-3">
          <el-icon size="24" :class="getFileIconColor(detailDialog.document.fileType)">
            <component :is="getFileIcon(detailDialog.document.fileType)" />
          </el-icon>
          <div>
            <h3 class="text-lg font-medium text-gray-800">
              {{ detailDialog.document.fileName }}
            </h3>
            <p class="text-sm text-gray-500">
              {{ detailDialog.document.fileSize }} • {{ detailDialog.document.uploadTime }}
            </p>
          </div>
        </div>
        
        <el-divider />
        
        <div>
          <h4 class="font-medium text-gray-800 mb-2">文档标签</h4>
          <div class="flex flex-wrap gap-2">
            <el-tag
              v-for="tag in detailDialog.document.tags"
              :key="tag"
              :type="getTagType(tag) as any"
            >
              {{ getTagText(tag) }}
            </el-tag>
          </div>
        </div>
        
        <div>
          <h4 class="font-medium text-gray-800 mb-2">搜索匹配</h4>
          <div class="bg-gray-50 p-4 rounded">
            <div class="text-sm text-gray-600 mb-2">相关性：{{ detailDialog.document.relevance }}%</div>
            <div class="text-sm text-gray-600 mb-2">匹配内容：</div>
            <div class="text-sm text-gray-800">
              {{ detailDialog.document.excerpt }}
            </div>
          </div>
        </div>
        
        <div>
          <h4 class="font-medium text-gray-800 mb-2">相关段落</h4>
          <div class="space-y-2 max-h-40 overflow-y-auto">
            <div 
              v-for="(paragraph, index) in detailDialog.document.paragraphs" 
              :key="index"
              class="text-sm text-gray-700 p-2 bg-blue-50 rounded"
            >
              {{ paragraph }}
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialog.visible = false">关闭</el-button>
          <el-button type="primary" @click="previewDocument(detailDialog.document!)">
            预览文档
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Tickets,
  Grid,
  Document,
  DocumentCopy,
  Tickets as ExcelIcon,
  Notebook
} from '@element-plus/icons-vue'

interface SearchResult {
  id: string
  fileName: string
  fileType: string
  fileSize: string
  uploadTime: string
  tags: string[]
  relevance: number
  excerpt: string
  paragraphs: string[]
}

// 搜索状态
const searchQuery = ref('')
const isSearching = ref(false)
const hasSearched = ref(false)
const searchTime = ref('')
const totalResults = ref(0)

// 搜索选项
const searchType = ref('all')
const fileType = ref('')
const selectedTags = ref<string[]>([])
const dateRange = ref('')
const sortBy = ref('relevance')

// 显示选项
const viewMode = ref('list')

// 搜索结果
const searchResults = reactive<SearchResult[]>([])

// 详情对话框
const detailDialog = reactive({
  visible: false,
  document: null as SearchResult | null
})

// 模拟搜索
const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }

  isSearching.value = true
  hasSearched.value = true

  // 模拟搜索延迟
  setTimeout(() => {
    // 模拟搜索结果
    searchResults.length = 0
    searchResults.push(...[
      {
        id: '1',
        fileName: '医疗质量管理规范.pdf',
        fileType: 'pdf',
        fileSize: '2.3 MB',
        uploadTime: '2024-01-15',
        tags: ['quality', 'medical'],
        relevance: 95,
        excerpt: '医疗质量管理是医院管理的核心内容，直接关系到患者的生命安全和医疗效果...',
        paragraphs: [
          '医疗质量管理是医院管理的核心内容，直接关系到患者的生命安全和医疗效果。',
          '建立完善的质量管理体系需要全员参与，持续改进。'
        ]
      },
      {
        id: '2',
        fileName: '2024年度质量报告.docx',
        fileType: 'docx',
        fileSize: '1.8 MB',
        uploadTime: '2024-01-15',
        tags: ['quality'],
        relevance: 88,
        excerpt: '2024年度医疗质量管理工作取得了显著成效，各项指标均达到预期目标...',
        paragraphs: [
          '2024年度医疗质量管理工作取得了显著成效。',
          '各项指标均达到预期目标，患者满意度持续提升。'
        ]
      },
      {
        id: '3',
        fileName: '质量指标统计表.xlsx',
        fileType: 'xlsx',
        fileSize: '856 KB',
        uploadTime: '2024-01-14',
        tags: ['quality', 'training'],
        relevance: 82,
        excerpt: '质量指标统计表包含了各项医疗质量指标的详细数据和分析...',
        paragraphs: [
          '质量指标统计表包含了各项医疗质量指标的详细数据。',
          '通过数据分析可以发现问题并制定改进措施。'
        ]
      }
    ])

    totalResults.value = searchResults.length
    searchTime.value = '0.25'
    isSearching.value = false
    
    ElMessage.success(`搜索完成，找到 ${totalResults.value} 个相关结果`)
  }, 1500)
}

// 处理排序
const handleSort = () => {
  // 根据sortBy重新排序结果
  ElMessage.info(`按${sortBy.value}排序`)
}

// 获取文件图标
const getFileIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    pdf: Document,
    doc: DocumentCopy,
    docx: DocumentCopy,
    xls: ExcelIcon,
    xlsx: ExcelIcon,
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

// 获取相关性颜色
const getRelevanceColor = (relevance: number) => {
  if (relevance >= 90) return '#22c55e'
  if (relevance >= 70) return '#3b82f6'
  if (relevance >= 50) return '#f59e0b'
  return '#ef4444'
}

// 预览文档
const previewDocument = (document: SearchResult) => {
  ElMessage.info(`预览文档: ${document.fileName}`)
}

// 查看详情
const viewDetails = (document: SearchResult) => {
  detailDialog.document = document
  detailDialog.visible = true
}
</script>

<style scoped>
/* 自定义样式 */
</style>