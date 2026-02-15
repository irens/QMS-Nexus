// 状态管理统一导出
export { useDocumentStore } from './document'
export { useUserStore } from './user'
export { useChatStore } from './chat'
export { useSystemStore } from './system'
export { useUploadStore } from './upload'
export { useTagStore } from './tag'

// 创建状态管理插件
// import type { App } from 'vue'

// export function createPiniaPlugins(app: App) {
//   // 可以在这里添加全局的Pinia插件
//   // 例如：持久化插件、日志插件等
// }