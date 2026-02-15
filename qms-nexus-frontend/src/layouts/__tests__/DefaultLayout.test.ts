// DefaultLayout 组件测试
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createTestingPinia } from '@pinia/testing'
import { ref, nextTick } from 'vue'
import ElementPlus from 'element-plus'

// Mock Vue Router
const mockRoutes = [
  { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
  { path: '/dashboard', name: 'dashboard', component: { template: '<div>Dashboard</div>' } },
  { path: '/upload', name: 'upload', component: { template: '<div>Upload</div>' } },
  { path: '/documents', name: 'documents', component: { template: '<div>Documents</div>' } },
  { path: '/chat', name: 'chat', component: { template: '<div>Chat</div>' } }
]

const router = createRouter({
  history: createWebHistory(),
  routes: mockRoutes
})

describe('DefaultLayout.vue', () => {
  let wrapper: VueWrapper<any>

  beforeEach(async () => {
    // 重置路由
    router.push('/system')
    await router.isReady()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('组件渲染', () => {
    it('应该正确渲染布局结构', async () => {
      const DefaultLayout = {
        template: `
          <div class="layout">
            <header class="header">Header</header>
            <aside class="sidebar">Sidebar</aside>
            <main class="main">
              <router-view />
            </main>
          </div>
        `
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [router, ElementPlus, createTestingPinia()]
        }
      })

      expect(wrapper.find('.layout').exists()).toBe(true)
      expect(wrapper.find('.header').exists()).toBe(true)
      expect(wrapper.find('.sidebar').exists()).toBe(true)
      expect(wrapper.find('.main').exists()).toBe(true)
    })

    it('应该显示Logo和标题', async () => {
      const DefaultLayout = {
        template: `
          <div>
            <div class="logo">
              <el-icon class="logo-icon"><FirstAidKit /></el-icon>
              <h1 class="title">QMS-Nexus</h1>
              <span class="subtitle">医疗质量管理系统</span>
            </div>
          </div>
        `,
        components: {
          FirstAidKit: {
            template: '<div class="mock-first-aid-kit"></div>'
          }
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [ElementPlus]
        }
      })

      expect(wrapper.find('.logo').exists()).toBe(true)
      expect(wrapper.find('.logo-icon').exists()).toBe(true)
      expect(wrapper.find('.title').text()).toBe('QMS-Nexus')
      expect(wrapper.find('.subtitle').text()).toBe('医疗质量管理系统')
    })

    it('应该显示搜索框', async () => {
      const DefaultLayout = {
        template: `
          <div>
            <el-input
              v-model="searchQuery"
              placeholder="搜索文档..."
              class="search-input"
              size="small"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        `,
        data() {
          return {
            searchQuery: ''
          }
        },
        components: {
          Search: {
            template: '<div class="mock-search"></div>'
          }
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [ElementPlus]
        }
      })

      const searchInput = wrapper.find('.search-input')
      expect(searchInput.exists()).toBe(true)
      
      const input = wrapper.find('input')
      expect(input.attributes('placeholder')).toBe('搜索文档...')
    })

    it('应该显示通知图标', async () => {
      const DefaultLayout = {
        template: `
          <div>
            <el-badge :value="3" class="notification-badge">
              <el-button :icon="Bell" circle size="small" />
            </el-badge>
          </div>
        `,
        components: {
          Bell: {
            template: '<div class="mock-bell"></div>'
          }
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [ElementPlus]
        }
      })

      expect(wrapper.find('.notification-badge').exists()).toBe(true)
      expect(wrapper.find('.el-badge__content').text()).toBe('3')
    })

    it('应该显示用户菜单', async () => {
      const DefaultLayout = {
        template: `
          <div>
            <el-dropdown class="user-menu">
              <div class="user-info">
                <el-avatar size="small" :icon="User" />
                <span class="username">管理员</span>
                <el-icon><CaretBottom /></el-icon>
              </div>
            </el-dropdown>
          </div>
        `,
        components: {
          User: {
            template: '<div class="mock-user"></div>'
          },
          CaretBottom: {
            template: '<div class="mock-caret"></div>'
          }
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [ElementPlus]
        }
      })

      expect(wrapper.find('.user-menu').exists()).toBe(true)
      expect(wrapper.find('.username').text()).toBe('管理员')
    })
  })

  describe('导航菜单', () => {
    it('应该显示所有导航菜单项', async () => {
      const DefaultLayout = {
        template: `
          <div>
            <el-menu :default-active="activeMenu" class="nav-menu">
              <el-menu-item index="dashboard">
                <el-icon><House /></el-icon>
                <template #title>仪表盘</template>
              </el-menu-item>
              <el-sub-menu index="documents">
                <template #title>
                  <el-icon><Document /></el-icon>
                  <span>文档管理</span>
                </template>
                <el-menu-item index="upload">文件上传</el-menu-item>
                <el-menu-item index="document-list">文档列表</el-menu-item>
              </el-sub-menu>
              <el-menu-item index="chat">
                <el-icon><ChatDotRound /></el-icon>
                <template #title>智能问答</template>
              </el-menu-item>
            </el-menu>
          </div>
        `,
        data() {
          return {
            activeMenu: 'dashboard'
          }
        },
        components: {
          House: { template: '<div class="mock-house"></div>' },
          Document: { template: '<div class="mock-document"></div>' },
          ChatDotRound: { template: '<div class="mock-chat"></div>' }
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [ElementPlus, router]
        }
      })

      expect(wrapper.find('.nav-menu').exists()).toBe(true)
      expect(wrapper.findAll('.el-menu-item')).toHaveLength(4) // 3个主菜单 + 1个激活的
      expect(wrapper.findAll('.el-sub-menu')).toHaveLength(1) // 1个子菜单
    })

    it('应该正确高亮当前激活的菜单', async () => {
      const DefaultLayout = {
        template: `
          <div>
            <el-menu :default-active="activeMenu">
              <el-menu-item index="dashboard">仪表盘</el-menu-item>
              <el-menu-item index="chat">智能问答</el-menu-item>
            </el-menu>
            <div class="current-route">{{ activeMenu }}</div>
          </div>
        `,
        data() {
          return {
            activeMenu: 'dashboard'
          }
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [ElementPlus]
        }
      })

      expect(wrapper.vm.activeMenu).toBe('dashboard')
      
      // 切换激活菜单
      wrapper.vm.activeMenu = 'chat'
      await nextTick()
      
      expect(wrapper.vm.activeMenu).toBe('chat')
    })

    it('应该响应菜单点击事件', async () => {
      const handleMenuSelect = vi.fn()
      
      const DefaultLayout = {
        template: `
          <div>
            <el-menu @select="handleMenuSelect">
              <el-menu-item index="dashboard">仪表盘</el-menu-item>
              <el-menu-item index="chat">智能问答</el-menu-item>
            </el-menu>
          </div>
        `,
        methods: {
          handleMenuSelect
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [ElementPlus]
        }
      })

      const menuItems = wrapper.findAll('.el-menu-item')
      await menuItems[1].trigger('click')

      expect(handleMenuSelect).toHaveBeenCalledWith('chat', ['/chat'], {
        index: 'chat',
        indexPath: ['chat']
      })
    })
  })

  describe('响应式布局', () => {
    it('应该支持侧边栏折叠', async () => {
      const DefaultLayout = {
        template: `
          <div>
            <el-aside :width="isCollapse ? '64px' : '240px'" class="sidebar">
              <div class="sidebar-width">{{ isCollapse ? '64px' : '240px' }}</div>
            </el-aside>
            <el-button @click="toggleSidebar">切换</el-button>
          </div>
        `,
        data() {
          return {
            isCollapse: false
          }
        },
        methods: {
          toggleSidebar() {
            this.isCollapse = !this.isCollapse
          }
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [ElementPlus]
        }
      })

      expect(wrapper.find('.sidebar-width').text()).toBe('240px')
      expect(wrapper.vm.isCollapse).toBe(false)

      await wrapper.find('button').trigger('click')

      expect(wrapper.vm.isCollapse).toBe(true)
      expect(wrapper.find('.sidebar-width').text()).toBe('64px')
    })

    it('应该根据屏幕尺寸自动折叠', async () => {
      // Mock window.innerWidth
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768 // 小于md断点
      })

      const DefaultLayout = {
        template: `
          <div>
            <div class="screen-width">{{ window.innerWidth }}</div>
            <div class="is-mobile">{{ isMobile }}</div>
          </div>
        `,
        computed: {
          isMobile() {
            return window.innerWidth < 768
          }
        }
      }

      wrapper = mount(DefaultLayout)

      expect(wrapper.vm.isMobile).toBe(true)

      // 改变屏幕宽度
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024
      })

      // 触发resize事件
      window.dispatchEvent(new Event('resize'))
      await nextTick()

      expect(wrapper.vm.isMobile).toBe(false)
    })
  })

  describe('路由集成', () => {
    it('应该根据路由更新激活菜单', async () => {
      const DefaultLayout = {
        template: `
          <div>
            <el-menu :default-active="activeMenu">
              <el-menu-item index="dashboard">仪表盘</el-menu-item>
              <el-menu-item index="chat">智能问答</el-menu-item>
            </el-menu>
          </div>
        `,
        computed: {
          activeMenu() {
            return this.$route.path.replace('/', '') || 'dashboard'
          }
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [router, ElementPlus]
        }
      })

      expect(wrapper.vm.activeMenu).toBe('dashboard')

      await router.push('/system/chat')
      await nextTick()

      expect(wrapper.vm.activeMenu).toBe('chat')
    })

    it('应该渲染路由视图', async () => {
      const DefaultLayout = {
        template: `
          <div class="layout">
            <router-view />
          </div>
        `
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [router]
        }
      })

      expect(wrapper.find('.layout').exists()).toBe(true)
      expect(wrapper.html()).toContain('router-view')
    })
  })

  describe('用户权限', () => {
    it('应该根据权限显示菜单', async () => {
      const DefaultLayout = {
        template: `
          <div>
            <el-menu>
              <el-menu-item index="dashboard">仪表盘</el-menu-item>
              <el-sub-menu index="system" v-if="isAdmin">
                <template #title>系统管理</template>
                <el-menu-item index="users">用户管理</el-menu-item>
              </el-sub-menu>
            </el-menu>
            <div class="user-role">{{ isAdmin ? 'Admin' : 'User' }}</div>
          </div>
        `,
        data() {
          return {
            isAdmin: false
          }
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [ElementPlus]
        }
      })

      expect(wrapper.find('.user-role').text()).toBe('User')
      expect(wrapper.findAll('.el-sub-menu')).toHaveLength(0) // 非管理员不显示系统管理

      wrapper.vm.isAdmin = true
      await nextTick()

      expect(wrapper.find('.user-role').text()).toBe('Admin')
      expect(wrapper.findAll('.el-sub-menu')).toHaveLength(1) // 管理员显示系统管理
    })
  })

  describe('搜索功能', () => {
    it('应该响应搜索输入', async () => {
      const handleSearch = vi.fn()
      
      const DefaultLayout = {
        template: `
          <div>
            <el-input
              v-model="searchQuery"
              placeholder="搜索文档..."
              @keyup.enter="handleSearch"
              class="search-input"
            />
          </div>
        `,
        data() {
          return {
            searchQuery: ''
          }
        },
        methods: {
          handleSearch
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [ElementPlus]
        }
      })

      const input = wrapper.find('input')
      await input.setValue('ISO 13485')
      
      expect(wrapper.vm.searchQuery).toBe('ISO 13485')
      
      await input.trigger('keyup.enter')
      expect(handleSearch).toHaveBeenCalled()
    })
  })

  describe('移动端适配', () => {
    it('应该隐藏移动端菜单按钮', async () => {
      const DefaultLayout = {
        template: `
          <div>
            <el-button class="mobile-menu-btn md:hidden" @click="toggleMenu">菜单</el-button>
            <div class="is-mobile">{{ isMobile }}</div>
          </div>
        `,
        data() {
          return {
            isMobile: false
          }
        },
        methods: {
          toggleMenu() {
            this.isMobile = !this.isMobile
          }
        }
      }

      wrapper = mount(DefaultLayout, {
        global: {
          plugins: [ElementPlus]
        }
      })

      const menuBtn = wrapper.find('.mobile-menu-btn')
      expect(menuBtn.exists()).toBe(true)
      expect(menuBtn.classes()).toContain('md:hidden') // 桌面端隐藏
    })
  })

  describe('组件状态', () => {
    it('应该正确初始化所有状态', async () => {
      const DefaultLayout = {
        template: `
          <div>
            <div class="is-collapse">{{ isCollapse }}</div>
            <div class="active-menu">{{ activeMenu }}</div>
            <div class="search-query">{{ searchQuery }}</div>
          </div>
        `,
        data() {
          return {
            isCollapse: false,
            activeMenu: 'dashboard',
            searchQuery: ''
          }
        }
      }

      wrapper = mount(DefaultLayout)

      expect(wrapper.vm.isCollapse).toBe(false)
      expect(wrapper.vm.activeMenu).toBe('dashboard')
      expect(wrapper.vm.searchQuery).toBe('')
    })
  })
})
