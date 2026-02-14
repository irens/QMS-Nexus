# QMS-Nexus 前端 UI 视觉与组件规范

## 设计系统概述

### 设计理念
- **专业性**: 体现医疗器械行业的严谨性和权威性
- **现代感**: 采用现代化设计语言，简洁而不失专业
- **易用性**: 清晰的视觉层次，直观的交互反馈
- **一致性**: 统一的视觉语言和交互模式

## 色彩系统 (Design Tokens)

### 主色调
```css
:root {
  /* 医疗蓝 - 主品牌色 */
  --color-primary: #1890ff;
  --color-primary-hover: #40a9ff;
  --color-primary-active: #096dd9;
  --color-primary-light: #e6f7ff;
  
  /* 深空灰 - 文字和背景 */
  --color-text-primary: #001529;
  --color-text-secondary: #595959;
  --color-text-disabled: #bfbfbf;
  
  /* 状态色 */
  --color-success: #52c41a;
  --color-warning: #faad14;
  --color-error: #ff4d4f;
  --color-info: #1890ff;
  
  /* 中性色 */
  --color-white: #ffffff;
  --color-black: #000000;
  --color-gray-1: #fafafa;
  --color-gray-2: #f5f5f5;
  --color-gray-3: #f0f0f0;
  --color-gray-4: #d9d9d9;
  --color-gray-5: #bfbfbf;
  --color-gray-6: #8c8c8c;
  --color-gray-7: #595959;
  --color-gray-8: #434343;
  --color-gray-9: #262626;
  --color-gray-10: #1f1f1f;
}
```

### Tailwind 配置
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1890ff',
          hover: '#40a9ff',
          active: '#096dd9',
          light: '#e6f7ff'
        },
        success: '#52c41a',
        warning: '#faad14',
        error: '#ff4d4f',
        info: '#1890ff',
        text: {
          primary: '#001529',
          secondary: '#595959',
          disabled: '#bfbfbf'
        }
      }
    }
  }
};
```

## 字体系统

### 字体族
```css
:root {
  /* 主要字体 */
  --font-family-primary: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
    'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 
    'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
  
  /* 等宽字体 */
  --font-family-mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, 
    Courier, monospace;
  
  /* 中文字体优化 */
  --font-family-zh: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 
    'WenQuanYi Micro Hei', sans-serif;
}
```

### 字号系统
```css
:root {
  /* 标题 */
  --font-size-h1: 32px;
  --font-size-h2: 24px;
  --font-size-h3: 20px;
  --font-size-h4: 16px;
  
  /* 正文 */
  --font-size-base: 14px;
  --font-size-small: 12px;
  --font-size-large: 16px;
  
  /* 辅助文本 */
  --font-size-caption: 12px;
  --font-size-helper: 12px;
}
```

### 字重系统
```css
:root {
  --font-weight-light: 300;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
}
```

## 间距系统

### 基础间距
```css
:root {
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 12px;
  --spacing-lg: 16px;
  --spacing-xl: 24px;
  --spacing-2xl: 32px;
  --spacing-3xl: 48px;
}
```

### 圆角系统
```css
:root {
  --border-radius-sm: 2px;
  --border-radius-base: 4px;
  --border-radius-lg: 6px;
  --border-radius-xl: 8px;
  --border-radius-round: 50%;
}
```

## 通用组件规范

### 按钮组件 (Button)

#### 按钮类型
```typescript
interface ButtonProps {
  type: 'primary' | 'success' | 'warning' | 'error' | 'info' | 'default';
  size: 'small' | 'medium' | 'large';
  variant: 'filled' | 'outlined' | 'text';
  disabled?: boolean;
  loading?: boolean;
  icon?: string;
  iconPosition?: 'left' | 'right';
}
```

#### 按钮状态样式
```css
/* 主要按钮 */
.btn-primary {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-white);
}

.btn-primary:hover {
  background-color: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

.btn-primary:active {
  background-color: var(--color-primary-active);
  border-color: var(--color-primary-active);
}

.btn-primary:disabled {
  background-color: var(--color-gray-4);
  border-color: var(--color-gray-4);
  color: var(--color-gray-6);
  cursor: not-allowed;
}

/* 加载状态 */
.btn-loading {
  position: relative;
  pointer-events: none;
}

.btn-loading::before {
  content: '';
  position: absolute;
  inset: 0;
  background-color: rgba(255, 255, 255, 0.4);
  border-radius: inherit;
}
```

### 输入框组件 (Input)

#### 输入框状态
```css
.input-base {
  border: 1px solid var(--color-gray-4);
  border-radius: var(--border-radius-base);
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-base);
  transition: all 0.3s ease;
}

.input-base:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  outline: none;
}

.input-error {
  border-color: var(--color-error);
}

.input-error:focus {
  box-shadow: 0 0 0 2px rgba(255, 77, 79, 0.2);
}

.input-disabled {
  background-color: var(--color-gray-2);
  color: var(--color-gray-6);
  cursor: not-allowed;
}
```

### 卡片组件 (Card)

#### 卡片样式
```css
.card {
  background-color: var(--color-white);
  border-radius: var(--border-radius-lg);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: var(--spacing-lg);
  transition: box-shadow 0.3s ease;
}

.card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.card-header {
  border-bottom: 1px solid var(--color-gray-3);
  padding-bottom: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}
```

## 图标系统

### 文件类型图标映射
```typescript
const fileTypeIcons = {
  'application/pdf': {
    icon: 'file-pdf',
    color: '#ff4d4f',
    label: 'PDF'
  },
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {
    icon: 'file-word',
    color: '#1890ff',
    label: 'Word'
  },
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': {
    icon: 'file-excel',
    color: '#52c41a',
    label: 'Excel'
  },
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': {
    icon: 'file-ppt',
    color: '#faad14',
    label: 'PPT'
  },
  'default': {
    icon: 'file-unknown',
    color: '#8c8c8c',
    label: '未知'
  }
};
```

### 状态图标
```typescript
const statusIcons = {
  'success': {
    icon: 'check-circle',
    color: '#52c41a'
  },
  'warning': {
    icon: 'exclamation-circle',
    color: '#faad14'
  },
  'error': {
    icon: 'close-circle',
    color: '#ff4d4f'
  },
  'info': {
    icon: 'info-circle',
    color: '#1890ff'
  },
  'loading': {
    icon: 'loading',
    color: '#1890ff',
    animated: true
  }
};
```

### 操作图标
```typescript
const actionIcons = {
  'upload': 'upload',
  'download': 'download',
  'delete': 'delete',
  'edit': 'edit',
  'search': 'search',
  'filter': 'filter',
  'sort': 'sort',
  'refresh': 'refresh',
  'settings': 'settings',
  'user': 'user',
  'logout': 'logout',
  'menu': 'menu',
  'close': 'close',
  'back': 'arrow-left',
  'forward': 'arrow-right',
  'up': 'arrow-up',
  'down': 'arrow-down'
};
```

## 动画效果

### 过渡动画
```css
/* 淡入淡出 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 滑入滑出 */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from {
  transform: translateX(-100%);
}

.slide-leave-to {
  transform: translateX(100%);
}

/* 缩放 */
.zoom-enter-active,
.zoom-leave-active {
  transition: transform 0.3s ease;
}

.zoom-enter-from,
.zoom-leave-to {
  transform: scale(0.9);
  opacity: 0;
}
```

### 加载动画
```css
/* 旋转加载 */
.loading-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 脉冲加载 */
.loading-pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

## 响应式断点

### 断点定义
```css
:root {
  --breakpoint-xs: 480px;
  --breakpoint-sm: 576px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 992px;
  --breakpoint-xl: 1200px;
  --breakpoint-2xl: 1600px;
}
```

### 媒体查询
```css
/* 超小屏幕 */
@media (max-width: 480px) {
  /* 移动端样式 */
}

/* 小屏幕 */
@media (min-width: 481px) and (max-width: 576px) {
  /* 小屏移动端样式 */
}

/* 中等屏幕 */
@media (min-width: 577px) and (max-width: 768px) {
  /* 平板样式 */
}

/* 大屏幕 */
@media (min-width: 769px) and (max-width: 1200px) {
  /* 桌面端样式 */
}

/* 超大屏幕 */
@media (min-width: 1201px) {
  /* 大屏桌面端样式 */
}
```

## 可访问性规范

### 色彩对比度
- 普通文本: 对比度 ≥ 4.5:1
- 大文本(18pt+): 对比度 ≥ 3:1
- 交互元素: 对比度 ≥ 4.5:1

### 焦点指示器
```css
/* 焦点样式 */
.focus-visible:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* 键盘导航焦点 */
.focus-keyboard:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

### 屏幕阅读器支持
```html
<!-- aria-label 示例 -->
<button aria-label="上传PDF文件" class="btn-upload">
  <i class="icon-upload"></i>
</button>

<!-- aria-live 示例 -->
<div aria-live="polite" class="status-message">
  文件上传成功
</div>
```

## 组件库使用指南

### Element Plus 主题定制
```javascript
// element-plus-theme.js
import { setConfig } from 'element-plus';

setConfig({
  theme: {
    colors: {
      primary: '#1890ff',
      success: '#52c41a',
      warning: '#faad14',
      danger: '#ff4d4f',
      error: '#ff4d4f',
      info: '#1890ff'
    }
  }
});
```

### 自定义组件规范
```typescript
// 组件Props接口定义
interface BaseComponentProps {
  className?: string;
  style?: CSSProperties;
  id?: string;
  testId?: string; // 测试用ID
}

// 组件状态接口
interface ComponentState {
  isLoading?: boolean;
  error?: string;
  isDisabled?: boolean;
}
```

这个UI视觉与组件规范确保了QMS-Nexus前端界面的一致性、专业性和可维护性，为开发团队提供了清晰的设计指导。