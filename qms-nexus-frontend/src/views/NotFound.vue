<template>
  <div class="p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-2">404 - 页面未找到</h1>
      <p class="text-gray-600">您访问的页面不存在</p>
    </div>
    
    <div class="text-center py-12">
      <el-icon size="64" class="text-gray-300 mb-4">
        <Warning />
      </el-icon>
      <h3 class="text-lg font-medium text-gray-600 mb-4">抱歉，页面不存在</h3>
      <p class="text-gray-500 mb-6">您访问的页面可能已被删除或链接错误</p>
      <el-button type="primary" @click="$router.push('/')">
        <el-icon class="mr-2"><House /></el-icon>
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Warning, House } from '@element-plus/icons-vue'
</script>