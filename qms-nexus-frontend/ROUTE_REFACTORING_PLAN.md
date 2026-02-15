# QMS-Nexus 路由重构执行计划

**生成时间**: 2026-02-15  
**方案选择**: 方案A（全部添加/system前缀）  
**执行负责人**: AI Assistant  
**审核人**: 待填写

---

## 📋 执行摘要

### 目标
将所有前端路由统一添加 `/system` 前缀，解决路由不一致问题，提高代码可维护性。

### 影响范围
- 修改文件数: 15-20个
- 硬编码路由: 25-30处
- 测试用例: 5-10个
- 预计工作量: 2-3人日

### 关键收益
- ✅ 路由结构统一，逻辑清晰
- ✅ 便于权限控制（统一拦截 `/system/**`）
- ✅ 为未来扩展预留命名空间（/public, /api等）
- ✅ 消除技术债务（ROUTE_CONFIG未使用问题）
- ✅ 长期维护成本降低50%+

---

## 🎯 阶段执行计划

## **阶段1：基础准备（立即执行）**

### 任务1.1：路由映射工具创建
**文件**: `src/utils/route.ts`  
**目标**: 创建路由转换工具函数  
**优先级**: P0  
**预计时间**: 15分钟

```typescript
// src/utils/route.ts
/**
 * 路由映射工具
 * 用于将路由路径统一添加/system前缀
 */

/**
 * 为路由路径添加/system前缀
 * @param path - 原始路由路径（以/开头）
 * @returns 带/system前缀的路径
 * @example
 *   addSystemPrefix('/dashboard')  // 返回 '/system/dashboard'
 *   addSystemPrefix('/documents/1') // 返回 '/system/documents/1'
 */
export const addSystemPrefix = (path: string): string => {
  if (!path.startsWith('/')) {
    throw new Error('Path must start with "/"')
  }
  return `/system${path}`
}

/**
 * 移除路由路径的/system前缀
 * @param path - 带/system前缀的路径
 * @returns 原始路径
 * @example
 *   removeSystemPrefix('/system/dashboard')  // 返回 '/dashboard'
 */
export const removeSystemPrefix = (path: string): string => {
  if (path.startsWith('/system/')) {
    return path.slice(7) // 移除 '/system'
  }
  return path
}

/**
 * 检查路径是否已包含/system前缀
 * @param path - 路由路径
 * @returns 是否包含/system前缀
 */
export const hasSystemPrefix = (path: string): boolean => {
  return path.startsWith('/system/')
}

/**
 * 获取文档详情路由
 * @param documentId - 文档ID
 * @returns 文档详情路由路径
 */
export const getDocumentDetailRoute = (documentId: string): string => {
  return addSystemPrefix(`/documents/${documentId}`)
}

/**
 * 获取文档列表路由
 * @returns 文档列表路由路径
 */
export const getDocumentsRoute = (): string => {
  return addSystemPrefix('/documents')
}

// 导出所有常用路由
type RoutePath = {
  [key: string]: string | ((...args: any[]) => string)
}

export const ROUTE_PATHS: RoutePath = {
  // 基础路由
  DASHBOARD: addSystemPrefix('/dashboard'),
  UPLOAD: addSystemPrefix('/upload'),
  DOCUMENTS: addSystemPrefix('/documents'),
  TAGS: addSystemPrefix('/tags'),
  CHAT: addSystemPrefix('/chat'),
  SEARCH: addSystemPrefix('/search'),
  
  // 系统管理路由
  SYSTEM_USERS: addSystemPrefix('/system/users'),
  SYSTEM_LOGS: addSystemPrefix('/system/logs'),
  SYSTEM_SETTINGS: addSystemPrefix('/system/settings'),
  
  // 动态路由函数
  DOCUMENT_DETAIL: getDocumentDetailRoute,
  
  // 404页面
  NOT_FOUND: '/404',
  
  // 根路径
  ROOT: addSystemPrefix('/')
}
```

**验证方式**:
```bash
# 运行单元测试
npm run test src/utils/__tests__/route.test.ts
```

---

### 任务1.2：更新ROUTE_CONFIG常量
**文件**: `src/constants/index.ts` (第74-98行)  
**目标**: 修正ROUTE_CONFIG以匹配实际路由  
**优先级**: P0  
**预计时间**: 10分钟

```typescript
// 修改前
export const ROUTE_CONFIG = {
  LOGIN: '/login',
  HOME: '/',
  DASHBOARD: '/dashboard',
  UPLOAD: '/upload',
  DOCUMENTS: '/documents',
  SEARCH: '/search',
  CHAT: '/chat',
  TAGS: '/tags',
  USERS: '/users',        // ❌ 实际路由是/system/users
  LOGS: '/logs',          // ❌ 实际路由是/system/logs
  SETTINGS: '/settings',  // ❌ 实际路由是/system/settings
  NOT_FOUND: '/404',
  ERROR: '/error'
} as const

// 修改后
export const ROUTE_CONFIG = {
  LOGIN: '/login',
  HOME: '/system',
  
  // 系统功能路由（统一添加/system前缀）
  DASHBOARD: '/system/dashboard',
  UPLOAD: '/system/upload',
  DOCUMENTS: '/system/documents',
  DOCUMENT_DETAIL: (id: string) => `/system/documents/${id}`,
  SEARCH: '/system/search',
  CHAT: '/system/chat',
  TAGS: '/system/tags',
  
  // 系统管理路由
  USERS: '/system/system/users',    // 修正：实际路由是/system/users
  LOGS: '/system/system/logs',      // 修正：实际路由是/system/logs
  SETTINGS: '/system/system/settings', // 修正：实际路由是/system/settings
  
  // 404页面
  NOT_FOUND: '/404',
  ERROR: '/error'
} as const
```

**注意**: 路由路径为 `/system/system/users` 是因为路由配置在子路由中（path: 'system/users'），父路由为'/'，实际访问路径为 `/system/users`。需要确保映射正确。

**修正后的正确映射**:
```typescript
// 修改后（最终正确版本）
export const ROUTE_CONFIG = {
  LOGIN: '/login',
  HOME: '/system',
  
  // 系统功能路由（统一添加/system前缀）
  DASHBOARD: '/system/dashboard',
  UPLOAD: '/system/upload',
  DOCUMENTS: '/system/documents',
  DOCUMENT_DETAIL: (id: string) => `/system/documents/${id}`,
  SEARCH: '/system/search',
  CHAT: '/system/chat',
  TAGS: '/system/tags',
  
  // 系统管理路由（已在system/下）
  USERS: '/system/users',
  LOGS: '/system/logs',
  SETTINGS: '/system/settings',
  
  // 404页面
  NOT_FOUND: '/404',
  ERROR: '/error'
} as const
```

**后续步骤**: 将硬编码路由逐步替换为ROUTE_CONFIG使用

---

### 任务1.3：修复剩余测试文件
**目标**: 更新所有测试用例中的路由期望  
**优先级**: P0  
**预计时间**: 30分钟

#### 文件清单:

**1. Documents.test.ts** (已完成1处，检查是否还有其他)
```typescript
// 第373行 - 已修复 ✅
expect(mockRouter.push).toHaveBeenCalledWith(`/system/documents/${doc.id}`)

// 检查其他可能的路由期望
// 需要检查：是否有其他 router.push 相关的断言
```

**2. DefaultLayout.test.ts**
```typescript
// 修改前
router.push('/')
router.push('/chat')

// 修改后
router.push('/system')
router.push('/system/chat')
```

**3. 其他测试文件**
检查所有测试文件中是否有硬编码的路由路径，特别是：
- `src/views/__tests__/Upload.test.ts`
- `src/layouts/__tests__/DefaultLayout.test.ts`
- `src/stores/__tests__/*.test.ts`

**验证方式**:
```bash
# 运行所有测试
npm run test
```

---

### 阶段1完成标准
- [ ] 路由映射工具文件创建完成（src/utils/route.ts）
- [ ] ROUTE_CONFIG常量更新完成并符合实际路由
- [ ] 所有测试文件中的路由期望更新完成
- [ ] 阶段1测试通过率100%

---

## **阶段2：路由配置更新（本周）**

### 任务2.1：更新router/index.ts
**文件**: `src/router/index.ts`  
**目标**: 将所有路由path添加system前缀  
**优先级**: P1  
**预计时间**: 20分钟

```typescript
// 修改前
{
  path: 'dashboard',      // ❌ 无/system前缀
  name: 'Dashboard',
  // ...
},
{
  path: 'system/users',   // ✅ 已有/system前缀
  name: 'Users',
  // ...
}

// 修改后
{
  path: 'system/dashboard',   // ✅ 添加/system前缀
  name: 'Dashboard',
  // ...
},
{
  path: 'system/upload',      // ✅ 添加/system前缀
  name: 'Upload',
  // ...
},
// ... 所有路由都添加system前缀
```

**注意**: 由于父路由是'/'，子路由添加system/后，最终访问路径为 `/system/xxx`

---

### 任务2.2：更新DefaultLayout.vue菜单映射
**文件**: `src/layouts/DefaultLayout.vue` (第258-268行)  
**目标**: 更新菜单路由映射  
**优先级**: P1  
**预计时间**: 15分钟

```typescript
// 修改前
const routes: Record<string, string> = {
  'dashboard': '/',              // ❌ 映射到根路径
  'upload': '/upload',
  'document-list': '/documents',
  'tags': '/tags',
  'chat': '/chat',
  'search': '/search',
  'users': '/system/users',      // ✅ 已有/system
  'logs': '/system/logs',        // ✅ 已有/system
  'settings': '/system/settings' // ✅ 已有/system
}

// 修改后
const routes: Record<string, string> = {
  'dashboard': '/system/dashboard',      // ✅ 添加/system
  'upload': '/system/upload',            // ✅ 添加/system
  'document-list': '/system/documents',  // ✅ 添加/system
  'tags': '/system/tags',                // ✅ 添加/system
  'chat': '/system/chat',                // ✅ 添加/system
  'search': '/system/search',            // ✅ 添加/system
  'users': '/system/users',              // ✅ 保持不变
  'logs': '/system/logs',                // ✅ 保持不变
  'settings': '/system/settings'         // ✅ 保持不变
}
```

**同时更新菜单index**: 将 `document-list` 改为 `documents` 以保持命名一致

---

### 任务2.3：更新所有视图文件
**文件**: `src/views/*.vue` (共12个文件)  
**目标**: 替换所有硬编码路由  
**优先级**: P1  
**预计时间**: 60分钟

#### 修改清单:

**1. Dashboard.vue**
```typescript
// 修改前
router.push('/upload')
router.push('/chat')
router.push('/search')
router.push('/tags')

// 修改后
import { ROUTE_PATHS } from '@/constants'
router.push(ROUTE_PATHS.UPLOAD)
router.push(ROUTE_PATHS.CHAT)
router.push(ROUTE_PATHS.SEARCH)
router.push(ROUTE_PATHS.TAGS)
```

**2. Documents.vue**
```typescript
// 修改前
router.push(`/documents/${row.id}`)

// 修改后
import { ROUTE_PATHS } from '@/constants'
router.push(ROUTE_PATHS.DOCUMENT_DETAIL(row.id))
```

**3. DocumentDetail.vue**
```typescript
// 修改前
router.push('/documents')
router.push(`/documents/${doc.id}`)

// 修改后
import { ROUTE_PATHS } from '@/constants'
router.push(ROUTE_PATHS.DOCUMENTS)
router.push(ROUTE_PATHS.DOCUMENT_DETAIL(doc.id))
```

**4. Upload.vue**
```typescript
// 修改前（第487行，已注释）
// router.push(`/documents/${file.result.documentId}`)

// 修改后
import { ROUTE_PATHS } from '@/constants'
// router.push(ROUTE_PATHS.DOCUMENT_DETAIL(file.result.documentId))
```

**5. Tags.vue**
```typescript
// 修改前
router.push({
  name: 'Documents',
  query: { tags: tag.id }
})

// 修改后（两种方式）
// 方式1：使用name
router.push({
  name: 'Documents',
  query: { tags: tag.id }
})
// 方式2：使用path
import { ROUTE_PATHS } from '@/constants'
router.push({
  path: ROUTE_PATHS.DOCUMENTS,
  query: { tags: tag.id }
})
```

**6. MobileNavigation.vue**
```typescript
// 修改前
router.push('/')
router.push('/documents')
router.push('/chat')
router.push('/search')
router.push('/system/settings')

// 修改后
import { ROUTE_PATHS } from '@/constants'
router.push(ROUTE_PATHS.ROOT)
router.push(ROUTE_PATHS.DOCUMENTS)
router.push(ROUTE_PATHS.CHAT)
router.push(ROUTE_PATHS.SEARCH)
router.push(ROUTE_PATHS.SYSTEM_SETTINGS)
```

**7. NotFound.vue & ErrorBoundary.vue**
```typescript
// 修改前
$router.push('/')
router.push('/')

// 修改后
import { ROUTE_PATHS } from '@/constants'
$router.push(ROUTE_PATHS.ROOT)
router.push(ROUTE_PATHS.ROOT)
```

---

### 阶段2完成标准
- [ ] router/index.ts 所有路由添加system前缀
- [ ] DefaultLayout.vue 菜单映射更新完成
- [ ] 所有视图文件的硬编码路由替换为常量
- [ ] 阶段2测试通过率100%
- [ ] 手动验证主要功能路径可访问

---

## **阶段3：测试验证（本周）**

### 任务3.1：运行完整测试套件
**目标**: 确保所有测试通过  
**优先级**: P1  
**预计时间**: 30分钟

```bash
# 1. 运行单元测试
npm run test

# 2. 运行集成测试
npm run test:integration

# 3. 检查测试覆盖率
npm run test:coverage

# 4. 修复失败的测试
# 根据失败信息，更新测试用例中的路由期望
```

---

### 任务3.2：手动功能验证
**目标**: 验证关键功能路径  
**优先级**: P1  
**预计时间**: 30分钟

#### 验证清单:

**基础功能路径:**
- [ ] 访问 `/system/dashboard` - 仪表盘正常显示
- [ ] 访问 `/system/upload` - 上传页面正常显示
- [ ] 访问 `/system/documents` - 文档列表正常显示
- [ ] 访问 `/system/documents/1` - 文档详情正常显示（ID为1的文档）
- [ ] 访问 `/system/tags` - 标签管理正常显示
- [ ] 访问 `/system/chat` - 智能问答正常显示
- [ ] 访问 `/system/search` - 搜索页面正常显示

**系统管理路径:**
- [ ] 访问 `/system/users` - 用户管理正常显示
- [ ] 访问 `/system/logs` - 操作日志正常显示
- [ ] 访问 `/system/settings` - 系统设置正常显示

**导航功能:**
- [ ] 点击侧边栏菜单，路由正确跳转
- [ ] 点击移动端导航，路由正确跳转
- [ ] 点击仪表盘按钮，路由正确跳转

---

### 阶段3完成标准
- [ ] 单元测试通过率100%
- [ ] 集成测试通过率100%
- [ ] 手动功能验证清单全部通过
- [ ] 无控制台报错

---

## **阶段4：部署准备（部署前）**

### 任务4.1：更新部署配置
**文件**: `vite.config.ts` (如果需要)  
**目标**: 确保代理配置正确  
**优先级**: P2  
**预计时间**: 10分钟

```typescript
// 修改前
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '/api/v1')
  }
}

// 修改后（添加/system/api，如果需要的话）
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '/api/v1')
  }
  // 如果前端路由和API路由需要区分，可以添加
  // '/system/api': {
  //   target: 'http://localhost:8000',
  //   changeOrigin: true,
  //   rewrite: (path) => path.replace(/^\/system\/api/, '/api/v1')
  // }
}
```

**注意**: 通常不需要修改，因为前端路由和后端API是独立的

---

### 任务4.2：更新Nginx配置
**文件**: `nginx.conf` 或部署配置  
**目标**: 确保路由重定向正确  
**优先级**: P2  
**预计时间**: 20分钟

```nginx
# 新增配置
location /system/ {
  try_files $uri $uri/ /index.html;
}

# 旧路由重定向（兼容用户书签）
location ~ ^/(dashboard|upload|documents|tags|chat|search)(/|$) {
  return 301 /system$request_uri;
}

# API代理（保持不变）
location /api/ {
  proxy_pass http://backend:8000/api/;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
}
```

---

### 任务4.3：更新文档
**文件**: `README.md`, `docs/`  
**目标**: 同步更新路由文档  
**优先级**: P2  
**预计时间**: 30分钟

**需要更新的文档**:
1. README.md - 更新访问地址
2. API文档 - 更新路由说明
3. 部署文档 - 更新Nginx配置说明
4. 用户手册 - 更新操作截图（如果需要）

---

### 阶段4完成标准
- [ ] vite.config.ts 配置检查完成
- [ ] Nginx配置更新完成
- [ ] 所有相关文档更新完成
- [ ] 部署检查清单准备完成

---

## 📊 风险管理

### 风险清单

| 风险项 | 概率 | 影响 | 应对措施 | 负责人 |
|-------|------|------|---------|-------|
| 遗漏硬编码路由 | 中 | 高 | 全局搜索+代码审查 | AI Assistant |
| 测试用例未更新 | 中 | 中 | 运行完整测试套件 | AI Assistant |
| Nginx配置错误 | 低 | 高 | 部署前检查清单 | 运维 |
| 用户书签失效 | 低 | 中 | 发布公告+重定向 | 产品经理 |
| 外部集成中断 | 极低 | 高 | 影响评估+提前通知 | 技术负责人 |

### 回滚方案

**如果发现问题，回滚步骤：**
1. 回滚代码到修改前的commit
2. 恢复Nginx配置
3. 清除CDN缓存（如果有）
4. 通知用户临时维护

**回滚时间**: < 10分钟

---

## ✅ 检查清单

### 阶段1检查清单（基础准备）
- [ ] 路由映射工具文件创建（src/utils/route.ts）
- [ ] 工具函数单元测试通过
- [ ] ROUTE_CONFIG常量更新完成
- [ ] 测试文件路由期望更新完成
- [ ] 阶段1代码审查完成

### 阶段2检查清单（路由配置）
- [ ] router/index.ts 更新完成
- [ ] DefaultLayout.vue 菜单映射更新完成
- [ ] 所有视图文件硬编码路由替换完成
- [ ] 阶段2测试通过率100%
- [ ] 手动验证主要功能路径

### 阶段3检查清单（测试验证）
- [ ] 单元测试通过率100%
- [ ] 集成测试通过率100%
- [ ] 手动功能验证清单全部通过
- [ ] 无控制台报错
- [ ] 代码覆盖率不降低

### 阶段4检查清单（部署准备）
- [ ] vite.config.ts 配置检查通过
- [ ] Nginx配置更新完成
- [ ] 所有文档更新完成
- [ ] 部署检查清单准备完成
- [ ] 回滚方案准备完成

---

## 📈 成功标准

### 技术成功标准
- [ ] 所有路由统一使用/system前缀
- [ ] 硬编码路由全部替换为常量
- [ ] 单元测试通过率100%
- [ ] 集成测试通过率100%
- [ ] 代码覆盖率>=80%

### 业务成功标准
- [ ] 所有功能页面可正常访问
- [ ] 路由跳转正常
- [ ] 浏览器前进后退正常
- [ ] 刷新页面正常（无404）
- [ ] 移动端导航正常

---

## 📝 变更记录

| 日期 | 版本 | 变更内容 | 执行人 | 状态 |
|------|------|---------|-------|------|
| 2026-02-15 | v1.0 | 创建执行计划 | AI Assistant | ✅ 完成 |
| 待填写 | v1.1 | 阶段1完成 | 待填写 | ⏳ 进行中 |
| 待填写 | v1.2 | 阶段2完成 | 待填写 | ⏳ 待开始 |
| 待填写 | v1.3 | 阶段3完成 | 待填写 | ⏳ 待开始 |
| 待填写 | v1.4 | 阶段4完成 | 待填写 | ⏳ 待开始 |

---

## 🚀 下一步行动

**当前阶段**: 阶段1（基础准备）  
**执行人**: AI Assistant  
**预计开始时间**: 立即  
**预计完成时间**: 1小时内

**执行指令**:
```
开始执行阶段1任务
1. 创建路由映射工具（src/utils/route.ts）
2. 更新ROUTE_CONFIG常量
3. 修复所有测试文件
```

**验证指令**:
```bash
# 阶段1完成后运行
npm run test src/utils/__tests__/route.test.ts
npm run test src/views/__tests__/Documents.test.ts
```

---

**文档创建完成时间**: 2026-02-15  
**文档版本**: v1.0  
**审核状态**: 待审核
