<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">用户管理</h1>
      <p class="text-gray-600">管理系统用户账户和权限</p>
    </div>

    <!-- 搜索和操作栏 -->
    <div class="mb-6">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-input
            v-model="searchQuery"
            placeholder="搜索用户姓名或邮箱..."
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
          <el-select v-model="selectedRole" placeholder="角色筛选" clearable @change="handleSearch">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
            <el-option label="访客" value="guest" />
          </el-select>
        </el-col>
        <el-col :span="6" class="text-right">
          <el-button type="primary" @click="showAddDialog">
            <el-icon class="mr-2"><Plus /></el-icon>
            添加用户
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 用户列表 -->
    <div class="mb-6">
      <el-table 
        :data="filteredUsers" 
        style="width: 100%"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column label="用户信息" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center space-x-3">
              <el-avatar size="small" :icon="User" />
              <div>
                <p class="text-sm font-medium text-gray-800">{{ row.name }}</p>
                <p class="text-xs text-gray-500">{{ row.email }}</p>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small">
              {{ getRoleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              active-value="active"
              inactive-value="inactive"
              @change="handleStatusChange(row)"
            />
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>

        <el-table-column label="最后登录" width="150">
          <template #default="{ row }">
            <div v-if="row.lastLogin">
              <p class="text-sm">{{ formatDate(row.lastLogin) }}</p>
              <p class="text-xs text-gray-500">{{ row.lastLoginIp }}</p>
            </div>
            <div v-else class="text-sm text-gray-400">从未登录</div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-2">
              <el-button
                type="primary"
                link
                size="small"
                @click="editUser(row)"
              >
                编辑
              </el-button>
              <el-button
                type="primary"
                link
                size="small"
                @click="resetPassword(row)"
              >
                重置密码
              </el-button>
              <el-dropdown>
                <el-button type="primary" link size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="viewUserDetail(row)">
                      <el-icon><User /></el-icon>
                      查看详情
                    </el-dropdown-item>
                    <el-dropdown-item @click="assignRole(row)">
                      <el-icon><Key /></el-icon>
                      分配角色
                    </el-dropdown-item>
                    <el-dropdown-item divided @click="deleteUser(row)">
                      <el-icon><Delete /></el-icon>
                      删除用户
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
        共 {{ totalUsers }} 个用户，已选择 {{ selectedUsers.length }} 个
      </div>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalUsers"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 添加/编辑用户对话框 -->
    <el-dialog
      v-model="userDialog.visible"
      :title="userDialog.isEdit ? '编辑用户' : '添加用户'"
      width="500px"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">姓名</label>
          <el-input
            v-model="userDialog.form.name"
            placeholder="请输入用户姓名"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">邮箱</label>
          <el-input
            v-model="userDialog.form.email"
            placeholder="请输入邮箱地址"
            :disabled="userDialog.isEdit"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">角色</label>
          <el-select v-model="userDialog.form.role" class="w-full">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
            <el-option label="访客" value="guest" />
          </el-select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">部门</label>
          <el-input
            v-model="userDialog.form.department"
            placeholder="请输入部门名称"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">电话</label>
          <el-input
            v-model="userDialog.form.phone"
            placeholder="请输入联系电话"
          />
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="userDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="saveUser">
            {{ userDialog.isEdit ? '保存' : '添加' }}
          </el-button>
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
  Plus,
  User,
  MoreFilled,
  Key,
  Delete
} from '@element-plus/icons-vue'

interface UserItem {
  id: string
  name: string
  email: string
  role: 'admin' | 'user' | 'guest'
  department: string
  phone: string
  status: 'active' | 'inactive'
  createdAt: string
  lastLogin?: string
  lastLoginIp?: string
}

// 搜索和筛选
const searchQuery = ref('')
const selectedRole = ref('')

// 表格数据
const loading = ref(false)
const selectedUsers = ref<UserItem[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const totalUsers = ref(100)

// 模拟用户数据
const users = ref<UserItem[]>([
  {
    id: '1',
    name: '张三',
    email: 'zhangsan@example.com',
    role: 'admin',
    department: '质量管理部',
    phone: '13800138000',
    status: 'active',
    createdAt: '2024-01-15',
    lastLogin: '2024-01-15 14:30',
    lastLoginIp: '192.168.1.100'
  },
  {
    id: '2',
    name: '李四',
    email: 'lisi@example.com',
    role: 'user',
    department: '医疗部',
    phone: '13900139000',
    status: 'active',
    createdAt: '2024-01-14',
    lastLogin: '2024-01-15 10:15',
    lastLoginIp: '192.168.1.101'
  },
  {
    id: '3',
    name: '王五',
    email: 'wangwu@example.com',
    role: 'user',
    department: '护理部',
    phone: '13700137000',
    status: 'inactive',
    createdAt: '2024-01-13',
    lastLogin: '2024-01-10 16:45',
    lastLoginIp: '192.168.1.102'
  },
  {
    id: '4',
    name: '赵六',
    email: 'zhaoliu@example.com',
    role: 'guest',
    department: '行政部',
    phone: '13600136000',
    status: 'active',
    createdAt: '2024-01-12',
    lastLogin: undefined,
    lastLoginIp: undefined
  }
])

// 用户对话框
const userDialog = reactive({
  visible: false,
  isEdit: false,
  form: {
    id: '',
    name: '',
    email: '',
    role: 'user' as 'admin' | 'user' | 'guest',
    department: '',
    phone: ''
  }
})

// 筛选后的用户
const filteredUsers = computed(() => {
  let result = users.value

  // 搜索筛选
  if (searchQuery.value) {
    result = result.filter(user => 
      user.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }

  // 角色筛选
  if (selectedRole.value) {
    result = result.filter(user => user.role === selectedRole.value)
  }

  return result
})

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1
  // 这里可以调用API重新获取数据
}

// 处理选择变化
const handleSelectionChange = (val: UserItem[]) => {
  selectedUsers.value = val
}

// 处理分页
const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
}

// 获取角色类型
const getRoleType = (role: string) => {
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    admin: 'danger',
    user: 'primary',
    guest: 'info'
  }
  return typeMap[role] || 'info'
}

// 获取角色文本
const getRoleText = (role: string) => {
  const textMap: Record<string, string> = {
    admin: '管理员',
    user: '普通用户',
    guest: '访客'
  }
  return textMap[role] || role
}

// 处理状态变化
const handleStatusChange = (row: UserItem) => {
  const statusText = row.status === 'active' ? '启用' : '禁用'
  ElMessage.success(`用户${row.name}已${statusText}`)
}

// 显示添加对话框
const showAddDialog = () => {
  userDialog.isEdit = false
  userDialog.form = {
    id: '',
    name: '',
    email: '',
    role: 'user',
    department: '',
    phone: ''
  }
  userDialog.visible = true
}

// 编辑用户
const editUser = (row: UserItem) => {
  userDialog.isEdit = true
  userDialog.form = {
    id: row.id,
    name: row.name,
    email: row.email,
    role: row.role,
    department: row.department,
    phone: row.phone
  }
  userDialog.visible = true
}

// 保存用户
const saveUser = () => {
  if (!userDialog.form.name.trim()) {
    ElMessage.warning('请输入用户姓名')
    return
  }
  
  if (!userDialog.form.email.trim()) {
    ElMessage.warning('请输入邮箱地址')
    return
  }
  
  if (userDialog.isEdit) {
    // 编辑用户
    const user = users.value.find(u => u.id === userDialog.form.id)
    if (user) {
      user.name = userDialog.form.name
      user.role = userDialog.form.role
      user.department = userDialog.form.department
      user.phone = userDialog.form.phone
      ElMessage.success('用户更新成功')
    }
  } else {
    // 添加用户
    const newUser: UserItem = {
      id: Date.now().toString(),
      name: userDialog.form.name,
      email: userDialog.form.email,
      role: userDialog.form.role,
      department: userDialog.form.department,
      phone: userDialog.form.phone,
      status: 'active',
      createdAt: new Date().toISOString().split('T')[0]
    }
    users.value.unshift(newUser)
    ElMessage.success('用户添加成功')
  }
  
  userDialog.visible = false
}

// 重置密码
const resetPassword = async (row: UserItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要重置用户 "${row.name}" 的密码吗？`,
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    ElMessage.success(`密码重置成功，新密码已发送到 ${row.email}`)
  } catch {
    // 用户取消
  }
}

// 查看用户详情
const viewUserDetail = (row: UserItem) => {
  ElMessage.info(`查看用户详情: ${row.name}`)
}

// 分配角色
const assignRole = (row: UserItem) => {
  ElMessage.info(`分配角色: ${row.name}`)
}

// 删除用户
const deleteUser = async (row: UserItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = users.value.findIndex(u => u.id === row.id)
    if (index > -1) {
      users.value.splice(index, 1)
    }
    
    ElMessage.success('用户删除成功')
  } catch {
    // 用户取消删除
  }
}

// 工具函数
const formatDate = (dateString: string): string => {
  if (!dateString) return '从未登录'
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
/* 自定义样式 */
</style>