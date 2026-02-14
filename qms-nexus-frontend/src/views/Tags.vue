<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">标签管理</h1>
      <p class="text-gray-600">管理文档标签，便于分类和检索</p>
    </div>

    <!-- 添加新标签 -->
    <div class="mb-6">
      <el-card>
        <template #header>
          <div class="flex items-center justify-between">
            <span class="text-lg font-medium">添加新标签</span>
          </div>
        </template>
        
        <div class="flex space-x-4">
          <el-input
            v-model="newTagName"
            placeholder="输入标签名称"
            class="flex-1"
          />
          <el-select v-model="newTagColor" placeholder="选择颜色">
            <el-option
              v-for="color in tagColors"
              :key="color.value"
              :label="color.label"
              :value="color.value"
            >
              <div class="flex items-center space-x-2">
                <div 
                  class="w-4 h-4 rounded-full" 
                  :class="color.class"
                ></div>
                <span>{{ color.label }}</span>
              </div>
            </el-option>
          </el-select>
          <el-button type="primary" @click="addTag" :disabled="!newTagName">
            <el-icon class="mr-1"><Plus /></el-icon>
            添加标签
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 标签列表 -->
    <div class="mb-6">
      <el-card>
        <template #header>
          <div class="flex items-center justify-between">
            <span class="text-lg font-medium">标签列表</span>
            <div class="text-sm text-gray-500">
              共 {{ tags.length }} 个标签
            </div>
          </div>
        </template>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div 
            v-for="tag in tags" 
            :key="tag.id"
            class="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
          >
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center space-x-2">
                <div 
                  class="w-3 h-3 rounded-full" 
                  :class="getTagColorClass(tag.color)"
                ></div>
                <span class="font-medium text-gray-800">{{ tag.name }}</span>
              </div>
              <el-dropdown>
                <el-button type="primary" link size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="editTag(tag)">
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item @click="viewTaggedDocuments(tag)">
                      <el-icon><Document /></el-icon>
                      查看文档
                    </el-dropdown-item>
                    <el-dropdown-item divided @click="deleteTag(tag)">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            
            <div class="text-sm text-gray-600 mb-2">
              <p>文档数量: {{ tag.documentCount }}</p>
              <p>创建时间: {{ tag.createdAt }}</p>
            </div>
            
            <div class="text-xs text-gray-500">
              <p>描述: {{ tag.description || '暂无描述' }}</p>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 标签统计 -->
    <div>
      <el-card>
        <template #header>
          <span class="text-lg font-medium">标签统计</span>
        </template>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="text-center">
            <div class="text-2xl font-bold text-blue-600">{{ tags.length }}</div>
            <div class="text-sm text-gray-600">总标签数</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-green-600">{{ totalDocuments }}</div>
            <div class="text-sm text-gray-600">关联文档</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-orange-600">{{ averageDocumentsPerTag }}</div>
            <div class="text-sm text-gray-600">平均文档数</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 编辑标签对话框 -->
    <el-dialog
      v-model="editDialog.visible"
      title="编辑标签"
      width="500px"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">标签名称</label>
          <el-input
            v-model="editDialog.form.name"
            placeholder="输入标签名称"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">标签颜色</label>
          <el-select v-model="editDialog.form.color" class="w-full">
            <el-option
              v-for="color in tagColors"
              :key="color.value"
              :label="color.label"
              :value="color.value"
            >
              <div class="flex items-center space-x-2">
                <div 
                  class="w-4 h-4 rounded-full" 
                  :class="color.class"
                ></div>
                <span>{{ color.label }}</span>
              </div>
            </el-option>
          </el-select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">标签描述</label>
          <el-input
            v-model="editDialog.form.description"
            type="textarea"
            :rows="3"
            placeholder="输入标签描述（可选）"
          />
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="saveTag">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Edit,
  Delete,
  Document,
  MoreFilled
} from '@element-plus/icons-vue'

interface TagItem {
  id: string
  name: string
  color: string
  description?: string
  documentCount: number
  createdAt: string
}

interface TagColor {
  value: string
  label: string
  class: string
}

// 标签颜色配置
const tagColors: TagColor[] = [
  { value: 'blue', label: '蓝色', class: 'bg-blue-500' },
  { value: 'green', label: '绿色', class: 'bg-green-500' },
  { value: 'yellow', label: '黄色', class: 'bg-yellow-500' },
  { value: 'red', label: '红色', class: 'bg-red-500' },
  { value: 'purple', label: '紫色', class: 'bg-purple-500' },
  { value: 'pink', label: '粉色', class: 'bg-pink-500' },
  { value: 'indigo', label: '靛蓝', class: 'bg-indigo-500' },
  { value: 'gray', label: '灰色', class: 'bg-gray-500' }
]

// 标签数据
const tags = ref<TagItem[]>([
  {
    id: '1',
    name: '质量管理',
    color: 'blue',
    description: '与医疗质量管理相关的文档',
    documentCount: 25,
    createdAt: '2024-01-15'
  },
  {
    id: '2',
    name: '医疗规范',
    color: 'green',
    description: '医疗行业标准和规范',
    documentCount: 18,
    createdAt: '2024-01-14'
  },
  {
    id: '3',
    name: '培训资料',
    color: 'yellow',
    description: '员工培训和教育资料',
    documentCount: 12,
    createdAt: '2024-01-13'
  },
  {
    id: '4',
    name: '政策法规',
    color: 'red',
    description: '相关法律法规和政策文件',
    documentCount: 8,
    createdAt: '2024-01-12'
  },
  {
    id: '5',
    name: '标准规范',
    color: 'purple',
    description: '行业标准和操作规范',
    documentCount: 15,
    createdAt: '2024-01-11'
  }
])

// 新标签表单
const newTagName = ref('')
const newTagColor = ref('blue')

// 编辑对话框
const editDialog = reactive({
  visible: false,
  form: {
    id: '',
    name: '',
    color: '',
    description: ''
  }
})

// 计算属性
const totalDocuments = computed(() => {
  return tags.value.reduce((sum, tag) => sum + tag.documentCount, 0)
})

const averageDocumentsPerTag = computed(() => {
  if (tags.value.length === 0) return 0
  return Math.round(totalDocuments.value / tags.value.length)
})

// 获取标签颜色类名
const getTagColorClass = (color: string): string => {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
    purple: 'bg-purple-500',
    pink: 'bg-pink-500',
    indigo: 'bg-indigo-500',
    gray: 'bg-gray-500'
  }
  return colorMap[color] || 'bg-gray-500'
}

// 添加标签
const addTag = () => {
  if (!newTagName.value.trim()) {
    ElMessage.warning('请输入标签名称')
    return
  }
  
  const existingTag = tags.value.find(tag => 
    tag.name.toLowerCase() === newTagName.value.toLowerCase()
  )
  
  if (existingTag) {
    ElMessage.warning('标签名称已存在')
    return
  }
  
  const newTag: TagItem = {
    id: Date.now().toString(),
    name: newTagName.value.trim(),
    color: newTagColor.value,
    description: '',
    documentCount: 0,
    createdAt: new Date().toISOString().split('T')[0]
  }
  
  tags.value.push(newTag)
  
  newTagName.value = ''
  newTagColor.value = 'blue'
  
  ElMessage.success('标签添加成功')
}

// 编辑标签
const editTag = (tag: TagItem) => {
  editDialog.form = {
    id: tag.id,
    name: tag.name,
    color: tag.color,
    description: tag.description || ''
  }
  editDialog.visible = true
}

// 保存标签
const saveTag = () => {
  if (!editDialog.form.name.trim()) {
    ElMessage.warning('请输入标签名称')
    return
  }
  
  const tag = tags.value.find(t => t.id === editDialog.form.id)
  if (tag) {
    tag.name = editDialog.form.name.trim()
    tag.color = editDialog.form.color
    tag.description = editDialog.form.description.trim()
    
    editDialog.visible = false
    ElMessage.success('标签更新成功')
  }
}

// 查看标签文档
const viewTaggedDocuments = (tag: TagItem) => {
  ElMessage.info(`查看标签 "${tag.name}" 的文档`)
}

// 删除标签
const deleteTag = async (tag: TagItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除标签 "${tag.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    if (tag.documentCount > 0) {
      await ElMessageBox.confirm(
        `标签 "${tag.name}" 下还有 ${tag.documentCount} 个文档，删除后这些文档将失去此标签。是否继续？`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    }
    
    const index = tags.value.findIndex(t => t.id === tag.id)
    if (index > -1) {
      tags.value.splice(index, 1)
    }
    
    ElMessage.success('标签删除成功')
  } catch {
    // 用户取消删除
  }
}
</script>

<style scoped>
/* 自定义样式 */
</style>