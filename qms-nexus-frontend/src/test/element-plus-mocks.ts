// Element Plus 组件模拟
import { vi } from 'vitest'

// 基础组件模拟
export const elementPlusMocks = {
  // 表单组件
  ElInput: {
    name: 'ElInput',
    template: '<div class="el-input"><input :placeholder="placeholder" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" @keyup.enter="$emit(\'keyup:enter\')" /></div>',
    props: ['modelValue', 'placeholder', 'clearable'],
    emits: ['update:modelValue', 'clear', 'keyup:enter']
  },
  
  ElSelect: {
    name: 'ElSelect',
    template: '<div class="el-select"><select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value); $emit(\'change\', $event.target.value)"><slot /></select></div>',
    props: ['modelValue', 'placeholder', 'clearable'],
    emits: ['update:modelValue', 'change', 'clear']
  },
  
  ElOption: {
    name: 'ElOption',
    template: '<option :value="value">{{ label }}</option>',
    props: ['value', 'label']
  },
  
  ElButton: {
    name: 'ElButton',
    template: '<button :class="buttonClass" @click="$emit(\'click\', $event)"><slot /></button>',
    props: ['type', 'size'],
    computed: {
      buttonClass() {
        return `el-button el-button--${this.type || 'default'} el-button--${this.size || 'default'}`
      }
    },
    emits: ['click']
  },
  
  // 表格组件
  ElTable: {
    name: 'ElTable',
    template: '<div class="el-table"><slot /></div>',
    props: ['data', 'loading'],
    emits: ['selection-change']
  },
  
  ElTableColumn: {
    name: 'ElTableColumn',
    template: '<div class="el-table-column"><slot /></div>',
    props: ['prop', 'label', 'width', 'min-width', 'type']
  },
  
  // 标签组件
  ElTag: {
    name: 'ElTag',
    template: '<span :class="tagClass"><slot /></span>',
    props: ['type'],
    computed: {
      tagClass() {
        return `el-tag el-tag--${this.type || 'info'}`
      }
    }
  },
  
  // 布局组件
  ElRow: {
    name: 'ElRow',
    template: '<div class="el-row" :style="rowStyle"><slot /></div>',
    props: ['gutter'],
    computed: {
      rowStyle() {
        return this.gutter ? { marginLeft: `-${this.gutter/2}px`, marginRight: `-${this.gutter/2}px` } : {}
      }
    }
  },
  
  ElCol: {
    name: 'ElCol',
    template: '<div class="el-col" :style="colStyle"><slot /></div>',
    props: ['span'],
    computed: {
      colStyle() {
        return this.span ? { width: `${(this.span / 24) * 100}%` } : {}
      }
    }
  },
  
  // 日期选择器
  ElDatePicker: {
    name: 'ElDatePicker',
    template: '<div class="el-date-picker"><input :placeholder="startPlaceholder" @change="handleChange" /></div>',
    props: ['modelValue', 'type', 'range-separator', 'start-placeholder', 'end-placeholder', 'format', 'value-format', 'clearable'],
    emits: ['update:modelValue', 'change', 'clear'],
    methods: {
      handleChange(event: Event) {
        this.$emit('update:modelValue', (event.target as HTMLInputElement).value)
        this.$emit('change', (event.target as HTMLInputElement).value)
      }
    }
  },
  
  // 分页
  ElPagination: {
    name: 'ElPagination',
    template: '<div class="el-pagination"><button @click="$emit(\'current-change\', currentPage - 1)">上一页</button><span>{{ currentPage }}</span><button @click="$emit(\'current-change\', currentPage + 1)">下一页</button></div>',
    props: ['currentPage', 'pageSize', 'total', 'pageSizes'],
    emits: ['current-change', 'size-change']
  },
  
  // 下拉菜单
  ElDropdown: {
    name: 'ElDropdown',
    template: '<div class="el-dropdown"><slot /></div>',
    props: ['trigger']
  },
  
  ElDropdownMenu: {
    name: 'ElDropdownMenu',
    template: '<div class="el-dropdown-menu"><slot /></div>'
  },
  
  ElDropdownItem: {
    name: 'ElDropdownItem',
    template: '<div class="el-dropdown-item" @click="$emit(\'click\', $event)"><slot /></div>',
    emits: ['click']
  },
  
  // 对话框
  ElDialog: {
    name: 'ElDialog',
    template: '<div v-if="visible" class="el-dialog"><div class="el-dialog__body"><slot /></div></div>',
    props: ['visible', 'title', 'width'],
    emits: ['update:visible', 'close']
  },
  
  // 结果组件
  ElResult: {
    name: 'ElResult',
    template: '<div class="el-result"><div class="el-result__icon"><el-icon :name="icon" /></div><div class="el-result__title">{{ title }}</div><div class="el-result__subtitle">{{ subTitle }}</div><div class="el-result__extra"><slot name="extra" /></div></div>',
    props: ['icon', 'title', 'subTitle']
  },
  
  // 图标
  ElIcon: {
    name: 'ElIcon',
    template: '<i :class="iconClass" />',
    props: ['name'],
    computed: {
      iconClass() {
        return `el-icon-${this.name}`
      }
    }
  },
  
  // 间距
  ElSpace: {
    name: 'ElSpace',
    template: '<div class="el-space" :style="spaceStyle"><slot /></div>',
    props: ['size', 'direction'],
    computed: {
      spaceStyle() {
        return {
          gap: this.size || '8px',
          flexDirection: this.direction === 'vertical' ? 'column' : 'row'
        }
      }
    }
  },
  
  // 加载状态
  ElLoading: {
    name: 'ElLoading',
    template: '<div v-if="loading" class="el-loading-mask"><div class="el-loading-spinner"><i class="el-icon-loading"></i></div></div>',
    props: ['loading']
  }
}

// 创建完整的 Element Plus 模拟
export function createElementPlusMock() {
  return {
    ...elementPlusMocks,
    // 消息组件
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    },
    // 消息框组件
    ElMessageBox: {
      confirm: vi.fn(() => Promise.resolve()),
      alert: vi.fn(() => Promise.resolve()),
      prompt: vi.fn(() => Promise.resolve())
    }
  }
}