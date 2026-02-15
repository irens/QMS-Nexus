// 移动端导航组件
<template>
  <div class="mobile-nav" v-if="isMobile">
    <!-- 顶部导航栏 -->
    <div class="mobile-header">
      <div class="mobile-header-content">
        <el-button
          :icon="Menu"
          circle
          size="small"
          @click="showDrawer = true"
        />
        <div class="mobile-title">{{ currentTitle }}</div>
        <el-button
          :icon="Search"
          circle
          size="small"
          @click="showSearch = true"
        />
      </div>
    </div>

    <!-- 搜索抽屉 -->
    <el-drawer
      v-model="showSearch"
      direction="ttb"
      size="auto"
      :with-header="false"
    >
      <div class="mobile-search">
        <el-input
          v-model="searchQuery"
          placeholder="搜索文档、标签..."
          size="large"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <div class="mobile-search-suggestions">
          <div class="search-suggestion-item" @click="handleSearch">
            <el-icon><Document /></el-icon>
            <span>搜索文档</span>
          </div>
          <div class="search-suggestion-item" @click="handleSearch">
            <el-icon><CollectionTag /></el-icon>
            <span>搜索标签</span>
          </div>
        </div>
      </div>
    </el-drawer>

    <!-- 侧边导航抽屉 -->
    <el-drawer
      v-model="showDrawer"
      direction="ltr"
      size="80%"
      :with-header="false"
    >
      <div class="mobile-drawer">
        <div class="mobile-drawer-header">
          <div class="mobile-drawer-title">QMS-Nexus</div>
          <el-button
            :icon="Close"
            circle
            size="small"
            @click="showDrawer = false"
          />
        </div>
        
        <el-menu
          :default-active="activeMenu"
          class="mobile-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="dashboard">
            <el-icon><House /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>

          <el-sub-menu index="documents">
            <template #title>
              <el-icon><Document /></el-icon>
              <span>文档管理</span>
            </template>
            <el-menu-item index="upload">
              <el-icon><Upload /></el-icon>
              <span>文件上传</span>
            </el-menu-item>
            <el-menu-item index="document-list">
              <el-icon><DocumentCopy /></el-icon>
              <span>文档列表</span>
            </el-menu-item>
            <el-menu-item index="tags">
              <el-icon><CollectionTag /></el-icon>
              <span>标签管理</span>
            </el-menu-item>
          </el-sub-menu>

          <el-menu-item index="chat">
            <el-icon><ChatDotRound /></el-icon>
            <span>智能问答</span>
          </el-menu-item>

          <el-menu-item index="search">
            <el-icon><Search /></el-icon>
            <span>文档搜索</span>
          </el-menu-item>

          <el-sub-menu index="system" v-if="isAdmin">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item index="users">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="logs">
              <el-icon><DocumentChecked /></el-icon>
              <span>操作日志</span>
            </el-menu-item>
            <el-menu-item index="settings">
              <el-icon><Tools /></el-icon>
              <span>系统设置</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>

        <div class="mobile-drawer-footer">
          <div class="user-info">
            <el-avatar size="small" :icon="User" />
            <span class="username">管理员</span>
          </div>
          <el-button type="danger" size="small" @click="handleLogout">
            退出登录
          </el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 底部导航栏 -->
    <div class="mobile-footer">
      <div 
        v-for="item in bottomNavItems" 
        :key="item.key"
        class="mobile-footer-item"
        :class="{ active: activeBottomNav === item.key }"
        @click="handleBottomNavClick(item)"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span class="mobile-footer-text">{{ item.title }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useResponsive } from '@/utils/responsive'
import {
  Menu,
  Search,
  Close,
  House,
  Document,
  Upload,
  DocumentCopy,
  CollectionTag,
  ChatDotRound,
  Setting,
  User,
  DocumentChecked,
  Tools
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const { isMobile } = useResponsive()

// 状态
const showDrawer = ref(false)
const showSearch = ref(false)
const searchQuery = ref('')
const activeBottomNav = ref('dashboard')

// 底部导航项
const bottomNavItems = [
  { key: 'dashboard', title: '首页', icon: House },
  { key: 'documents', title: '文档', icon: Document },
  { key: 'chat', title: '问答', icon: ChatDotRound },
  { key: 'search', title: '搜索', icon: Search },
  { key: 'system', title: '设置', icon: Setting }
]

// 计算属性
const currentTitle = computed(() => {
  const path = route.path
  if (path.includes('/dashboard')) return '仪表盘'
  if (path.includes('/upload')) return '文件上传'
  if (path.includes('/documents')) return '文档列表'
  if (path.includes('/tags')) return '标签管理'
  if (path.includes('/chat')) return '智能问答'
  if (path.includes('/search')) return '文档搜索'
  if (path.includes('/users')) return '用户管理'
  if (path.includes('/logs')) return '操作日志'
  if (path.includes('/settings')) return '系统设置'
  return 'QMS-Nexus'
})

const isAdmin = computed(() => true) // 这里应该从权限系统获取

const activeMenu = computed(() => {
  const path = route.path
  if (path.includes('/upload')) return 'upload'
  if (path.includes('/documents')) return 'document-list'
  if (path.includes('/tags')) return 'tags'
  if (path.includes('/chat')) return 'chat'
  if (path.includes('/search')) return 'search'
  if (path.includes('/users')) return 'users'
  if (path.includes('/logs')) return 'logs'
  if (path.includes('/settings')) return 'settings'
  return 'dashboard'
})

// 方法
const handleMenuSelect = (index: string) => {
  const routes: Record<string, string> = {
    'dashboard': '/',
    'upload': '/upload',
    'document-list': '/documents',
    'tags': '/tags',
    'chat': '/chat',
    'search': '/search',
    'users': '/system/users',
    'logs': '/system/logs',
    'settings': '/system/settings'
  }
  
  const path = routes[index]
  if (path) {
    router.push(path)
    showDrawer.value = false
  }
}

const handleBottomNavClick = (item: any) => {
  activeBottomNav.value = item.key
  
  switch (item.key) {
    case 'dashboard':
      router.push('/system')
      break
    case 'documents':
      router.push('/system/documents')
      break
    case 'chat':
      router.push('/system/chat')
      break
    case 'search':
      router.push('/system/search')
      break
    case 'system':
      router.push('/system/settings')
      break
  }
}

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      path: '/system/search',
      query: { q: searchQuery.value.trim() }
    })
    showSearch.value = false
    searchQuery.value = ''
  }
}

const handleLogout = () => {
  // 这里应该调用退出登录的API
  ElMessage.success('已退出登录')
  showDrawer.value = false
}

// 监听路由变化
watch(() => route.path, (newPath) => {
  if (newPath.includes('/dashboard')) activeBottomNav.value = 'dashboard'
  else if (newPath.includes('/documents')) activeBottomNav.value = 'documents'
  else if (newPath.includes('/chat')) activeBottomNav.value = 'chat'
  else if (newPath.includes('/search')) activeBottomNav.value = 'search'
  else if (newPath.includes('/system')) activeBottomNav.value = 'system'
})
</script>

<style scoped>
.mobile-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.mobile-header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  padding: 12px 16px;
}

.mobile-header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mobile-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  flex: 1;
  text-align: center;
}

.mobile-search {
  padding: 20px;
}

.mobile-search-suggestions {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-suggestion-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: #f5f7fa;
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-suggestion-item:hover {
  background: #e4e7ed;
}

.mobile-drawer {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.mobile-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.mobile-drawer-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.mobile-menu {
  flex: 1;
  border-right: none;
}

.mobile-drawer-footer {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  font-size: 14px;
  color: #606266;
}

.mobile-footer {
  background: white;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-around;
  padding: 8px 0;
}

.mobile-footer-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  cursor: pointer;
  transition: color 0.2s;
  color: #909399;
}

.mobile-footer-item:hover {
  color: #409eff;
}

.mobile-footer-item.active {
  color: #409eff;
}

.mobile-footer-text {
  font-size: 12px;
  font-weight: 500;
}
</style>