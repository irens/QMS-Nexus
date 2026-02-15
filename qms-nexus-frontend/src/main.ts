import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import App from './App.vue'
import router from './router'
import './assets/main.css'

// 导入状态管理
import { useUserStore, useSystemStore } from '@/stores'

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 创建Pinia实例
const pinia = createPinia()

// 注册全局错误处理
pinia.use(({ store }) => {
  store.$onAction(({ name, store, args, after, onError }) => {
    after(() => {
      // 动作成功完成后的处理
      if (store.$id === 'system' && name === 'addNotification') {
        const notification = args[0]
        if (notification) {
          ElMessage({
            message: notification.message,
            type: notification.type,
            duration: 3000
          })
        }
      }
    })
    
    onError((error) => {
      // 动作失败后的处理
      console.error(`[${store.$id}] Action "${name}" failed:`, error)
      
      if (store.$id === 'system') {
        // 系统级别的错误，显示通知
        const systemStore = useSystemStore()
        systemStore.addNotification({
          type: 'error',
          title: '操作失败',
          message: (error as Error).message || '未知错误',
          read: false
        })
      }
    })
  })
})

app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 初始化应用
async function initializeApp() {
  try {
    // 初始化用户状态
    const userStore = useUserStore()
    await userStore.fetchCurrentUser()
    
    // 初始化系统状态
    const systemStore = useSystemStore()
    await systemStore.getSystemStatus()
    await systemStore.getSystemConfig()
    
    // 启动定期状态检查
    setInterval(() => {
      systemStore.getSystemStatus()
    }, 30000) // 30秒检查一次
    
  } catch (error) {
    console.error('Failed to initialize app:', error)
  }
}

// 挂载应用
app.mount('#app')

// 初始化应用
initializeApp()