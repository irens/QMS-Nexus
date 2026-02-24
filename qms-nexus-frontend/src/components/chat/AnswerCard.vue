<template>
  <div class="answer-card">
    <!-- 答案内容 -->
    <div class="answer-content" v-html="formattedAnswer"></div>

    <!-- 版本信息提示（如果有引用历史版本） -->
    <el-alert
      v-if="hasObsoleteSources"
      type="warning"
      :closable="false"
      class="version-warning"
    >
      <template #title>
        <div class="flex items-center">
          <el-icon class="mr-2"><Warning /></el-icon>
          <span>注意：答案引用了已作废或历史版本的内容</span>
        </div>
      </template>
      <p class="text-sm text-gray-600 mt-1">建议查看最新生效版本以获得准确信息</p>
      <el-button type="primary" size="small" class="mt-2" @click="viewLatestVersions">
        查看最新版本
      </el-button>
    </el-alert>

    <!-- 版本对比快捷入口（如果用户询问版本区别） -->
    <div v-if="showVersionCompare" class="version-compare-entry">
      <el-divider />
      <div class="bg-blue-50 p-4 rounded-lg">
        <div class="flex items-center mb-2">
          <el-icon class="text-blue-500 mr-2"><DocumentCopy /></el-icon>
          <h4 class="text-sm font-medium text-gray-800">版本对比</h4>
        </div>
        <p class="text-xs text-gray-600 mb-3">检测到您可能想了解版本差异</p>
        <el-button type="primary" size="small" @click="openVersionCompare">
          查看版本对比
        </el-button>
      </div>
    </div>

    <!-- 历史版本追溯 -->
    <div v-if="enableHistoricalQuery" class="historical-query">
      <el-divider />
      <div class="bg-gray-50 p-4 rounded-lg">
        <div class="flex items-center mb-2">
          <el-icon class="text-gray-500 mr-2"><Calendar /></el-icon>
          <h4 class="text-sm font-medium text-gray-800">历史版本查询</h4>
        </div>
        <div class="flex items-center space-x-2">
          <el-date-picker
            v-model="selectedDate"
            type="date"
            placeholder="选择日期查看历史版本"
            :disabled-date="disabledFutureDate"
            size="small"
            style="width: 200px"
          />
          <el-button type="primary" size="small" @click="queryHistoricalVersion">
            查询
          </el-button>
        </div>
      </div>
    </div>

    <!-- 来源文档列表 -->
    <SourceList
      v-if="sources && sources.length > 0"
      :sources="sources"
      @view-version="viewVersionDetail"
      @view-document="viewDocumentDetail"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning, DocumentCopy, Calendar } from '@element-plus/icons-vue'
import SourceList from './SourceList.vue'
import type { Source } from '@/services/chat'

const props = defineProps<{
  answer: string
  sources: Source[]
  currentQuestion?: string
  enableHistoricalQuery?: boolean
}>()

const emit = defineEmits<{
  (e: 'view-version', versionId: string): void
  (e: 'view-document', documentId: string): void
  (e: 'query-historical', date: string): void
  (e: 'compare-versions', v1Id: string, v2Id: string): void
}>()

const router = useRouter()
const selectedDate = ref('')

// 检查是否有作废或历史版本
const hasObsoleteSources = computed(() => {
  return props.sources.some(s => s.status === 'obsolete' || !s.is_latest)
})

// 检查是否是版本对比问题
const showVersionCompare = computed(() => {
  if (!props.currentQuestion) return false
  const question = props.currentQuestion.toLowerCase()
  return question.includes('区别') ||
         question.includes('不同') ||
         question.includes('对比') ||
         question.includes('变更') ||
         question.includes('差异') ||
         question.includes('更新')
})

// 格式化答案，添加版本标注
const formattedAnswer = computed(() => {
  let text = props.answer

  // 在答案开头添加版本信息说明
  if (props.sources.length > 0) {
    const versionInfo = props.sources.map(s => {
      const statusText = getStatusText(s.status)
      return `${s.document_name} ${s.version_label}(${statusText})`
    }).join('、')

    text = `> 📄 参考文档：${versionInfo}\n\n${text}`
  }

  // 简单的 Markdown 渲染
  return renderMarkdown(text)
})

// 获取状态文本
const getStatusText = (status: string): string => {
  const statusMap: Record<string, string> = {
    'draft': '草稿',
    'review': '审核中',
    'approved': '已批准',
    'effective': '生效中',
    'obsolete': '已作废'
  }
  return statusMap[status] || status
}

// 简单的 Markdown 渲染
const renderMarkdown = (text: string): string => {
  return text
    // 处理引用块
    .replace(/^> (.*$)/gim, '<blockquote class="border-l-4 border-blue-400 pl-4 py-2 my-2 bg-blue-50 text-gray-700">$1</blockquote>')
    // 处理粗体
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // 处理斜体
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // 处理换行
    .replace(/\n/g, '<br>')
}

// 查看最新版本
const viewLatestVersions = () => {
  // 获取所有有历史版本的文档
  const documentIds = [...new Set(props.sources.map(s => s.version_id))]
  if (documentIds.length > 0) {
    // 导航到第一个文档的版本页面
    router.push(`/documents/${documentIds[0]}/versions`)
  }
}

// 打开版本对比
const openVersionCompare = () => {
  // 获取不同版本的文档
  const uniqueVersions = props.sources.filter((s, i, arr) =>
    arr.findIndex(t => t.version_id === s.version_id) === i
  )

  if (uniqueVersions.length >= 2) {
    emit('compare-versions', uniqueVersions[0].version_id, uniqueVersions[1].version_id)
  } else {
    ElMessage.info('需要至少两个不同版本才能进行对比')
  }
}

// 查询历史版本
const queryHistoricalVersion = () => {
  if (!selectedDate.value) {
    ElMessage.warning('请选择日期')
    return
  }
  const dateStr = new Date(selectedDate.value).toISOString().split('T')[0]
  emit('query-historical', dateStr)
}

// 禁用未来日期
const disabledFutureDate = (date: Date) => {
  return date > new Date()
}

// 查看版本详情
const viewVersionDetail = (versionId: string) => {
  emit('view-version', versionId)
}

// 查看文档详情
const viewDocumentDetail = (documentId: string) => {
  emit('view-document', documentId)
}
</script>

<style scoped>
.answer-card {
  @apply space-y-4;
}

.answer-content {
  @apply text-sm text-gray-800 leading-relaxed;
}

.answer-content :deep(blockquote) {
  @apply border-l-4 border-blue-400 pl-4 py-2 my-2 bg-blue-50 text-gray-700 rounded;
}

.answer-content :deep(strong) {
  @apply font-semibold;
}

.version-warning {
  @apply my-4;
}

.version-compare-entry,
.historical-query {
  @apply my-4;
}
</style>
