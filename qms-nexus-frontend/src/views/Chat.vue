<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">智能问答</h1>
      <p class="text-gray-600">基于医疗文档知识库的智能问答系统</p>
    </div>

    <!-- 错误边界包装 -->
    <ErrorBoundary 
      error-title="问答系统出现异常"
      error-message="很抱歉，智能问答系统遇到了问题。请尝试重新加载或返回首页。"
      @error="handleChatError"
      @reset="resetChat"
    >
      <!-- 问答界面 -->
      <div class="flex h-[calc(100vh-200px)] bg-white rounded-lg shadow-sm">
      <!-- 对话历史侧边栏 -->
      <div class="w-80 border-r border-gray-200 flex flex-col">
        <!-- 新建对话按钮 -->
        <div class="p-4 border-b border-gray-200">
          <el-button 
            type="primary" 
            class="w-full"
            @click="startNewChat"
          >
            <el-icon class="mr-2"><Plus /></el-icon>
            新建对话
          </el-button>
        </div>

        <!-- 历史对话列表 -->
        <div class="flex-1 overflow-y-auto">
          <div 
            v-for="chat in chatHistory" 
            :key="chat.id"
            class="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100"
            :class="{ 'bg-blue-50': currentChatId === chat.id }"
            @click="loadChat(chat.id)"
          >
            <div class="flex items-center justify-between mb-1">
              <div class="flex items-center space-x-2">
                <el-icon size="16" class="text-gray-500">
                  <ChatDotRound />
                </el-icon>
                <span class="text-sm font-medium text-gray-800 truncate">
                  {{ chat.title }}
                </span>
              </div>
              <el-dropdown>
                <el-button type="primary" link size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="renameChat(chat)">
                      <el-icon><Edit /></el-icon>
                      重命名
                    </el-dropdown-item>
                    <el-dropdown-item @click="deleteChat(chat)">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            <p class="text-xs text-gray-500 ml-6 truncate">
              {{ chat.lastMessage }}
            </p>
            <p class="text-xs text-gray-400 ml-6">
              {{ chat.lastTime }}
            </p>
          </div>
        </div>
      </div>

      <!-- 主对话区域 -->
      <div class="flex-1 flex flex-col">
        <!-- 对话头部 -->
        <div class="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 class="text-lg font-medium text-gray-800">
            {{ currentChatTitle || '新对话' }}
          </h2>
          <div class="flex items-center space-x-2">
            <el-button
              v-if="messages.length > 0"
              type="primary"
              link
              @click="clearCurrentChat"
            >
              <el-icon class="mr-1"><Delete /></el-icon>
              清空
            </el-button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div ref="messageContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
          <!-- 欢迎消息 -->
          <div v-if="messages.length === 0" class="text-center py-12">
            <el-icon size="48" class="text-gray-300 mb-4">
              <ChatDotRound />
            </el-icon>
            <h3 class="text-lg font-medium text-gray-600 mb-2">欢迎使用智能问答</h3>
            <p class="text-gray-500 mb-6">我可以帮您解答医疗质量管理相关的问题</p>
            <div class="space-y-2">
              <el-button
                v-for="suggestion in quickSuggestions"
                :key="suggestion"
                type="info"
                plain
                @click="sendMessage(suggestion)"
              >
                {{ suggestion }}
              </el-button>
            </div>
          </div>

          <!-- 消息列表 -->
          <div v-else>
            <div 
              v-for="message in messages" 
              :key="message.id"
              class="flex"
              :class="{ 'justify-end': message.role === 'user' }"
            >
              <!-- 用户消息 -->
              <div v-if="message.role === 'user'" class="max-w-[70%]">
                <div class="bg-primary-500 text-white rounded-lg px-4 py-2">
                  <p class="text-sm">{{ message.content }}</p>
                </div>
                <p class="text-xs text-gray-400 mt-1 text-right">
                  {{ message.timestamp }}
                </p>
              </div>

              <!-- AI消息 -->
              <div v-else class="max-w-[70%]">
                <div class="flex items-start space-x-2">
                  <el-avatar size="small" class="bg-green-100">
                    <el-icon class="text-green-600"><MagicStick /></el-icon>
                  </el-avatar>
                  <div class="bg-gray-100 rounded-lg px-4 py-2">
                    <div 
                      v-if="message.status === 'thinking'"
                      class="flex items-center space-x-2 text-gray-600"
                    >
                      <el-icon class="animate-spin"><Loading /></el-icon>
                      <span class="text-sm">思考中...</span>
                    </div>
                    
                    <div 
                      v-else-if="message.status === 'streaming'"
                      class="text-sm text-gray-800"
                    >
                      <span>{{ message.content }}</span>
                      <span class="animate-pulse">|</span>
                    </div>
                    
                    <div 
                      v-else
                      class="text-sm text-gray-800"
                      v-html="formatMessage(message.content)"
                    ></div>

                    <!-- 来源标注 -->
                    <div v-if="message.sources && message.sources.length > 0" class="mt-3 pt-3 border-t border-gray-200">
                      <p class="text-xs text-gray-600 mb-2">参考来源：</p>
                      <div class="space-y-1">
                        <div 
                          v-for="source in message.sources" 
                          :key="source.id"
                          class="text-xs text-blue-600 hover:text-blue-800 cursor-pointer"
                          @click="viewSource(source)"
                        >
                          [{{ source.fileName }}, 第{{ source.page }}页]
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <p class="text-xs text-gray-400 mt-1 ml-8">
                  {{ message.timestamp }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="p-4 border-t border-gray-200">
          <div class="flex space-x-3">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="2"
              placeholder="请输入您的问题..."
              class="flex-1"
              :disabled="isThinking"
              @keyup.enter.prevent="sendMessage"
            />
            <div class="flex flex-col space-y-2">
              <el-button
                type="primary"
                :loading="isThinking"
                :disabled="!inputMessage.trim() || isThinking"
                @click="() => sendMessage()"
                class="h-full"
              >
                <el-icon><Position /></el-icon>
              </el-button>
            </div>
          </div>
          
          <!-- 输入提示 -->
          <div class="mt-2 text-xs text-gray-500 flex items-center justify-between">
            <div>
              按 Enter 发送，Shift+Enter 换行
            </div>
            <div class="flex items-center space-x-2">
              <el-checkbox v-model="enableStreaming" size="small">
                流式响应
              </el-checkbox>
              <el-checkbox v-model="enableSources" size="small">
                显示来源
              </el-checkbox>
            </div>
          </div>
        </div>
      </div>
    </div>
  </ErrorBoundary>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, watch, ComponentPublicInstance } from 'vue'
import { ElMessage } from 'element-plus'
import { chatService } from '@/services/chat'
import ErrorBoundary from '@/components/ErrorBoundary.vue'
import {
  Plus,
  ChatDotRound,
  MoreFilled,
  Edit,
  Delete,
  MagicStick,
  Loading,
  Position
} from '@element-plus/icons-vue'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  status?: 'thinking' | 'streaming' | 'completed'
  sources?: Source[]
}

interface ChatHistoryItem {
  id: string
  title: string
  lastMessage: string
  lastTime: string
  messageCount: number
}

interface Source {
  id: string
  fileName: string
  page: number
  content: string
}

// 状态管理
const inputMessage = ref('')
const isThinking = ref(false)
const enableStreaming = ref(true)
const enableSources = ref(true)
const messageContainer = ref<HTMLElement>()

// 当前对话
const currentChatId = ref<string>('')
const currentChatTitle = ref<string>('')

// 对话历史
const chatHistory = reactive<ChatHistoryItem[]>([
  {
    id: '1',
    title: '质量管理体系建立',
    lastMessage: '如何建立有效的质量管理体系？',
    lastTime: '2小时前',
    messageCount: 12
  },
  {
    id: '2',
    title: '医疗质量指标',
    lastMessage: '医疗质量指标有哪些？',
    lastTime: '昨天',
    messageCount: 8
  },
  {
    id: '3',
    title: '持续改进方法',
    lastMessage: 'PDCA循环的具体步骤是什么？',
    lastTime: '3天前',
    messageCount: 15
  }
])

// 消息列表
const messages = reactive<Message[]>([])

// 快速建议
const quickSuggestions = [
  '如何建立医疗质量管理体系？',
  '医疗质量指标有哪些？',
  '如何进行质量持续改进？',
  '医疗质量管理的关键要素是什么？'
]

// 发送消息
const sendMessage = async (message?: string) => {
  const content = message || inputMessage.value.trim()
  if (!content || isThinking.value) return

  // 清空输入框
  inputMessage.value = ''
  isThinking.value = true

  // 创建用户消息
  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content,
    timestamp: new Date().toLocaleTimeString('zh-CN')
  }
  messages.push(userMessage)

  // 更新对话标题（如果是新对话）
  if (!currentChatTitle.value && messages.length === 1) {
    currentChatTitle.value = content.slice(0, 20) + (content.length > 20 ? '...' : '')
  }

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  try {
    // 创建AI思考消息
    const thinkingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString('zh-CN'),
      status: 'thinking'
    }
    messages.push(thinkingMessage)

    // 滚动到底部显示思考状态
    await nextTick()
    scrollToBottom()

    // 根据是否启用流式响应选择不同的调用方式
    if (enableStreaming.value) {
      // 流式响应
      thinkingMessage.status = 'streaming'
      thinkingMessage.content = '正在为您查询相关知识...'

      let fullResponse = ''
      const response = await chatService.askQuestionStream(
        content,
        undefined, // context
        undefined, // filterTags
        5, // topK
        (chunk: string) => {
          fullResponse += chunk
          thinkingMessage.content = fullResponse
          scrollToBottom()
        }
      )

      // 更新最终状态
      thinkingMessage.status = 'completed'
      thinkingMessage.content = response.answer
      
      // 添加来源（如果启用且有来源）
      if (enableSources.value && response.sources && response.sources.length > 0) {
        thinkingMessage.sources = response.sources.map((source, index) => ({
          id: (index + 1).toString(),
          fileName: source.documentName,
          page: source.page || 1,
          content: source.table || '相关章节内容'
        }))
      }
    } else {
      // 普通响应
      thinkingMessage.content = '正在为您查询相关知识...'
      
      const response = await chatService.askQuestion(content)
      
      thinkingMessage.status = 'completed'
      thinkingMessage.content = response.answer
      
      // 添加来源（如果启用且有来源）
      if (enableSources.value && response.sources && response.sources.length > 0) {
        thinkingMessage.sources = response.sources.map((source, index) => ({
          id: (index + 1).toString(),
          fileName: source.documentName,
          page: source.page || 1,
          content: source.table || '相关章节内容'
        }))
      }
    }

    isThinking.value = false
    scrollToBottom()
    
    // 更新对话历史
    updateChatHistory()
    
  } catch (error) {
    console.error('问答请求失败:', error)
    
    // 更新错误消息
    const errorMessage = messages[messages.length - 1]
    if (errorMessage && errorMessage.role === 'assistant') {
      errorMessage.status = 'completed'
      errorMessage.content = '抱歉，我无法回答您的问题。请稍后重试或联系技术支持。'
    }
    
    isThinking.value = false
    scrollToBottom()
  }
}



// 格式化消息
const formatMessage = (content: string): string => {
  return content.replace(/\n/g, '<br>')
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight
    }
  })
}

// 开始新对话
const startNewChat = () => {
  currentChatId.value = ''
  currentChatTitle.value = ''
  messages.length = 0
}

// 加载对话
const loadChat = (chatId: string) => {
  currentChatId.value = chatId
  const chat = chatHistory.find(c => c.id === chatId)
  if (chat) {
    currentChatTitle.value = chat.title
    // 这里应该加载具体的对话消息
    messages.length = 0
  }
}

// 清空当前对话
const clearCurrentChat = () => {
  messages.length = 0
}

// 重命名对话
const renameChat = (_chat: ChatHistoryItem) => {
  // 实现重命名逻辑
  ElMessage.info('重命名功能开发中')
}

// 删除对话
const deleteChat = (_chat: ChatHistoryItem) => {
  // 实现删除逻辑
  ElMessage.info('删除功能开发中')
}

// 查看来源
const viewSource = (source: Source) => {
  ElMessage.info(`查看来源: ${source.fileName} 第${source.page}页`)
}

// 更新对话历史
const updateChatHistory = () => {
  if (currentChatId.value) {
    const chat = chatHistory.find(c => c.id === currentChatId.value)
    if (chat) {
      chat.lastMessage = messages[messages.length - 2]?.content.slice(0, 50) + '...' || ''
      chat.lastTime = '刚刚'
      chat.messageCount = messages.length
    }
  } else if (messages.length > 0) {
    // 创建新的对话历史记录
    const newChat: ChatHistoryItem = {
      id: Date.now().toString(),
      title: currentChatTitle.value,
      lastMessage: messages[messages.length - 2]?.content.slice(0, 50) + '...' || '',
      lastTime: '刚刚',
      messageCount: messages.length
    }
    chatHistory.unshift(newChat)
    currentChatId.value = newChat.id
  }
}

// 监听消息变化
watch(messages, () => {
  scrollToBottom()
})

/**
 * 处理聊天错误
 */
const handleChatError = (error: Error, instance: ComponentPublicInstance | null, info: string) => {
  console.error('Chat组件错误:', error, info)
  
  // 记录错误日志
  chatService.logError({
    error: error.message,
    stack: error.stack,
    component: 'Chat',
    info
  }).catch(console.error)
}

/**
 * 重置聊天状态
 */
const resetChat = () => {
  console.log('重置聊天状态')
  currentChatId.value = ''
  currentChatTitle.value = ''
  messages.length = 0
  isThinking.value = false
  inputMessage.value = ''
}
</script>

<style scoped>
/* 自定义样式 */
</style>