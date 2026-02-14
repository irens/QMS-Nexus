<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">智能问答</h1>
      <p class="text-gray-600">基于医疗文档知识库的智能问答系统</p>
    </div>

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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
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

  // 模拟AI响应
  setTimeout(() => {
    // 创建AI思考消息
    const thinkingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString('zh-CN'),
      status: 'thinking'
    }
    messages.push(thinkingMessage)

    // 模拟思考过程
    setTimeout(() => {
      thinkingMessage.status = 'streaming'
      thinkingMessage.content = '正在为您查询相关知识...'

      // 模拟流式响应
      let response = getMockResponse(content)
      let currentIndex = 0
      const streamingInterval = setInterval(() => {
        if (currentIndex < response.length) {
          thinkingMessage.content = response.slice(0, currentIndex + 1)
          currentIndex += Math.floor(Math.random() * 5) + 1
          scrollToBottom()
        } else {
          clearInterval(streamingInterval)
          thinkingMessage.status = 'completed'
          thinkingMessage.content = response
          
          // 添加来源（如果启用）
          if (enableSources.value) {
            thinkingMessage.sources = [
              {
                id: '1',
                fileName: '医疗质量管理规范.pdf',
                page: 12,
                content: '相关章节内容'
              },
              {
                id: '2',
                fileName: '2024年度质量报告.docx',
                page: 8,
                content: '相关章节内容'
              }
            ]
          }

          isThinking.value = false
          scrollToBottom()
          
          // 更新对话历史
          updateChatHistory()
        }
      }, 50)
    }, 1000)
  }, 500)
}

// 获取模拟响应
const getMockResponse = (question: string): string => {
  const responses: Record<string, string> = {
    '如何建立医疗质量管理体系？': '建立医疗质量管理体系需要遵循以下步骤：\n\n1. **制定质量方针和目标**\n   - 明确质量管理的总体方向\n   - 设定可测量的质量目标\n   - 确保目标与组织战略一致\n\n2. **建立组织架构**\n   - 设立质量管理委员会\n   - 指定质量管理人员\n   - 明确各部门职责分工\n\n3. **制定标准操作程序**\n   - 建立标准化工作流程\n   - 制定质量控制标准\n   - 建立监测评估机制\n\n4. **实施PDCA循环**\n   - Plan(计划)：制定改进计划\n   - Do(执行)：实施改进措施\n   - Check(检查)：检查执行效果\n   - Act(处理)：标准化成功经验\n\n5. **持续监控和改进**\n   - 定期收集质量数据\n   - 分析质量问题\n   - 实施改进措施\n   - 评估改进效果',
    
    '医疗质量指标有哪些？': '医疗质量指标主要包括以下几个方面：\n\n1. **结构指标**\n   - 医疗设备和设施配置\n   - 医护人员资质和配比\n   - 医疗技术标准\n   - 管理制度完善程度\n\n2. **过程指标**\n   - 诊疗规范执行率\n   - 平均住院日\n   - 术前等待时间\n   - 会诊及时率\n   - 病历书写合格率\n\n3. **结果指标**\n   - 死亡率\n   - 并发症发生率\n   - 感染率\n   - 再入院率\n   - 患者满意度\n   - 治愈率\n\n4. **效率指标**\n   - 床位周转率\n   - 手术台利用率\n   - 检查预约等待时间\n   - 急诊等待时间\n\n5. **安全指标**\n   - 医疗事故发生率\n   - 用药错误率\n   - 跌倒发生率\n   - 压疮发生率'
  }
  
  return responses[question] || '我理解您的问题，基于医疗质量管理知识库，我可以为您提供相关信息。请允许我查询相关知识库内容...'
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
</script>

<style scoped>
/* 自定义样式 */
</style>