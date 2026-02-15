<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">系统设置</h1>
      <p class="text-gray-600">配置系统参数和管理API密钥</p>
    </div>

    <!-- 系统配置 -->
    <el-card class="mb-6">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg font-medium">系统配置</span>
          <el-button type="primary" @click="saveSystemConfig" :loading="savingConfig">
            保存配置
          </el-button>
        </div>
      </template>
      
      <el-form :model="systemConfig" label-width="150px" class="space-y-4">
        <el-form-item label="系统名称">
          <el-input v-model="systemConfig.appName" placeholder="请输入系统名称" />
        </el-form-item>
        
        <el-form-item label="系统版本">
          <el-input v-model="systemConfig.version" placeholder="请输入系统版本" disabled />
        </el-form-item>
        
        <el-form-item label="会话超时时间">
          <el-input-number 
            v-model="systemConfig.sessionTimeout" 
            :min="5" 
            :max="120"
            :step="5"
            controls-position="right"
          />
          <span class="ml-2 text-sm text-gray-500">分钟</span>
        </el-form-item>
        
        <el-form-item label="最大文件大小">
          <el-input-number 
            v-model="systemConfig.maxFileSize" 
            :min="10" 
            :max="500"
            :step="10"
            controls-position="right"
          />
          <span class="ml-2 text-sm text-gray-500">MB</span>
        </el-form-item>
        
        <el-form-item label="匿名访问">
          <el-switch v-model="systemConfig.enableAnonymousAccess" />
          <span class="ml-2 text-sm text-gray-500">允许未登录用户访问公开文档</span>
        </el-form-item>
        
        <el-form-item label="审批流程">
          <el-switch v-model="systemConfig.requireApproval" />
          <span class="ml-2 text-sm text-gray-500">文档上传需要管理员审批</span>
        </el-form-item>
        
        <el-form-item label="相似度阈值">
          <el-slider 
            v-model="systemConfig.similarityThreshold" 
            :min="0.1" 
            :max="1.0" 
            :step="0.1"
            :format-tooltip="(val: number) => `${(val * 100).toFixed(0)}%`"
          />
          <span class="ml-2 text-sm text-gray-500">{{ (systemConfig.similarityThreshold * 100).toFixed(0) }}%</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- API密钥管理 -->
    <el-card class="mb-6">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg font-medium">API密钥管理</span>
          <el-button type="primary" @click="showAddApiKeyDialog">
            <el-icon class="mr-1"><Plus /></el-icon>
            新建密钥
          </el-button>
        </div>
      </template>
      
      <el-table :data="apiKeys" style="width: 100%" v-loading="loadingKeys">
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="密钥名称" prop="name" min-width="150" />
        
        <el-table-column label="密钥" min-width="300">
          <template #default="{ row }">
            <div class="flex items-center space-x-2">
              <code class="bg-gray-100 px-2 py-1 rounded text-sm font-mono">
                {{ showKey(row.key) }}
              </code>
              <el-button type="primary" link size="small" @click="toggleKeyVisibility(row)">
                <el-icon>
                  <component :is="row.visible ? View : Hide" />
                </el-icon>
              </el-button>
              <el-button type="primary" link size="small" @click="copyKey(row.key)">
                <el-icon><CopyDocument /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="权限范围" min-width="200">
          <template #default="{ row }">
            <el-tag 
              v-for="permission in row.permissions" 
              :key="permission"
              size="small"
              class="mr-1"
            >
              {{ getPermissionText(permission) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch 
              v-model="row.status" 
              active-value="active"
              inactive-value="inactive"
              @change="toggleApiKeyStatus(row)"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>
        
        <el-table-column label="最后使用" width="160">
          <template #default="{ row }">
            <div v-if="row.lastUsedAt">
              {{ formatDate(row.lastUsedAt) }}
            </div>
            <div v-else class="text-gray-400 text-sm">从未使用</div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-2">
              <el-button type="primary" link size="small" @click="editApiKey(row)">
                编辑
              </el-button>
              <el-button type="primary" link size="small" @click="viewApiKeyLogs(row)">
                日志
              </el-button>
              <el-button type="danger" link size="small" @click="deleteApiKey(row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="mt-4 flex justify-between items-center">
        <div class="text-sm text-gray-600">
          共 {{ apiKeys.length }} 个API密钥
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="totalKeys"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>
    </el-card>

    <!-- 系统状态 -->
    <el-card>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg font-medium">系统状态</span>
          <el-button type="primary" link @click="refreshSystemStatus">
            <el-icon class="mr-1"><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">{{ systemStatus.services.database }}</div>
          <div class="text-sm text-gray-600">数据库状态</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">{{ systemStatus.services.redis }}</div>
          <div class="text-sm text-gray-600">缓存状态</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-green-600">{{ systemStatus.services.vectorDb }}</div>
          <div class="text-sm text-gray-600">向量数据库</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-blue-600">{{ systemStatus.version }}</div>
          <div class="text-sm text-gray-600">系统版本</div>
        </div>
      </div>
      
      <div class="mt-6">
        <el-alert
          v-if="systemStatus.status === 'error'"
          title="系统异常"
          type="error"
          description="系统检测到异常状态，请联系技术支持"
          :closable="false"
        />
        <el-alert
          v-else-if="systemStatus.status === 'degraded'"
          title="系统性能下降"
          type="warning"
          description="系统性能有所下降，建议检查系统资源"
          :closable="false"
        />
        <el-alert
          v-else
          title="系统运行正常"
          type="success"
          description="所有系统组件运行正常"
          :closable="false"
        />
      </div>
    </el-card>

    <!-- API密钥对话框 -->
    <el-dialog
      v-model="apiKeyDialog.visible"
      :title="apiKeyDialog.isEdit ? '编辑API密钥' : '新建API密钥'"
      width="600px"
    >
      <el-form :model="apiKeyDialog.form" label-width="100px">
        <el-form-item label="密钥名称" required>
          <el-input 
            v-model="apiKeyDialog.form.name" 
            placeholder="请输入密钥名称"
          />
        </el-form-item>
        
        <el-form-item label="权限范围" required>
          <el-checkbox-group v-model="apiKeyDialog.form.permissions">
            <el-checkbox label="document:read">文档读取</el-checkbox>
            <el-checkbox label="document:write">文档写入</el-checkbox>
            <el-checkbox label="chat:use">智能问答</el-checkbox>
            <el-checkbox label="user:read">用户读取</el-checkbox>
            <el-checkbox label="system:read">系统读取</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="apiKeyDialog.form.expiresAt"
            type="date"
            placeholder="选择过期时间"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
          <span class="ml-2 text-sm text-gray-500">留空表示永不过期</span>
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input 
            v-model="apiKeyDialog.form.description" 
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="apiKeyDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="saveApiKey" :loading="savingKey">
            {{ apiKeyDialog.isEdit ? '保存' : '创建' }}
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
import type { SystemConfig, ApiKey, ApiKeyForm } from '@/types/system'
import {
  Plus,
  View,
  Hide,
  CopyDocument,
  Refresh
} from '@element-plus/icons-vue'

// 状态管理
const systemStore = useSystemStore()

// 系统配置
const systemConfig = ref<SystemConfig>({
  appName: 'QMS-Nexus',
  version: '1.0.0',
  sessionTimeout: 30,
  maxFileSize: 50,
  enableAnonymousAccess: false,
  requireApproval: false,
  similarityThreshold: 0.8
})

// API密钥管理
const apiKeys = ref<ApiKey[]>([])
const loadingKeys = ref(false)
const savingKey = ref(false)
const savingConfig = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const totalKeys = ref(0)
const visibleKeys = ref<Set<string>>(new Set())

// API密钥对话框
const apiKeyDialog = reactive({
  visible: false,
  isEdit: false,
  form: {
    id: '',
    name: '',
    permissions: [] as string[],
    expiresAt: '',
    description: ''
  } as ApiKeyForm
})

// 系统状态
const systemStatus = ref({
  status: 'ok',
  services: {
    database: 'connected',
    redis: 'connected',
    vectorDb: 'connected'
  },
  version: '1.0.0'
})

/**
 * 加载系统配置
 */
const loadSystemConfig = async () => {
  try {
    const config = await systemService.getSystemConfig()
    systemConfig.value = { ...systemConfig.value, ...config }
  } catch (error) {
    ElMessage.error('加载系统配置失败')
  }
}

/**
 * 保存系统配置
 */
const saveSystemConfig = async () => {
  savingConfig.value = true
  try {
    await systemService.updateSystemConfig(systemConfig.value)
    ElMessage.success('系统配置保存成功')
  } catch (error) {
    ElMessage.error('保存系统配置失败')
  } finally {
    savingConfig.value = false
  }
}

/**
 * 加载API密钥列表
 */
const loadApiKeys = async () => {
  loadingKeys.value = true
  try {
    const response = await systemService.getApiKeys(currentPage.value, pageSize.value)
    apiKeys.value = response.items.map(key => ({
      ...key,
      visible: visibleKeys.value.has(key.id)
    }))
    totalKeys.value = response.total
  } catch (error) {
    ElMessage.error('加载API密钥失败')
  } finally {
    loadingKeys.value = false
  }
}

/**
 * 显示添加API密钥对话框
 */
const showAddApiKeyDialog = () => {
  apiKeyDialog.isEdit = false
  apiKeyDialog.form = {
    id: '',
    name: '',
    permissions: [],
    expiresAt: '',
    description: ''
  }
  apiKeyDialog.visible = true
}

/**
 * 编辑API密钥
 */
const editApiKey = (key: ApiKey) => {
  apiKeyDialog.isEdit = true
  apiKeyDialog.form = {
    id: key.id,
    name: key.name,
    permissions: [...key.permissions],
    expiresAt: key.expiresAt || '',
    description: key.description || ''
  }
  apiKeyDialog.visible = true
}

/**
 * 保存API密钥
 */
const saveApiKey = async () => {
  if (!apiKeyDialog.form.name.trim()) {
    ElMessage.warning('请输入密钥名称')
    return
  }
  
  if (apiKeyDialog.form.permissions.length === 0) {
    ElMessage.warning('请至少选择一个权限')
    return
  }

  savingKey.value = true
  try {
    if (apiKeyDialog.isEdit) {
      await systemService.updateApiKey(apiKeyDialog.form.id, apiKeyDialog.form)
      ElMessage.success('API密钥更新成功')
    } else {
      await systemService.createApiKey(apiKeyDialog.form)
      ElMessage.success('API密钥创建成功')
    }
    
    apiKeyDialog.visible = false
    await loadApiKeys()
  } catch (error) {
    ElMessage.error(apiKeyDialog.isEdit ? '更新API密钥失败' : '创建API密钥失败')
  } finally {
    savingKey.value = false
  }
}

/**
 * 删除API密钥
 */
const deleteApiKey = async (key: ApiKey) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除API密钥 "${key.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await systemService.deleteApiKey(key.id)
    ElMessage.success('API密钥删除成功')
    await loadApiKeys()
  } catch {
    // 用户取消删除
  }
}

/**
 * 切换API密钥状态
 */
const toggleApiKeyStatus = async (key: ApiKey) => {
  try {
    const newStatus = key.status === 'active' ? 'inactive' : 'active'
    await systemService.updateApiKey(key.id, { status: newStatus })
    ElMessage.success(`API密钥已${newStatus === 'active' ? '启用' : '禁用'}`)
    await loadApiKeys()
  } catch (error) {
    ElMessage.error('更新API密钥状态失败')
    // 恢复状态
    key.status = key.status === 'active' ? 'inactive' : 'active'
  }
}

/**
 * 显示密钥
 */
const showKey = (key: string): string => {
  return key.slice(0, 8) + '...' + key.slice(-8)
}

/**
 * 切换密钥可见性
 */
const toggleKeyVisibility = (key: ApiKey) => {
  if (visibleKeys.value.has(key.id)) {
    visibleKeys.value.delete(key.id)
  } else {
    visibleKeys.value.add(key.id)
  }
}

/**
 * 复制密钥
 */
const copyKey = async (key: string) => {
  try {
    await navigator.clipboard.writeText(key)
    ElMessage.success('API密钥已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

/**
 * 查看API密钥日志
 */
const viewApiKeyLogs = (key: ApiKey) => {
  // 跳转到日志页面，筛选该密钥的日志
  ElMessage.info(`查看密钥 "${key.name}" 的使用日志`)
}

/**
 * 刷新系统状态
 */
const refreshSystemStatus = async () => {
  try {
    const status = await systemService.getSystemStatus()
    systemStatus.value = status
    ElMessage.success('系统状态已刷新')
  } catch (error) {
    ElMessage.error('刷新系统状态失败')
  }
}

/**
 * 获取权限文本
 */
const getPermissionText = (permission: string): string => {
  const permissionMap: Record<string, string> = {
    'document:read': '文档读取',
    'document:write': '文档写入',
    'chat:use': '智能问答',
    'user:read': '用户读取',
    'system:read': '系统读取'
  }
  return permissionMap[permission] || permission
}

/**
 * 格式化日期
 */
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadSystemConfig(),
    loadApiKeys(),
    refreshSystemStatus()
  ])
})
</script>

<style scoped>
/* 自定义样式 */
</style>