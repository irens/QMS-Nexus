<template>
  <el-container class="min-h-screen bg-gray-50">
    <!-- 顶部导航栏 -->
    <el-header class="bg-white shadow-sm border-b border-gray-200 px-0">
      <nav class="flex items-center justify-between h-16 px-6">
        <!-- Logo和标题 -->
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2">
            <el-icon size="24" class="text-primary-500">
              <FirstAidKit />
            </el-icon>
            <h1 class="text-xl font-semibold text-gray-800">QMS-Nexus</h1>
            <span class="text-sm text-gray-500">医疗质量管理系统</span>
          </div>
        </div>

        <!-- 右侧功能区 -->
        <div class="flex items-center space-x-4">
          <!-- 搜索框 -->
          <div class="hidden md:block">
            <el-input
              v-model="searchQuery"
              placeholder="搜索文档..."
              class="w-64"
              size="small"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>

          <!-- 通知 -->
          <el-badge :value="3" class="item">
            <el-button :icon="Bell" circle size="small" />
          </el-badge>

          <!-- 用户菜单 -->
          <el-dropdown>
            <div class="flex items-center space-x-2 cursor-pointer">
              <el-avatar size="small" :icon="User" />
              <span class="text-sm text-gray-700">管理员</span>
              <el-icon><CaretBottom /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人设置</el-dropdown-item>
                <el-dropdown-item>系统管理</el-dropdown-item>
                <el-dropdown-item divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <!-- 移动端菜单按钮 -->
          <el-button
            :icon="isCollapse ? Expand : Fold"
            circle
            size="small"
            @click="toggleSidebar"
            class="md:hidden"
          />
        </div>
      </nav>
    </el-header>

    <el-container>
      <!-- 侧边栏 -->
      <el-aside 
        :width="isCollapse ? '64px' : '240px'"
        class="bg-white shadow-sm transition-all duration-300"
      >
        <div class="h-full flex flex-col">
          <!-- 侧边栏头部 -->
          <div class="p-4 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <div v-if="!isCollapse" class="flex items-center space-x-2">
                <el-icon class="text-primary-500"><Operation /></el-icon>
                <span class="text-sm font-medium text-gray-700">功能菜单</span>
              </div>
              <el-button
                :icon="isCollapse ? Expand : Fold"
                text
                size="small"
                @click="toggleSidebar"
                class="hidden md:block"
              />
            </div>
          </div>

          <!-- 菜单 -->
          <el-menu
            :default-active="activeMenu"
            :collapse="isCollapse"
            :collapse-transition="false"
            class="flex-1 border-r-0"
            @select="handleMenuSelect"
          >
            <el-menu-item index="dashboard">
              <el-icon><House /></el-icon>
              <template #title>仪表盘</template>
            </el-menu-item>

            <el-sub-menu index="documents">
              <template #title>
                <el-icon><Document /></el-icon>
                <span>文档管理</span>
              </template>
              <el-menu-item index="upload">
                <el-icon><Upload /></el-icon>
                <template #title>文件上传</template>
              </el-menu-item>
              <el-menu-item index="documents">
                <el-icon><DocumentCopy /></el-icon>
                <template #title>文档列表</template>
              </el-menu-item>
              <el-menu-item index="tags">
                <el-icon><CollectionTag /></el-icon>
                <template #title>标签管理</template>
              </el-menu-item>
            </el-sub-menu>

            <el-menu-item index="chat">
              <el-icon><ChatDotRound /></el-icon>
              <template #title>智能问答</template>
            </el-menu-item>

            <el-menu-item index="search">
              <el-icon><Search /></el-icon>
              <template #title>文档搜索</template>
            </el-menu-item>

            <el-sub-menu index="system" v-if="isAdmin">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>系统管理</span>
              </template>
              <el-menu-item index="users">
                <el-icon><User /></el-icon>
                <template #title>用户管理</template>
              </el-menu-item>
              <el-menu-item index="logs">
                <el-icon><DocumentChecked /></el-icon>
                <template #title>操作日志</template>
              </el-menu-item>
              <el-menu-item index="settings">
                <el-icon><Tools /></el-icon>
                <template #title>系统设置</template>
              </el-menu-item>
            </el-sub-menu>
          </el-menu>

          <!-- 侧边栏底部 -->
          <div class="p-4 border-t border-gray-200">
            <div class="flex items-center justify-center">
              <el-icon class="text-gray-400"><InfoFilled /></el-icon>
              <span v-if="!isCollapse" class="ml-2 text-xs text-gray-500">版本 1.0.0</span>
            </div>
          </div>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="bg-gray-50">
        <div class="h-full">
          <!-- 面包屑导航 -->
          <div class="mb-4">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">
                <el-icon><House /></el-icon>
                首页
              </el-breadcrumb-item>
              <el-breadcrumb-item 
                v-for="item in breadcrumbs" 
                :key="item.path"
                :to="{ path: item.path }"
              >
                {{ item.title }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <!-- 页面内容 -->
          <div class="bg-white rounded-lg shadow-sm min-h-[calc(100vh-200px)]">
            <router-view />
          </div>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  House,
  Document,
  Upload,
  DocumentCopy,
  CollectionTag,
  ChatDotRound,
  Search,
  Setting,
  Tools,
  User,
  DocumentChecked,
  Operation,
  InfoFilled,
  Bell,
  CaretBottom,
  Fold,
  Expand
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 搜索查询
const searchQuery = ref('')

// 侧边栏状态
const isCollapse = ref(false)

// 管理员权限
const isAdmin = ref(true)

// 当前激活菜单
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

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  return matched.map(item => ({
    title: item.meta.title,
    path: item.path
  }))
})

// 切换侧边栏
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}

// 菜单选择
const handleMenuSelect = (index: string) => {
  const routes: Record<string, string> = {
    'dashboard': '/system/dashboard',
    'upload': '/system/upload',
    'documents': '/system/documents',
    'tags': '/system/tags',
    'chat': '/system/chat',
    'search': '/system/search',
    'users': '/system/users',
    'logs': '/system/logs',
    'settings': '/system/settings'
  }
  
  const path = routes[index]
  if (path) {
    router.push(path)
  }
}

// 监听路由变化，更新搜索查询
watch(() => route.query.q, (newQuery) => {
  if (newQuery) {
    searchQuery.value = newQuery as string
  }
}, { immediate: true })
</script>

<style scoped>
/* 自定义样式 */
.el-header {
  padding: 0;
}

.el-aside {
  transition: width 0.3s ease;
}

/* 响应式处理 */
@media (max-width: 768px) {
  .el-aside {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .el-aside.mobile-open {
    transform: translateX(0);
  }
  
  .mobile-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
  }
}
</style>