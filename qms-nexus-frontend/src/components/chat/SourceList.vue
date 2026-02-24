<template>
  <div class="source-list">
    <el-divider />
    <div class="flex items-center mb-3">
      <el-icon class="text-gray-500 mr-2"><Document /></el-icon>
      <h4 class="text-sm font-medium text-gray-800">参考来源</h4>
      <el-tag size="small" type="info" class="ml-2">{{ sources.length }}个来源</el-tag>
    </div>

    <div class="space-y-2">
      <div
        v-for="(source, index) in sources"
        :key="source.version_id + '-' + index"
        class="source-item"
        :class="{ 'has-warning': source.warning }"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <!-- 文档名称和版本信息 -->
            <div class="flex items-center flex-wrap gap-2">
              <span class="text-sm font-medium text-blue-600 hover:text-blue-800 cursor-pointer"
                @click="viewDocument(source)">
                {{ source.document_name }}
              </span>

              <!-- 版本标签 -->
              <el-tag size="small" type="primary" effect="plain">
                {{ source.version_label }}
              </el-tag>

              <!-- 状态标签 -->
              <el-tag
                size="small"
                :type="getStatusType(source.status)"
                effect="light"
              >
                {{ getStatusText(source.status) }}
              </el-tag>

              <!-- 最新版本标记 -->
              <el-tag
                v-if="source.is_latest"
                size="small"
                type="success"
                effect="plain"
              >
                最新
              </el-tag>
            </div>

            <!-- 页码和相似度 -->
            <div class="flex items-center mt-1 text-xs text-gray-500 space-x-3">
              <span>
                <el-icon class="mr-1"><Document /></el-icon>
                第 {{ source.page }} 页
              </span>
              <span>
                <el-icon class="mr-1"><TrendCharts /></el-icon>
                相似度: {{ (source.score * 100).toFixed(1) }}%
              </span>
              <span v-if="source.effective_date">
                <el-icon class="mr-1"><Calendar /></el-icon>
                生效日期: {{ formatDate(source.effective_date) }}
              </span>
            </div>

            <!-- 警告信息 -->
            <div v-if="source.warning" class="mt-2">
              <el-alert
                :title="source.warning"
                type="warning"
                :closable="false"
                size="small"
                show-icon
              />
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="flex items-center space-x-2 ml-4">
            <el-button
              type="primary"
              link
              size="small"
              @click="viewVersion(source.version_id)"
            >
              <el-icon class="mr-1"><View /></el-icon>
              查看版本
            </el-button>
            <el-button
              v-if="!source.is_latest"
              type="warning"
              link
              size="small"
              @click="viewLatest(source)"
            >
              <el-icon class="mr-1"><TopRight /></el-icon>
              查看最新
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 版本统计信息 -->
    <div v-if="showStats" class="mt-4 pt-3 border-t border-gray-200">
      <div class="flex items-center justify-between text-xs text-gray-500">
        <span>版本统计:</span>
        <div class="flex items-center space-x-4">
          <span class="flex items-center">
            <span class="w-2 h-2 rounded-full bg-green-500 mr-1"></span>
            生效中: {{ effectiveCount }}
          </span>
          <span class="flex items-center">
            <span class="w-2 h-2 rounded-full bg-gray-400 mr-1"></span>
            历史版本: {{ historicalCount }}
          </span>
          <span class="flex items-center">
            <span class="w-2 h-2 rounded-full bg-red-500 mr-1"></span>
            已作废: {{ obsoleteCount }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, TrendCharts, Calendar, View, TopRight } from '@element-plus/icons-vue'
import type { Source } from '@/services/chat'

const props = defineProps<{
  sources: Source[]
  showStats?: boolean
}>()

const emit = defineEmits<{
  (e: 'view-version', versionId: string): void
  (e: 'view-document', documentId: string): void
}>()

const router = useRouter()

// 状态类型映射
const getStatusType = (status: string): string => {
  const typeMap: Record<string, string> = {
    'draft': 'info',
    'review': 'warning',
    'approved': 'success',
    'effective': 'success',
    'obsolete': 'danger'
  }
  return typeMap[status] || 'info'
}

// 状态文本映射
const getStatusText = (status: string): string => {
  const textMap: Record<string, string> = {
    'draft': '草稿',
    'review': '审核中',
    'approved': '已批准',
    'effective': '生效中',
    'obsolete': '已作废'
  }
  return textMap[status] || status
}

// 格式化日期
const formatDate = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 查看版本详情
const viewVersion = (versionId: string) => {
  emit('view-version', versionId)
  // 导航到版本详情页
  router.push(`/documents/versions/${versionId}`)
}

// 查看文档
const viewDocument = (source: Source) => {
  // 从 version_id 提取 document_id
  // 假设 version_id 格式为: doc_id + _v + version_number
  const documentId = source.version_id.split('_v')[0]
  emit('view-document', documentId)
  router.push(`/documents/${documentId}`)
}

// 查看最新版本
const viewLatest = (source: Source) => {
  const documentId = source.version_id.split('_v')[0]
  router.push(`/documents/${documentId}/versions`)
}

// 统计信息
const effectiveCount = computed(() => {
  return props.sources.filter(s => s.status === 'effective').length
})

const historicalCount = computed(() => {
  return props.sources.filter(s => s.status !== 'effective' && s.status !== 'obsolete').length
})

const obsoleteCount = computed(() => {
  return props.sources.filter(s => s.status === 'obsolete').length
})
</script>

<style scoped>
.source-list {
  @apply mt-4;
}

.source-item {
  @apply p-3 bg-gray-50 rounded-lg border border-gray-200;
}

.source-item.has-warning {
  @apply border-yellow-300 bg-yellow-50/30;
}

.source-item:hover {
  @apply bg-gray-100;
}
</style>
