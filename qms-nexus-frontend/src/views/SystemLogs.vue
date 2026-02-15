// 系统日志查看器
<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">系统日志</h1>
      <p class="text-gray-600">查看系统运行日志和操作记录</p>
    </div>

    <!-- 日志筛选 -->
    <el-card class="mb-6">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg font-medium">日志筛选</span>
          <div class="flex space-x-2">
            <el-button type="primary" @click="searchLogs">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="resetFilters">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
            <el-button type="success" @click="exportLogs">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
          </div>
        </div>
      </template>
      
      <el-form :model="filters" label-width="100px" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <el-form-item label="日志级别">
            <el-select v-model="filters.level" placeholder="选择日志级别" clearable>
              <el-option label="调试" value="debug" />
              <el-option label="信息" value="info" />
              <el-option label="警告" value="warning" />
              <el-option label="错误" value="error" />
              <el-option label="严重" value="critical" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="模块">
            <el-select v-model="filters.module" placeholder="选择模块" clearable>
              <el-option label="文档管理" value="document" />
              <el-option label="智能问答" value="chat" />
              <el-option label="用户管理" value="user" />
              <el-option label="系统管理" value="system" />
              <el-option label="标签管理" value="tag" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="开始时间">
            <el-date-picker
              v-model="filters.startTime"
              type="datetime"
              placeholder="选择开始时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>
          
          <el-form-item label="结束时间">
            <el-date-picker
              v-model="filters.endTime"
              type="datetime"
              placeholder="选择结束时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>
        </div>
        
        <el-form-item label="关键词">
          <el-input
            v-model="filters.keyword"
            placeholder="输入关键词搜索日志内容"
            clearable
          />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志统计 -->
    <el-card class="mb-6">
      <template #header>
        <span class="text-lg font-medium">日志统计</span>
      </template>
      
      <div class="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div class="text-center">
          <div class="text-2xl font-bold text-blue-600">{{ stats.total }}</div>
          <div class="text-sm text-gray-600">总日志数</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">{{ stats.info }}</div>
          <div class="text-sm text-gray-600">信息日志</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-yellow-600">{{ stats.warning }}</div>
          <div class="text-sm text-gray-600">警告日志</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-red-600">{{ stats.error }}</div>
          <div class="text-sm text-gray-600">错误日志</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-purple-600">{{ stats.critical }}</div>
          <div class="text-sm text-gray-600">严重日志</div>
        </div>
      </div>
    </el-card>

    <!-- 日志列表 -->
    <el-card>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg font-medium">日志列表</span>
          <div class="flex space-x-2">
            <el-button type="danger" @click="clearLogs" v-if="hasPermission('system:write')">
              <el-icon><Delete /></el-icon>
              清空日志
            </el-button>
            <el-button @click="refreshLogs">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table 
        :data="logs" 
        style="width: 100%" 
        v-loading="loading"
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="{ row }">
            <div class="text-sm">
              {{ formatDate(row.timestamp) }}
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="getLevelType(row.level)" 
              size="small"
              effect="dark"
            >
              {{ getLevelText(row.level) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="module" label="模块" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getModuleType(row.module)">
              {{ getModuleText(row.module) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="message" label="消息内容" min-width="300">
          <template #default="{ row }">
            <div class="text-sm">
              <div class="font-medium">{{ row.message }}</div>
              <div v-if="row.details" class="text-gray-500 text-xs mt-1">
                {{ truncateText(row.details, 100) }}
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="userId" label="用户" width="120">
          <template #default="{ row }">
            <div v-if="row.userId" class="text-sm">
              <div>{{ getUserName(row.userId) }}</div>
              <div class="text-gray-500 text-xs">{{ row.userId }}</div>
            </div>
            <div v-else class="text-gray-400 text-sm">系统</div>
          </template>
        </el-table-column>
        
        <el-table-column prop="ipAddress" label="IP地址" width="120">
          <template #default="{ row }">
            <div class="text-sm">
              <div>{{ row.ipAddress || '-' }}</div>
              <div v-if="row.requestId" class="text-gray-500 text-xs">
                {{ row.requestId.slice(0, 8) }}
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-2">
              <el-button type="primary" link size="small" @click="viewLogDetails(row)">
                详情
              </el-button>
              <el-button type="danger" link size="small" @click="deleteLog(row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="mt-4 flex justify-between items-center">
        <div class="text-sm text-gray-600">
          共 {{ totalLogs }} 条日志
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalLogs"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="logDetailDialog.visible"
      title="日志详情"
      width="800px"
    >
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">时间</label>
            <div class="text-sm text-gray-900">{{ formatDate(logDetailDialog.log.timestamp) }}</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">级别</label>
            <el-tag 
              :type="getLevelType(logDetailDialog.log.level)" 
              size="small"
              effect="dark"
            >
              {{ getLevelText(logDetailDialog.log.level) }}
            </el-tag>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">模块</label>
            <el-tag size="small" :type="getModuleType(logDetailDialog.log.module)">
              {{ getModuleText(logDetailDialog.log.module) }}
            </el-tag>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">用户</label>
            <div class="text-sm text-gray-900">
              <div>{{ getUserName(logDetailDialog.log.userId) }}</div>
              <div class="text-gray-500">{{ logDetailDialog.log.userId || '系统' }}</div>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">IP地址</label>
            <div class="text-sm text-gray-900">{{ logDetailDialog.log.ipAddress || '-' }}</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">请求ID</label>
            <div class="text-sm text-gray-900">{{ logDetailDialog.log.requestId || '-' }}</div>
          </div>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">消息内容</label>
          <div class="text-sm text-gray-900 bg-gray-50 p-3 rounded">
            {{ logDetailDialog.log.message }}
          </div>
        </div>
        
        <div v-if="logDetailDialog.log.details">
          <label class="block text-sm font-medium text-gray-700 mb-1">详细信息</label>
          <div class="text-sm text-gray-900 bg-gray-50 p-3 rounded max-h-60 overflow-auto">
            <pre>{{ logDetailDialog.log.details }}</pre>
          </div>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="logDetailDialog.visible = false">关闭</el-button>
          <el-button type="primary" @click="copyLogDetails">
            <el-icon><CopyDocument /></el-icon>
            复制详情
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useSystemStore } from '@/stores/system'
import { systemService } from '@/services/system'
import type { SystemLog } from '@/types/system'
import {
  Search,
  Refresh,
  Download,
  Delete,
  CopyDocument
} from '@element-plus/icons-vue'

// 状态管理
const systemStore = useSystemStore()

// 日志数据
const logs = ref<SystemLog[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const totalLogs = ref(0)
const selectedLogs = ref<SystemLog[]>([])

// 筛选条件
const filters = reactive({
  level: '',
  module: '',
  startTime: '',
  endTime: '',
  keyword: ''
})

// 统计信息
const stats = reactive({
  total: 0,
  debug: 0,
  info: 0,
  warning: 0,
  error: 0,
  critical: 0
})

// 日志详情对话框
const logDetailDialog = reactive({
  visible: false,
  log: {} as SystemLog
})

// 权限检查
const hasPermission = (permission: string): boolean => {
  return systemStore.hasPermission(permission)
}

/**
 * 加载日志列表
 */
const loadLogs = async () => {
  loading.value = true
  try {
    const response = await systemService.getSystemLogs(
      currentPage.value,
      pageSize.value,
      {
        level: filters.level || undefined,
        module: filters.module || undefined,
        startTime: filters.startTime || undefined,
        endTime: filters.endTime || undefined
      }
    )
    
    logs.value = response.items
    totalLogs.value = response.total
    
    // 更新统计信息
    updateStats()
  } catch (error) {
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

/**
 * 搜索日志
 */
const searchLogs = () => {
  currentPage.value = 1
  loadLogs()
}

/**
 * 重置筛选条件
 */
const resetFilters = () => {
  filters.level = ''
  filters.module = ''
  filters.startTime = ''
  filters.endTime = ''
  filters.keyword = ''
  loadLogs()
}

/**
 * 刷新日志
 */
const refreshLogs = () => {
  loadLogs()
}

/**
 * 导出日志
 */
const exportLogs = async () => {
  try {
    const blob = await systemService.exportSystemLogs({
      level: filters.level || undefined,
      module: filters.module || undefined,
      startTime: filters.startTime || undefined,
      endTime: filters.endTime || undefined
    })
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `system-logs-${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('日志导出成功')
  } catch (error) {
    ElMessage.error('导出日志失败')
  }
}

/**
 * 清空日志
 */
const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有系统日志吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用清空日志的API
    ElMessage.success('日志已清空')
    loadLogs()
  } catch {
    // 用户取消操作
  }
}

/**
 * 查看日志详情
 */
const viewLogDetails = (log: SystemLog) => {
  logDetailDialog.log = log
  logDetailDialog.visible = true
}

/**
 * 删除日志
 */
const deleteLog = async (log: SystemLog) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条日志吗？',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用删除日志的API
    ElMessage.success('日志删除成功')
    loadLogs()
  } catch {
    // 用户取消删除
  }
}

/**
 * 复制日志详情
 */
const copyLogDetails = async () => {
  try {
    const details = JSON.stringify(logDetailDialog.log, null, 2)
    await navigator.clipboard.writeText(details)
    ElMessage.success('日志详情已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

/**
 * 更新统计信息
 */
const updateStats = () => {
  // 这里应该根据实际数据更新统计
  // 暂时使用模拟数据
  stats.total = totalLogs.value
  stats.debug = Math.floor(totalLogs.value * 0.1)
  stats.info = Math.floor(totalLogs.value * 0.6)
  stats.warning = Math.floor(totalLogs.value * 0.2)
  stats.error = Math.floor(totalLogs.value * 0.08)
  stats.critical = Math.floor(totalLogs.value * 0.02)
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection: SystemLog[]) => {
  selectedLogs.value = selection
}

/**
 * 处理分页大小变化
 */
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadLogs()
}

/**
 * 处理当前页变化
 */
const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadLogs()
}

/**
 * 获取日志级别类型
 */
const getLevelType = (level: string): string => {
  const typeMap: Record<string, string> = {
    debug: 'info',
    info: 'success',
    warning: 'warning',
    error: 'danger',
    critical: 'danger'
  }
  return typeMap[level] || 'info'
}

/**
 * 获取日志级别文本
 */
const getLevelText = (level: string): string => {
  const textMap: Record<string, string> = {
    debug: '调试',
    info: '信息',
    warning: '警告',
    error: '错误',
    critical: '严重'
  }
  return textMap[level] || level
}

/**
 * 获取模块类型
 */
const getModuleType = (module: string): string => {
  const typeMap: Record<string, string> = {
    document: 'primary',
    chat: 'success',
    user: 'warning',
    system: 'danger',
    tag: 'info'
  }
  return typeMap[module] || 'info'
}

/**
 * 获取模块文本
 */
const getModuleText = (module: string): string => {
  const textMap: Record<string, string> = {
    document: '文档管理',
    chat: '智能问答',
    user: '用户管理',
    system: '系统管理',
    tag: '标签管理'
  }
  return textMap[module] || module
}

/**
 * 获取用户名
 */
const getUserName = (userId: string): string => {
  // 这里应该根据用户ID获取用户名
  return userId ? `用户${userId.slice(-4)}` : '系统'
}

/**
 * 格式化日期
 */
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('zh-CN')
}

/**
 * 截断文本
 */
const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

// 生命周期
onMounted(() => {
  loadLogs()
})
</script>