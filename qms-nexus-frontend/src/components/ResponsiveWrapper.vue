// 响应式组件包装器
<template>
  <component
    :is="tag"
    v-bind="responsiveProps"
    class="responsive-component"
    :class="responsiveClasses"
  >
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useResponsive, getResponsiveConfig, type DeviceType } from '@/utils/responsive'

interface Props {
  tag?: string
  component?: 'el-button' | 'el-input' | 'el-table' | 'el-form' | 'el-card'
  mobile?: Record<string, any>
  tablet?: Record<string, any>
  desktop?: Record<string, any>
  large?: Record<string, any>
  classes?: {
    mobile?: string[]
    tablet?: string[]
    desktop?: string[]
    large?: string[]
  }
}

const props = withDefaults(defineProps<Props>(), {
  tag: 'div',
  component: undefined
})

const { deviceType } = useResponsive()

// 响应式属性
const responsiveProps = computed(() => {
  if (!props.component) {
    return {
      ...getResponsiveConfig(props.component as any, deviceType),
      ...props[deviceType]
    }
  }
  
  // 合并基础配置和自定义配置
  const baseConfig = getResponsiveConfig(props.component as any, deviceType)
  const customConfig = props[deviceType] || {}
  
  return {
    ...baseConfig,
    ...customConfig
  }
})

// 响应式类名
const responsiveClasses = computed(() => {
  const deviceClasses = props.classes?.[deviceType] || []
  const baseClasses = [`responsive-${deviceType}`]
  
  return [...baseClasses, ...deviceClasses].join(' ')
})
</script>

<style scoped>
.responsive-component {
  transition: all 0.3s ease;
}

.responsive-mobile {
  font-size: 14px;
}

.responsive-tablet {
  font-size: 15px;
}

.responsive-desktop {
  font-size: 16px;
}

.responsive-large {
  font-size: 18px;
}
</style>