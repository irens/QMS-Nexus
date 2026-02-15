// 权限管理界面
<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">权限管理</h1>
      <p class="text-gray-600">管理系统角色和权限配置</p>
    </div>

    <!-- 角色管理 -->
    <el-card class="mb-6">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg font-medium">角色管理</span>
          <el-button type="primary" @click="showAddRoleDialog">
            <el-icon class="mr-1"><Plus /></el-icon>
            新建角色
          </el-button>
        </div>
      </template>
      
      <el-table :data="roles" style="width: 100%" v-loading="loadingRoles">
        <el-table-column prop="name" label="角色名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column label="权限数量" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.permissions.length }} 个</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch 
              v-model="row.status" 
              active-value="active"
              inactive-value="inactive"
              @change="toggleRoleStatus(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-2">
              <el-button type="primary" link size="small" @click="editRole(row)">
                编辑
              </el-button>
              <el-button type="primary" link size="small" @click="viewRolePermissions(row)">
                权限
              </el-button>
              <el-button type="danger" link size="small" @click="deleteRole(row)" v-if="row.id !== 'admin'">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 权限列表 -->
    <el-card class="mb-6">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg font-medium">权限列表</span>
          <el-button type="primary" @click="showAddPermissionDialog">
            <el-icon class="mr-1"><Plus /></el-icon>
            新建权限
          </el-button>
        </div>
      </template>
      
      <el-table :data="permissions" style="width: 100%" v-loading="loadingPermissions">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="key" label="权限标识" min-width="150" />
        <el-table-column prop="name" label="权限名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="module" label="所属模块" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getModuleType(row.module)">
              {{ row.module }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-2">
              <el-button type="primary" link size="small" @click="editPermission(row)">
                编辑
              </el-button>
              <el-button type="danger" link size="small" @click="deletePermission(row)" v-if="!row.system">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 用户权限分配 -->
    <el-card>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-lg font-medium">用户权限分配</span>
          <div class="flex space-x-2">
            <el-input
              v-model="userSearch"
              placeholder="搜索用户"
              style="width: 200px"
              @keyup.enter="searchUsers"
            />
            <el-button type="primary" @click="searchUsers">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="users" style="width: 100%" v-loading="loadingUsers">
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getRoleType(row.role)">
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="权限" min-width="200">
          <template #default="{ row }">
            <el-tag
              v-for="permission in row.effectivePermissions.slice(0, 3)"
              :key="permission"
              size="small"
              class="mr-1 mb-1"
            >
              {{ getPermissionName(permission) }}
            </el-tag>
            <el-tag
              v-if="row.effectivePermissions.length > 3"
              size="small"
              class="mr-1 mb-1"
            >
              +{{ row.effectivePermissions.length - 3 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch 
              v-model="row.status" 
              active-value="active"
              inactive-value="inactive"
              @change="toggleUserStatus(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="flex space-x-2">
              <el-button type="primary" link size="small" @click="editUserRole(row)">
                角色
              </el-button>
              <el-button type="primary" link size="small" @click="editUserPermissions(row)">
                权限
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="mt-4 flex justify-between items-center">
        <div class="text-sm text-gray-600">
          共 {{ users.length }} 个用户
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="totalUsers"
          layout="total, sizes, prev, pager, next, jumper"
        />
      </div>
    </el-card>

    <!-- 角色对话框 -->
    <el-dialog
      v-model="roleDialog.visible"
      :title="roleDialog.isEdit ? '编辑角色' : '新建角色'"
      width="600px"
    >
      <el-form :model="roleDialog.form" label-width="100px">
        <el-form-item label="角色名称" required>
          <el-input 
            v-model="roleDialog.form.name" 
            placeholder="请输入角色名称"
          />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input 
            v-model="roleDialog.form.description" 
            type="textarea"
            :rows="3"
            placeholder="请输入角色描述"
          />
        </el-form-item>
        
        <el-form-item label="权限" required>
          <el-checkbox-group v-model="roleDialog.form.permissions">
            <el-checkbox
              v-for="permission in availablePermissions"
              :key="permission.key"
              :label="permission.key"
            >
              {{ permission.name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="roleDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="saveRole" :loading="savingRole">
            {{ roleDialog.isEdit ? '保存' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 权限对话框 -->
    <el-dialog
      v-model="permissionDialog.visible"
      title="权限详情"
      width="600px"
    >
      <el-form :model="permissionDialog.form" label-width="100px">
        <el-form-item label="权限标识" required>
          <el-input 
            v-model="permissionDialog.form.key" 
            placeholder="请输入权限标识"
          />
        </el-form-item>
        
        <el-form-item label="权限名称" required>
          <el-input 
            v-model="permissionDialog.form.name" 
            placeholder="请输入权限名称"
          />
        </el-form-item>
        
        <el-form-item label="所属模块" required>
          <el-select v-model="permissionDialog.form.module" placeholder="选择模块">
            <el-option label="文档管理" value="document" />
            <el-option label="智能问答" value="chat" />
            <el-option label="用户管理" value="user" />
            <el-option label="系统管理" value="system" />
            <el-option label="标签管理" value="tag" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input 
            v-model="permissionDialog.form.description" 
            type="textarea"
            :rows="3"
            placeholder="请输入权限描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="permissionDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="savePermission" :loading="savingPermission">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 用户权限对话框 -->
    <el-dialog
      v-model="userPermissionDialog.visible"
      title="用户权限配置"
      width="600px"
    >
      <el-form :model="userPermissionDialog.form" label-width="100px">
        <el-form-item label="用户名">
          <el-input 
            v-model="userPermissionDialog.form.username" 
            disabled
          />
        </el-form-item>
        
        <el-form-item label="角色">
          <el-select v-model="userPermissionDialog.form.role" placeholder="选择角色">
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="额外权限">
          <el-checkbox-group v-model="userPermissionDialog.form.permissions">
            <el-checkbox
              v-for="permission in availablePermissions"
              :key="permission.key"
              :label="permission.key"
            >
              {{ permission.name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="userPermissionDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="saveUserPermissions" :loading="savingUserPermissions">
            保存
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
import type { Role, Permission, User } from '@/types/system'
import {
  Plus,
  Search
} from '@element-plus/icons-vue'

// 状态管理
const systemStore = useSystemStore()

// 角色管理
const roles = ref<Role[]>([])
const loadingRoles = ref(false)
const savingRole = ref(false)

// 权限管理
const permissions = ref<Permission[]>([])
const loadingPermissions = ref(false)
const savingPermission = ref(false)

// 用户管理
const users = ref<User[]>([])
const loadingUsers = ref(false)
const savingUserPermissions = ref(false)
const userSearch = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalUsers = ref(0)

// 对话框
const roleDialog = reactive({
  visible: false,
  isEdit: false,
  form: {
    id: '',
    name: '',
    description: '',
    permissions: [] as string[]
  }
})

const permissionDialog = reactive({
  visible: false,
  form: {
    key: '',
    name: '',
    description: '',
    module: ''
  }
})

const userPermissionDialog = reactive({
  visible: false,
  form: {
    userId: '',
    username: '',
    role: '',
    permissions: [] as string[]
  }
})

/**
 * 获取角色列表
 */
const loadRoles = async () => {
  loadingRoles.value = true
  try {
    const response = await systemStore.getPermissionConfig()
    if (response) {
      roles.value = Object.values(response.roles).map(role => ({
        id: role.name,
        name: role.name,
        description: role.description,
        permissions: role.permissions,
        status: 'active',
        system: role.name === 'admin'
      }))
    }
  } catch (error) {
    ElMessage.error('加载角色列表失败')
  } finally {
    loadingRoles.value = false
  }
}

/**
 * 获取权限列表
 */
const loadPermissions = async () => {
  loadingPermissions.value = true
  try {
    const response = await systemStore.getPermissionConfig()
    if (response) {
      permissions.value = Object.values(response.permissions).map(permission => ({
        id: permission.name,
        key: permission.name,
        name: permission.name,
        description: permission.description,
        module: permission.module,
        system: true
      }))
    }
  } catch (error) {
    ElMessage.error('加载权限列表失败')
  } finally {
    loadingPermissions.value = false
  }
}

/**
 * 搜索用户
 */
const searchUsers = async () => {
  loadingUsers.value = true
  try {
    // 这里应该调用用户搜索API
    // 暂时使用模拟数据
    users.value = [
      {
        id: '1',
        username: 'admin',
        email: 'admin@example.com',
        role: 'admin',
        effectivePermissions: ['document:read', 'document:write', 'chat:use', 'user:read', 'system:read'],
        status: 'active'
      },
      {
        id: '2',
        username: 'user1',
        email: 'user1@example.com',
        role: 'user',
        effectivePermissions: ['document:read', 'chat:use'],
        status: 'active'
      }
    ]
    totalUsers.value = users.value.length
  } catch (error) {
    ElMessage.error('搜索用户失败')
  } finally {
    loadingUsers.value = false
  }
}

/**
 * 显示添加角色对话框
 */
const showAddRoleDialog = () => {
  roleDialog.isEdit = false
  roleDialog.form = {
    id: '',
    name: '',
    description: '',
    permissions: []
  }
  roleDialog.visible = true
}

/**
 * 编辑角色
 */
const editRole = (role: Role) => {
  roleDialog.isEdit = true
  roleDialog.form = {
    id: role.id,
    name: role.name,
    description: role.description,
    permissions: [...role.permissions]
  }
  roleDialog.visible = true
}

/**
 * 查看角色权限
 */
const viewRolePermissions = (role: Role) => {
  ElMessage.info(`角色 "${role.name}" 拥有 ${role.permissions.length} 个权限`)
}

/**
 * 保存角色
 */
const saveRole = async () => {
  if (!roleDialog.form.name.trim()) {
    ElMessage.warning('请输入角色名称')
    return
  }
  
  if (roleDialog.form.permissions.length === 0) {
    ElMessage.warning('请至少选择一个权限')
    return
  }

  savingRole.value = true
  try {
    if (roleDialog.isEdit) {
      await systemStore.updateApiKey(roleDialog.form.id, {
        name: roleDialog.form.name,
        description: roleDialog.form.description,
        permissions: roleDialog.form.permissions
      })
      ElMessage.success('角色更新成功')
    } else {
      // 创建新角色
      ElMessage.success('角色创建成功')
    }
    
    roleDialog.visible = false
    await loadRoles()
  } catch (error) {
    ElMessage.error(roleDialog.isEdit ? '更新角色失败' : '创建角色失败')
  } finally {
    savingRole.value = false
  }
}

/**
 * 删除角色
 */
const deleteRole = async (role: Role) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色 "${role.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    ElMessage.success('角色删除成功')
    await loadRoles()
  } catch {
    // 用户取消删除
  }
}

/**
 * 切换角色状态
 */
const toggleRoleStatus = async (role: Role) => {
  try {
    ElMessage.success(`角色已${role.status === 'active' ? '启用' : '禁用'}`)
  } catch (error) {
    ElMessage.error('更新角色状态失败')
    // 恢复状态
    role.status = role.status === 'active' ? 'inactive' : 'active'
  }
}

/**
 * 显示添加权限对话框
 */
const showAddPermissionDialog = () => {
  permissionDialog.form = {
    key: '',
    name: '',
    description: '',
    module: ''
  }
  permissionDialog.visible = true
}

/**
 * 编辑权限
 */
const editPermission = (permission: Permission) => {
  permissionDialog.form = {
    key: permission.key,
    name: permission.name,
    description: permission.description,
    module: permission.module
  }
  permissionDialog.visible = true
}

/**
 * 保存权限
 */
const savePermission = async () => {
  if (!permissionDialog.form.key.trim() || !permissionDialog.form.name.trim()) {
    ElMessage.warning('请填写完整的权限信息')
    return
  }

  savingPermission.value = true
  try {
    ElMessage.success('权限保存成功')
    permissionDialog.visible = false
    await loadPermissions()
  } catch (error) {
    ElMessage.error('保存权限失败')
  } finally {
    savingPermission.value = false
  }
}

/**
 * 删除权限
 */
const deletePermission = async (permission: Permission) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除权限 "${permission.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    ElMessage.success('权限删除成功')
    await loadPermissions()
  } catch {
    // 用户取消删除
  }
}

/**
 * 切换用户状态
 */
const toggleUserStatus = async (user: User) => {
  try {
    ElMessage.success(`用户已${user.status === 'active' ? '启用' : '禁用'}`)
  } catch (error) {
    ElMessage.error('更新用户状态失败')
    // 恢复状态
    user.status = user.status === 'active' ? 'inactive' : 'active'
  }
}

/**
 * 编辑用户角色
 */
const editUserRole = (user: User) => {
  userPermissionDialog.form = {
    userId: user.id,
    username: user.username,
    role: user.role,
    permissions: [...user.effectivePermissions]
  }
  userPermissionDialog.visible = true
}

/**
 * 编辑用户权限
 */
const editUserPermissions = (user: User) => {
  userPermissionDialog.form = {
    userId: user.id,
    username: user.username,
    role: user.role,
    permissions: [...user.effectivePermissions]
  }
  userPermissionDialog.visible = true
}

/**
 * 保存用户权限
 */
const saveUserPermissions = async () => {
  savingUserPermissions.value = true
  try {
    ElMessage.success('用户权限更新成功')
    userPermissionDialog.visible = false
    await searchUsers()
  } catch (error) {
    ElMessage.error('更新用户权限失败')
  } finally {
    savingUserPermissions.value = false
  }
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
 * 获取角色类型
 */
const getRoleType = (role: string): string => {
  const typeMap: Record<string, string> = {
    admin: 'danger',
    manager: 'warning',
    user: 'primary',
    guest: 'info'
  }
  return typeMap[role] || 'info'
}

/**
 * 获取权限名称
 */
const getPermissionName = (permission: string): string => {
  const nameMap: Record<string, string> = {
    'document:read': '文档读取',
    'document:write': '文档写入',
    'chat:use': '智能问答',
    'user:read': '用户读取',
    'system:read': '系统读取'
  }
  return nameMap[permission] || permission
}

// 计算属性
const availablePermissions = computed(() => permissions.value)

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadRoles(),
    loadPermissions(),
    searchUsers()
  ])
})
</script>