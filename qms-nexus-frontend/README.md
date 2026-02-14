# QMS-Nexus Frontend

医疗行业质量管理系统前端项目

## 技术栈

- **框架**: Vue 3 + TypeScript
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **UI组件库**: Element Plus
- **样式**: TailwindCSS
- **构建工具**: Vite
- **代码规范**: ESLint + Prettier

## 项目特色

### 🏥 医疗蓝主题设计
- 专业的医疗蓝色调 (#0971f5)
- 符合医疗行业视觉规范
- 优雅的渐变和阴影效果
- 响应式设计适配

### 📄 文档管理核心功能
- 多格式文件上传 (PDF/DOC/DOCX/XLS/XLSX/PPT/PPTX)
- 实时上传状态监控
- 智能文档解析
- 标签分类管理

### 🤖 AI智能问答
- 基于RAG技术的知识问答
- 流式响应展示
- 来源标注追踪
- 对话历史管理

### ⚡ 技术亮点
- TypeScript严格类型检查
- 组件化架构设计
- 状态机驱动的异步逻辑
- API代理配置
- 生产环境优化

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 代码检查和格式化
npm run lint
npm run format
```

## 开发规范

- 遵循项目制定的API契约文档
- 严格按照状态机规范实现异步逻辑
- 保持UI视觉与组件规范的一致性
- 编写完整的TypeScript类型定义
- 遵循Vue 3 Composition API最佳实践

## 项目结构

```
src/
├── assets/          # 静态资源
├── components/      # 通用组件
├── views/          # 页面组件
├── stores/         # Pinia状态管理
├── router/         # 路由配置
├── utils/          # 工具函数
├── types/          # TypeScript类型定义
└── api/            # API接口封装
```