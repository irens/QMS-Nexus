<template>
  <div class="error-boundary">
    <div v-if="hasError" class="error-container">
      <div class="error-content">
        <div class="error-icon">
          <el-icon size="48" color="#F56C6C">
            <Warning />
          </el-icon>
        </div>
        <h3 class="error-title">{{ errorTitle }}</h3>
        <p class="error-message">{{ errorMessage }}</p>
        <div class="error-actions">
          <el-button type="primary" @click="resetError">
            <el-icon class="mr-1"><RefreshRight /></el-icon>
            重新加载
          </el-button>
          <el-button @click="goHome">
            <el-icon class="mr-1"><House /></el-icon>
            返回首页
          </el-button>
        </div>
        <details v-if="showDetails" class="error-details">
          <summary>错误详情</summary>
          <pre class="error-stack">{{ error?.stack }}</pre>
        </details>
      </div>
    </div>
    <div v-else>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured, defineExpose } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Warning, RefreshRight, House } from '@element-plus/icons-vue'

interface Props {
  errorTitle?: string
  errorMessage?: string
  showDetails?: boolean
  fallback?: () => void
}

const props = withDefaults(defineProps<Props>(), {
  errorTitle: '组件加载失败',
  errorMessage: '很抱歉，组件加载时遇到了问题。请尝试重新加载或返回首页。',
  showDetails: process.env.NODE_ENV === 'development'
})

const emit = defineEmits<{
  error: [error: Error, instance: ComponentPublicInstance | null, info: string]
  reset: []
}>()

const router = useRouter()

const hasError = ref(false)
const error = ref<Error | null>(null)
const errorInfo = ref('')

/**
 * 错误边界捕获函数
 * 捕获子组件的运行时错误
 */
const handleError = (err: Error, instance: ComponentPublicInstance | null, info: string) => {
  console.error('ErrorBoundary捕获到错误:', err, info)
  
  hasError.value = true
  error.value = err
  errorInfo.value = info
  
  // 发送错误事件
  emit('error', err, instance, info)
  
  // 显示错误通知
  ElMessage.error({
    message: '组件出现错误，请查看错误详情',
    duration: 5000
  })
  
  // 在开发环境下记录详细错误信息
  if (process.env.NODE_ENV === 'development') {
    console.group('🐛 错误详情')
    console.error('错误信息:', err.message)
    console.error('错误堆栈:', err.stack)
    console.error('组件实例:', instance)
    console.error('错误信息:', info)
    console.groupEnd()
  }
  
  return false // 阻止错误继续向上传播
}

/**
 * 重置错误状态
 */
const resetError = () => {
  hasError.value = false
  error.value = null
  errorInfo.value = ''
  
  emit('reset')
  
  if (props.fallback) {
    props.fallback()
  }
}

/**
 * 返回首页
 */
const goHome = () => {
  router.push('/system')
}

// 注册错误捕获
onErrorCaptured(handleError)

// 暴露方法给父组件
defineExpose({
  resetError,
  hasError,
  error
})
</script>

<style scoped>
.error-boundary {
  width: 100%;
  height: 100%;
}

.error-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 24px;
}

.error-content {
  text-align: center;
  max-width: 500px;
}

.error-icon {
  margin-bottom: 16px;
}

.error-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.error-message {
  font-size: 14px;
  color: #606266;
  margin-bottom: 24px;
  line-height: 1.5;
}

.error-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.error-details {
  margin-top: 24px;
  text-align: left;
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 16px;
}

.error-details summary {
  cursor: pointer;
  font-weight: 500;
  color: #606266;
  margin-bottom: 8px;
}

.error-stack {
  font-size: 12px;
  color: #909399;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

/* 暗色主题适配 */
@media (prefers-color-scheme: dark) {
  .error-title {
    color: #e5e5e5;
  }
  
  .error-message {
    color: #b5b5b5;
  }
  
  .error-details {
    background-color: #2a2a2a;
  }
  
  .error-details summary {
    color: #b5b5b5;
  }
  
  .error-stack {
    color: #888;
  }
}
</style>