// 用户状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types/api'
import { APP_CONFIG } from '@/constants'

export interface UserState {
  currentUser: User | null
  users: User[]
  loading: boolean
  error: string | null
  permissions: string[]
  roles: string[]
}

export const useUserStore = defineStore('user', () => {
  // 状态
  const currentUser = ref<User | null>(null)
  const users = ref<User[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const permissions = ref<string[]>([])
  const roles = ref<string[]>(['admin', 'user', 'guest'])
  
  // 计算属性
  const isLoggedIn = computed(() => currentUser.value !== null)
  const isAdmin = computed(() => currentUser.value?.role === 'admin')
  const isUser = computed(() => currentUser.value?.role === 'user')
  const isGuest = computed(() => currentUser.value?.role === 'guest')
  
  const activeUsers = computed(() => users.value.filter(user => user.status === 'active'))
  const inactiveUsers = computed(() => users.value.filter(user => user.status === 'inactive'))
  
  const usersByRole = computed(() => {
    const map = new Map<string, User[]>()
    users.value.forEach(user => {
      const list = map.get(user.role) || []
      list.push(user)
      map.set(user.role, list)
    })
    return map
  })
  
  const usersByDepartment = computed(() => {
    const map = new Map<string, User[]>()
    users.value.forEach(user => {
      const dept = user.department || '未分配'
      const list = map.get(dept) || []
      list.push(user)
      map.set(dept, list)
    })
    return map
  })
  
  // 方法
  /**
   * 用户登录
   */
  async function login(email: string, _password: string): Promise<boolean> {
    try {
      loading.value = true
      error.value = null
      
      // 模拟登录API调用
      // 实际项目中这里应该调用真实的登录API
      const mockUser: User = {
        id: '1',
        name: '管理员',
        email: email,
        role: 'admin',
        department: 'IT部门',
        phone: '13800138000',
        status: 'active',
        createdAt: '2024-01-01',
        lastLogin: new Date().toISOString(),
        lastLoginIp: '192.168.1.100',
        permissions: [
          'document:view', 'document:upload', 'document:download', 'document:delete', 'document:edit',
          'tag:view', 'tag:create', 'tag:edit', 'tag:delete',
          'chat:use', 'chat:history',
          'user:view', 'user:create', 'user:edit', 'user:delete', 'user:role',
          'system:view', 'system:config', 'system:logs'
        ]
      }
      
      // 模拟API延迟
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      currentUser.value = mockUser
      permissions.value = mockUser.permissions
      
      // 保存到本地存储
      localStorage.setItem(APP_CONFIG.STORAGE_KEYS.USER_INFO, JSON.stringify(mockUser))
      localStorage.setItem(APP_CONFIG.STORAGE_KEYS.TOKEN, 'mock_token_' + Date.now())
      
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '登录失败'
      return false
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 用户登出
   */
  async function logout(): Promise<void> {
    try {
      loading.value = true
      error.value = null
      
      // 模拟登出API调用
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 清理本地数据
      currentUser.value = null
      permissions.value = []
      localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.USER_INFO)
      localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.TOKEN)
      
    } catch (err) {
      error.value = err instanceof Error ? err.message : '登出失败'
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取用户信息
   */
  async function fetchCurrentUser(): Promise<void> {
    try {
      loading.value = true
      error.value = null
      
      // 从本地存储获取用户信息
      const userInfo = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.USER_INFO)
      if (userInfo) {
        currentUser.value = JSON.parse(userInfo)
        permissions.value = currentUser.value?.permissions || []
      }
      
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取用户信息失败'
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取用户列表
   */
  async function fetchUsers(): Promise<void> {
    try {
      loading.value = true
      error.value = null
      
      // 模拟获取用户列表API调用
      await new Promise(resolve => setTimeout(resolve, 800))
      
      // 模拟用户数据
      users.value = [
        {
          id: '1',
          name: '张三',
          email: 'zhangsan@example.com',
          role: 'admin',
          department: 'IT部门',
          phone: '13800138000',
          status: 'active',
          createdAt: '2024-01-01',
          lastLogin: '2024-01-15T10:30:00Z',
          lastLoginIp: '192.168.1.100',
          permissions: ['document:view', 'document:upload', 'user:view', 'user:create']
        },
        {
          id: '2',
          name: '李四',
          email: 'lisi@example.com',
          role: 'user',
          department: '质量部门',
          phone: '13900139000',
          status: 'active',
          createdAt: '2024-01-02',
          lastLogin: '2024-01-14T15:20:00Z',
          lastLoginIp: '192.168.1.101',
          permissions: ['document:view', 'document:upload', 'chat:use']
        },
        {
          id: '3',
          name: '王五',
          email: 'wangwu@example.com',
          role: 'guest',
          department: '行政部门',
          phone: '13700137000',
          status: 'inactive',
          createdAt: '2024-01-03',
          permissions: ['document:view']
        }
      ]
      
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取用户列表失败'
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 创建用户
   */
  async function createUser(userData: {
    name: string
    email: string
    role: 'admin' | 'user' | 'guest'
    department?: string
    phone?: string
  }): Promise<boolean> {
    try {
      loading.value = true
      error.value = null
      
      // 模拟创建用户API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 模拟创建新用户
      const newUser: User = {
        id: Date.now().toString(),
        name: userData.name,
        email: userData.email,
        role: userData.role,
        department: userData.department || '',
        phone: userData.phone || '',
        status: 'active',
        createdAt: new Date().toISOString(),
        permissions: getRolePermissions(userData.role)
      }
      
      users.value.push(newUser)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '创建用户失败'
      return false
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 更新用户
   */
  async function updateUser(userId: string, userData: Partial<User>): Promise<boolean> {
    try {
      loading.value = true
      error.value = null
      
      // 模拟更新用户API调用
      await new Promise(resolve => setTimeout(resolve, 800))
      
      // 更新本地数据
      const index = users.value.findIndex(user => user.id === userId)
      if (index !== -1) {
        users.value[index] = { ...users.value[index], ...userData }
        
        // 如果是当前用户，也更新currentUser
        if (currentUser.value?.id === userId) {
          currentUser.value = { ...currentUser.value, ...userData } as User
          localStorage.setItem(APP_CONFIG.STORAGE_KEYS.USER_INFO, JSON.stringify(currentUser.value))
        }
      }
      
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新用户失败'
      return false
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 删除用户
   */
  async function deleteUser(userId: string): Promise<boolean> {
    try {
      loading.value = true
      error.value = null
      
      // 不能删除自己
      if (currentUser.value?.id === userId) {
        error.value = '不能删除当前登录用户'
        return false
      }
      
      // 模拟删除用户API调用
      await new Promise(resolve => setTimeout(resolve, 800))
      
      // 从列表中移除
      const index = users.value.findIndex(user => user.id === userId)
      if (index !== -1) {
        users.value.splice(index, 1)
      }
      
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除用户失败'
      return false
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 更新用户状态
   */
  async function updateUserStatus(userId: string, status: 'active' | 'inactive'): Promise<boolean> {
    return updateUser(userId, { status })
  }
  
  /**
   * 检查权限
   */
  function hasPermission(permission: string): boolean {
    return permissions.value.includes(permission)
  }
  
  /**
   * 检查多个权限（满足任意一个）
   */
  function hasAnyPermission(...permissions: string[]): boolean {
    return permissions.some(permission => hasPermission(permission))
  }
  
  /**
   * 检查多个权限（满足所有）
   */
  function hasAllPermissions(...permissions: string[]): boolean {
    return permissions.every(permission => hasPermission(permission))
  }
  
  /**
   * 检查角色
   */
  function hasRole(role: string): boolean {
    return currentUser.value?.role === role
  }
  
  /**
   * 检查多个角色（满足任意一个）
   */
  function hasAnyRole(...roles: string[]): boolean {
    return roles.some(role => hasRole(role))
  }
  
  /**
   * 获取角色权限
   */
  function getRolePermissions(role: 'admin' | 'user' | 'guest'): string[] {
    const permissions = {
      admin: [
        'document:view', 'document:upload', 'document:download', 'document:delete', 'document:edit',
        'tag:view', 'tag:create', 'tag:edit', 'tag:delete',
        'chat:use', 'chat:history',
        'user:view', 'user:create', 'user:edit', 'user:delete', 'user:role',
        'system:view', 'system:config', 'system:logs'
      ],
      user: [
        'document:view', 'document:upload', 'document:download',
        'tag:view',
        'chat:use', 'chat:history',
        'user:view'
      ],
      guest: [
        'document:view',
        'tag:view',
        'chat:use'
      ]
    }
    
    return permissions[role] || []
  }
  
  /**
   * 重置状态
   */
  function reset(): void {
    currentUser.value = null
    users.value = []
    loading.value = false
    error.value = null
    permissions.value = []
  }
  
  return {
    // 状态
    currentUser,
    users,
    loading,
    error,
    permissions,
    roles,
    
    // 计算属性
    isLoggedIn,
    isAdmin,
    isUser,
    isGuest,
    activeUsers,
    inactiveUsers,
    usersByRole,
    usersByDepartment,
    
    // 方法
    login,
    logout,
    fetchCurrentUser,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    updateUserStatus,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    getRolePermissions,
    reset
  }
})