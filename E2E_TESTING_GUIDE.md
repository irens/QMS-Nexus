# QMS-Nexus E2E测试执行指南

## 概述
本指南介绍如何运行QMS-Nexus项目的端到端(E2E)测试。E2E测试验证从前端用户界面到后端API的完整用户工作流。

## 环境要求
- Node.js v20+ (或 v22+)
- Python 3.10+
- npm 或 yarn 包管理器
- 已安装Chrome浏览器（用于Cypress测试）

## 启动服务

### 1. 启动后端服务
```bash
cd qms-nexus
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### 2. 启动前端服务
```bash
cd qms-nexus-frontend
npm run dev
```

## 运行E2E测试

### 1. 安装Cypress（首次运行）
```bash
cd qms-nexus-frontend
npm install --save-dev cypress
npx cypress install
```

### 2. 运行所有E2E测试（图形界面）
```bash
cd qms-nexus-frontend
npm run test:e2e
```

### 3. 运行所有E2E测试（无头模式）
```bash
cd qms-nexus-frontend
npm run test:e2e:headless
```

### 4. 运行特定测试文件
```bash
cd qms-nexus-frontend
npx cypress run --spec "cypress/e2e/homepage.cy.ts"
```

## 测试文件结构
```
cypress/
├── e2e/                    # E2E测试文件
│   ├── homepage.cy.ts      # 主页功能测试
│   ├── api-workflow.cy.ts  # API工作流测试
│   └── feature-specific.cy.ts # 特定功能测试
├── fixtures/               # 测试数据
├── support/                # 测试支持文件
│   ├── e2e.ts             # E2E测试支持
│   └── commands.ts        # 自定义命令
└── cypress.config.ts       # Cypress配置文件
```

## 当前可用的E2E测试

### 1. 主页功能测试 (`homepage.cy.ts`)
- 验证主页加载
- 导航到不同页面的功能

### 2. API工作流测试 (`api-workflow.cy.ts`)
- 验证文档上传流程
- 验证文档搜索功能
- 验证标签管理功能

### 3. 特定功能测试 (`feature-specific.cy.ts`)
- 上传页面功能
- 搜索页面功能
- 聊天界面功能

### 4. 完整工作流测试 (`full-workflow.cy.ts`)
- 完整的文档上传到查询工作流
- 验证来源标注格式（[来源：文件名, 第X页]）
- 错误处理验证

### 5. 需求导向测试 (`requirements-based.cy.ts`)
- 针对QMS-Nexus具体需求的测试用例
- 验证US-MVP-01至US-MVP-08需求
- 验证US-Alpha-02等高级需求

### 6. API集成测试 (`api-integration.cy.ts`)
- 验证正确的API端点（/api/v1/...）
- 测试新的问答API（/ask）
- 完整的端到端工作流验证

## CI/CD集成示例

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd qms-nexus-frontend
          npm ci
      - name: Install Cypress
        run: |
          cd qms-nexus-frontend
          npx cypress install
      - name: Start backend server
        run: |
          cd qms-nexus
          pip install -r requirements.txt
          python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
      - name: Start frontend server
        run: |
          cd qms-nexus-frontend
          npm run dev &
      - name: Wait for servers to be ready
        run: |
          sleep 10
      - name: Run E2E tests
        run: |
          cd qms-nexus-frontend
          npx cypress run
```

## 故障排除

### 1. 如果遇到跨域问题
确保后端API允许来自前端的跨域请求。

### 2. 如果测试超时
增加Cypress中的默认超时值：
```javascript
// cypress.config.ts
e2e: {
  defaultCommandTimeout: 10000,
  pageLoadTimeout: 60000,
}
```

### 3. 如何调试测试
使用 `.pause()` 命令在特定位置暂停测试：
```javascript
cy.get('[data-testid="upload-area"]').pause()
```

## 最佳实践

1. **页面对象模式**：为每个页面创建专门的页面对象
2. **数据清理**：每次测试前后清理测试数据
3. **独立测试**：确保每个测试都是独立的
4. **可重试性**：编写稳定的、可重试的测试
5. **有意义的断言**：编写清晰、有意义的断言