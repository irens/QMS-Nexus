<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">仪表盘</h1>
      <p class="text-gray-600">欢迎使用QMS-Nexus医疗质量管理系统</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <el-card class="hover:shadow-lg transition-shadow duration-300">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 mb-1">总文档数</p>
            <p class="text-2xl font-bold text-gray-800">1,234</p>
            <p class="text-xs text-green-600 mt-1">↑ 12% 较上月</p>
          </div>
          <div class="p-3 bg-blue-100 rounded-full">
            <el-icon size="24" class="text-blue-600">
              <Document />
            </el-icon>
          </div>
        </div>
      </el-card>

      <el-card class="hover:shadow-lg transition-shadow duration-300">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 mb-1">已解析文档</p>
            <p class="text-2xl font-bold text-gray-800">987</p>
            <p class="text-xs text-green-600 mt-1">↑ 8% 较上月</p>
          </div>
          <div class="p-3 bg-green-100 rounded-full">
            <el-icon size="24" class="text-green-600">
              <CircleCheck />
            </el-icon>
          </div>
        </div>
      </el-card>

      <el-card class="hover:shadow-lg transition-shadow duration-300">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 mb-1">问答次数</p>
            <p class="text-2xl font-bold text-gray-800">5,678</p>
            <p class="text-xs text-green-600 mt-1">↑ 15% 较上月</p>
          </div>
          <div class="p-3 bg-purple-100 rounded-full">
            <el-icon size="24" class="text-purple-600">
              <ChatDotRound />
            </el-icon>
          </div>
        </div>
      </el-card>

      <el-card class="hover:shadow-lg transition-shadow duration-300">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-600 mb-1">活跃用户</p>
            <p class="text-2xl font-bold text-gray-800">156</p>
            <p class="text-xs text-green-600 mt-1">↑ 5% 较上月</p>
          </div>
          <div class="p-3 bg-orange-100 rounded-full">
            <el-icon size="24" class="text-orange-600">
              <User />
            </el-icon>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 最近活动和文档 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 最近上传的文档 -->
      <el-card>
        <template #header>
          <div class="flex items-center justify-between">
            <span class="text-lg font-medium">最近上传的文档</span>
            <el-button type="primary" link>查看全部</el-button>
          </div>
        </template>
        
        <div class="space-y-4">
          <div 
            v-for="doc in recentDocuments" 
            :key="doc.id"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <div class="flex items-center space-x-3">
              <el-icon size="20" :class="getFileIconColor(doc.type)">
                <component :is="getFileIcon(doc.type)" />
              </el-icon>
              <div>
                <p class="text-sm font-medium text-gray-800">{{ doc.name }}</p>
                <p class="text-xs text-gray-500">{{ doc.size }} • {{ doc.uploadTime }}</p>
              </div>
            </div>
            <el-tag 
              :type="getStatusType(doc.status) as any" 
              size="small"
              class="capitalize"
            >
              {{ getStatusText(doc.status) }}
            </el-tag>
          </div>
        </div>
      </el-card>

      <!-- 最近问答记录 -->
      <el-card>
        <template #header>
          <div class="flex items-center justify-between">
            <span class="text-lg font-medium">最近问答记录</span>
            <el-button type="primary" link>查看全部</el-button>
          </div>
        </template>
        
        <div class="space-y-4">
          <div 
            v-for="chat in recentChats" 
            :key="chat.id"
            class="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
          >
            <div class="flex items-start space-x-3">
              <el-avatar size="small" :icon="User" />
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-800 mb-1">{{ chat.question }}</p>
                <p class="text-xs text-gray-600 line-clamp-2">{{ chat.answer }}</p>
                <p class="text-xs text-gray-400 mt-2">{{ chat.time }}</p>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 快速操作 -->
    <div class="mt-8">
      <h3 class="text-lg font-medium text-gray-800 mb-4">快速操作</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <el-button 
          type="primary" 
          class="h-24 flex flex-col items-center justify-center space-y-2"
          @click="$router.push('/system/upload')"
        >
          <el-icon size="24"><Upload /></el-icon>
          <span>上传文档</span>
        </el-button>
        
        <el-button 
          class="h-24 flex flex-col items-center justify-center space-y-2"
          @click="$router.push('/system/chat')"
        >
          <el-icon size="24"><ChatDotRound /></el-icon>
          <span>智能问答</span>
        </el-button>
        
        <el-button 
          class="h-24 flex flex-col items-center justify-center space-y-2"
          @click="$router.push('/system/search')"
        >
          <el-icon size="24"><Search /></el-icon>
          <span>文档搜索</span>
        </el-button>
        
        <el-button 
          class="h-24 flex flex-col items-center justify-center space-y-2"
          @click="$router.push('/system/tags')"
        >
          <el-icon size="24"><CollectionTag /></el-icon>
          <span>标签管理</span>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  Document,
  CircleCheck,
  ChatDotRound,
  User,
  Upload,
  Search,
  CollectionTag,
  DocumentCopy,
  Tickets,
  Notebook
} from '@element-plus/icons-vue'

interface DocumentItem {
  id: string
  name: string
  type: string
  size: string
  uploadTime: string
  status: 'processing' | 'completed' | 'failed'
}

interface ChatItem {
  id: string
  question: string
  answer: string
  time: string
}

// 模拟数据
const recentDocuments = ref<DocumentItem[]>([
  {
    id: '1',
    name: '医疗质量管理规范.pdf',
    type: 'pdf',
    size: '2.3 MB',
    uploadTime: '2小时前',
    status: 'completed'
  },
  {
    id: '2',
    name: '2024年度质量报告.docx',
    type: 'docx',
    size: '1.8 MB',
    uploadTime: '5小时前',
    status: 'processing'
  },
  {
    id: '3',
    name: '质量指标统计表.xlsx',
    type: 'xlsx',
    size: '856 KB',
    uploadTime: '1天前',
    status: 'completed'
  },
  {
    id: '4',
    name: '培训计划.pptx',
    type: 'pptx',
    size: '3.2 MB',
    uploadTime: '2天前',
    status: 'completed'
  }
])

const recentChats = ref<ChatItem[]>([
  {
    id: '1',
    question: '如何建立医疗质量管理体系？',
    answer: '医疗质量管理体系的建立需要遵循以下步骤：1. 制定质量方针和目标 2. 建立组织架构...',
    time: '10分钟前'
  },
  {
    id: '2',
    question: '医疗质量指标有哪些？',
    answer: '主要医疗质量指标包括：死亡率、并发症发生率、患者满意度、平均住院日...',
    time: '1小时前'
  },
  {
    id: '3',
    question: '如何进行质量持续改进？',
    answer: '质量持续改进的PDCA循环：Plan(计划)、Do(执行)、Check(检查)、Act(处理)...',
    time: '3小时前'
  }
])

// 获取文件图标
const getFileIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    pdf: Document,
    doc: DocumentCopy,
    docx: DocumentCopy,
    xls: Tickets,
    xlsx: Tickets,
    ppt: Notebook,
    pptx: Notebook
  }
  return iconMap[type] || Document
}

// 获取文件图标颜色
const getFileIconColor = (type: string) => {
  const colorMap: Record<string, string> = {
    pdf: 'text-red-600',
    doc: 'text-blue-600',
    docx: 'text-blue-600',
    xls: 'text-green-600',
    xlsx: 'text-green-600',
    ppt: 'text-orange-600',
    pptx: 'text-orange-600'
  }
  return colorMap[type] || 'text-gray-600'
}

// 获取状态类型
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    processing: '解析中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || '未知'
}
</script>

<style scoped>
/* 自定义样式 */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>