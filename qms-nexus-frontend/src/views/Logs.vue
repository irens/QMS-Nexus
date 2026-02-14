<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">操作日志</h1>
      <p class="text-gray-600">查看系统操作记录和审计信息</p>
    </div>

    <!-- 筛选和搜索 -->
    <div class="mb-6">
      <el-card>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-input
              v-model="searchQuery"
              placeholder="搜索操作描述或用户..."
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
            <el-select v-model="selectedOperation" placeholder="操作类型" clearable @change="handleSearch">
              <el-option label="文件上传" value="upload" />
              <el-option label="文档查看" value="view" />
              <el-option label="文档下载" value="download" />
              <el-option label="用户管理" value="user" />
              <el-option label="系统设置" value="system" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select v-model="selectedUser" placeholder="操作用户" clearable @change="handleSearch">
              <el-option label="张三" value="张三" />
              <el-option label="李四" value="李四" />
              <el-option label="王五" value="王五" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-select v-model="selectedStatus" placeholder="操作状态" clearable @change="handleSearch">
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="handleSearch">
              <el-icon class="mr-1"><Search /></el-icon>
              搜索
            </el-button>
          </el-col>
        </el-row>
        
        <div class="mt-4">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 400px"
          />
          
          <el-button class="ml-4" @click="exportLogs">
            <el-icon class="mr-1"><Download /></el-icon>
            导出日志
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 日志列表 -->
    <div class="mb-6">
      <el-card>
        <el-table 
          :data="filteredLogs" 
          style="width: 100%"
          v-loading="loading"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="55" />
          
          <el-table-column label="操作时间" width="160" sortable>
            <template #default="{ row }">
              <div>
                <div class="text-sm">{{ formatDate(row.timestamp) }}</div>
                <div class="text-xs text-gray-500">{{ formatTime(row.timestamp) }}</div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="操作用户" width="120">
            <template #default="{ row }">
              <div class="flex items-center space-x-2">
                <el-avatar size="small" :icon="User" />
                <span class="text-sm">{{ row.userName }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="操作类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getOperationType(row.operation)" size="small">
                {{ getOperationText(row.operation) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作描述" min-width="250">
            <template #default="{ row }">
              <div>
                <div class="text-sm font-medium">{{ row.description }}</div>
                <div v-if="row.details" class="text-xs text-gray-500 mt-1">
                  {{ row.details }}
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="操作对象" width="150">
            <template #default="{ row }">
              <div class="text-sm">{{ row.objectName }}</div>
              <div class="text-xs text-gray-500">{{ row.objectType }}</div>
            </template>
          </el-table-column>

          <el-table-column label="IP地址" width="120">
            <template #default="{ row }">
              <div class="text-sm">{{ row.ipAddress }}</div>
              <div class="text-xs text-gray-500">{{ row.location }}</div>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag 
                :type="row.status === 'success' ? 'success' : 'danger'" 
                size="small"
              >
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="耗时" width="80">
            <template #default="{ row }">
              <div class="text-sm">{{ row.duration }}ms</div>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <div class="flex space-x-2">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="viewDetails(row)"
                >
                  详情
                </el-button>
                <el-button
                  v-if="row.status === 'failed'"
                  type="warning"
                  link
                  size="small"
                  @click="viewError(row)"
                >
                  错误
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 分页 -->
    <div class="flex justify-between items-center">
      <div class="text-sm text-gray-600">
        共 {{ totalLogs }} 条日志，已选择 {{ selectedLogs.length }} 条
      </div>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="totalLogs"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="detailDialog.visible"
      title="日志详情"
      width="600px"
    >
      <div v-if="detailDialog.log" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">操作时间</label>
            <div class="mt-1 text-sm text-gray-900">{{ formatDateTime(detailDialog.log.timestamp) }}</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">操作用户</label>
            <div class="mt-1 text-sm text-gray-900">{{ detailDialog.log.userName }}</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">操作类型</label>
            <div class="mt-1 text-sm text-gray-900">{{ getOperationText(detailDialog.log.operation) }}</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">操作状态</label>
            <div class="mt-1">
              <el-tag 
                :type="detailDialog.log.status === 'success' ? 'success' : 'danger'" 
                size="small"
              >
                {{ detailDialog.log.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">IP地址</label>
            <div class="mt-1 text-sm text-gray-900">{{ detailDialog.log.ipAddress }}</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">地理位置</label>
            <div class="mt-1 text-sm text-gray-900">{{ detailDialog.log.location }}</div>
          </div>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">操作描述</label>
          <div class="mt-1 text-sm text-gray-900">{{ detailDialog.log.description }}</div>
        </div>
        
        <div v-if="detailDialog.log.details">
          <label class="block text-sm font-medium text-gray-700">详细信息</label>
          <div class="mt-1 text-sm text-gray-900">{{ detailDialog.log.details }}</div>
        </div>
        
        <div v-if="detailDialog.log.objectName">
          <label class="block text-sm font-medium text-gray-700">操作对象</label>
          <div class="mt-1 text-sm text-gray-900">
            {{ detailDialog.log.objectName }} ({{ detailDialog.log.objectType }})
          </div>
        </div>
        
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">执行耗时</label>
            <div class="mt-1 text-sm text-gray-900">{{ detailDialog.log.duration }}ms</div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700">请求ID</label>
            <div class="mt-1 text-sm text-gray-900 font-mono">{{ detailDialog.log.requestId }}</div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="detailDialog.visible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 错误详情对话框 -->
    <el-dialog
      v-model="errorDialog.visible"
      title="错误详情"
      width="600px"
    >
      <div v-if="errorDialog.log" class="space-y-4">
        <el-alert
          :title="errorDialog.log.errorMessage || '操作失败'"
          type="error"
          :description="errorDialog.log.errorStack"
          :closable="false"
        />
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">错误信息</label>
          <el-input
            type="textarea"
            :rows="4"
            :model-value="errorDialog.log.errorDetails"
            readonly
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">建议解决方案</label>
          <el-input
            type="textarea"
            :rows="3"
            :model-value="getErrorSuggestion(errorDialog.log)"
            readonly
          />
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="errorDialog.visible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search,
  Download,
  User
} from '@element-plus/icons-vue'

interface LogItem {
  id: string
  timestamp: string
  userName: string
  operation: string
  description: string
  details?: string
  objectName?: string
  objectType?: string
  ipAddress: string
  location: string
  status: 'success' | 'failed'
  duration: number
  requestId: string
  errorMessage?: string
  errorStack?: string
  errorDetails?: string
}

// 搜索和筛选
const searchQuery = ref('')
const selectedOperation = ref('')
const selectedUser = ref('')
const selectedStatus = ref('')
const dateRange = ref('')

// 表格数据
const loading = ref(false)
const selectedLogs = ref<LogItem[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalLogs = ref(500)

// 模拟日志数据
const logs = ref<LogItem[]>([
  {
    id: '1',
    timestamp: '2024-01-15 14:30:25',
    userName: '张三',
    operation: 'upload',
    description: '上传文档：医疗质量管理规范.pdf',
    objectName: '医疗质量管理规范.pdf',
    objectType: '文档',
    ipAddress: '192.168.1.100',
    location: '北京市',
    status: 'success',
    duration: 1250,
    requestId: 'req_1234567890'
  },
  {
    id: '2',
    timestamp: '2024-01-15 14:28:15',
    userName: '李四',
    operation: 'view',
    description: '查看文档：2024年度质量报告.docx',
    objectName: '2024年度质量报告.docx',
    objectType: '文档',
    ipAddress: '192.168.1.101',
    location: '上海市',
    status: 'success',
    duration: 320,
    requestId: 'req_1234567891'
  },
  {
    id: '3',
    timestamp: '2024-01-15 14:25:30',
    userName: '王五',
    operation: 'user',
    description: '删除用户：赵六',
    objectName: '赵六',
    objectType: '用户',
    ipAddress: '192.168.1.102',
    location: '广州市',
    status: 'failed',
    duration: 150,
    requestId: 'req_1234567892',
    errorMessage: '权限不足',
    errorDetails: '当前用户没有删除用户的权限，需要管理员权限才能执行此操作。'
  }
])

// 详情对话框
const detailDialog = reactive({
  visible: false,
  log: null as LogItem | null
})

// 错误对话框
const errorDialog = reactive({
  visible: false,
  log: null as LogItem | null
})

// 筛选后的日志
const filteredLogs = computed(() => {
  let result = logs.value

  // 搜索筛选
  if (searchQuery.value) {
    result = result.filter(log => 
      log.description.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      log.userName.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }

  // 操作类型筛选
  if (selectedOperation.value) {
    result = result.filter(log => log.operation === selectedOperation.value)
  }

  // 用户筛选
  if (selectedUser.value) {
    result = result.filter(log => log.userName === selectedUser.value)
  }

  // 状态筛选
  if (selectedStatus.value) {
    result = result.filter(log => log.status === selectedStatus.value)
  }

  return result
})

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1
  // 这里可以调用API重新获取数据
}

// 处理选择变化
const handleSelectionChange = (val: LogItem[]) => {
  selectedLogs.value = val
}

// 处理分页
const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

// 获取操作类型
const getOperationType = (operation: string) => {
  const typeMap: Record<string, string> = {
    upload: 'primary',
    view: 'info',
    download: 'success',
    user: 'warning',
    system: 'danger'
  }
  return typeMap[operation] || 'info'
}

// 获取操作文本
const getOperationText = (operation: string) => {
  const textMap: Record<string, string> = {
    upload: '文件上传',
    view: '文档查看',
    download: '文档下载',
    user: '用户管理',
    system: '系统设置'
  }
  return textMap[operation] || operation
}

// 查看详情
const viewDetails = (row: LogItem) => {
  detailDialog.log = row
  detailDialog.visible = true
}

// 查看错误
const viewError = (row: LogItem) => {
  errorDialog.log = row
  errorDialog.visible = true
}

// 获取错误建议
const getErrorSuggestion = (log: LogItem): string => {
  if (log.errorMessage?.includes('权限')) {
    return '请联系系统管理员为您分配相应的操作权限，或确认您的账户角色是否具有执行此操作的权限。'
  }
  if (log.errorMessage?.includes('网络')) {
    return '请检查网络连接是否正常，或稍后重试。如果问题持续存在，请联系技术支持。'
  }
  if (log.errorMessage?.includes('文件')) {
    return '请确认文件是否存在，文件格式是否正确，以及您是否有权限访问该文件。'
  }
  return '请联系系统管理员或技术支持人员获取帮助。'
}

// 导出日志
const exportLogs = () => {
  ElMessage.success('日志导出功能开发中')
}

// 工具函数
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatTime = (dateString: string): string => {
  return new Date(dateString).toLocaleTimeString('zh-CN')
}

const formatDateTime = (dateString: string): string => {
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
/* 自定义样式 */
</style>