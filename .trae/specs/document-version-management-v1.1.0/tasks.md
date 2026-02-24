# 文档版本管理系统 v1.1.0 任务清单

## 任务组1：数据库架构升级（P0阻塞性）

### 任务1：创建文档版本管理表结构
**优先级**: P0（阻塞性）  
**文件**: `core/database.py` (修改)  
**当前状态**: documents 表无版本管理字段  
**目标状态**: 支持完整的文档版本生命周期管理

**详细需求**:
1. 修改 documents 表，添加版本管理字段：
   - `file_hash`: VARCHAR(64) - SHA256 文件哈希，用于去重
   - `version_number`: INTEGER - 版本号（1, 2, 3...）
   - `version_label`: VARCHAR(50) - 版本标签（V1.0, V1.1, V2.0）
   - `status`: VARCHAR(20) - 版本状态（draft/review/approved/effective/obsolete/archived）
   - `change_summary`: TEXT - 变更摘要
   - `change_details`: TEXT - 变更详细说明
   - `previous_version_id`: VARCHAR(36) - 上一版本ID
   - `effective_date`: DATETIME - 生效日期
   - `review_date`: DATETIME - 复审日期
   - `is_latest`: BOOLEAN - 是否最新版本
   - `prepared_by`: VARCHAR(50) - 编制人
   - `reviewed_by`: VARCHAR(50) - 审核人
   - `approved_by`: VARCHAR(50) - 批准人
   - `approved_date`: DATETIME - 批准日期
2. 创建 document_versions 表（版本历史表）
3. 创建 document_approval_history 表（审批历史）
4. 创建 document_distribution 表（文档分发/培训记录）
5. 添加唯一约束：(document_id, version_number)
6. 创建索引：idx_status_effective_date, idx_kb_id_is_latest
7. 编写数据迁移脚本，将现有文档标记为 V1.0

**验收标准**:
- [ ] 所有表结构符合医疗器械文档管理规范
- [ ] 现有数据成功迁移到新结构
- [ ] 索引创建成功，查询性能正常
- [ ] 外键约束正确设置

---

### 任务2：实现文档版本数据访问层
**优先级**: P0  
**文件**: `core/document_version_store.py` (新建)  
**当前状态**: 无版本管理数据访问层  
**目标状态**: 完整的版本管理 CRUD 操作

**详细需求**:
1. 创建 DocumentVersionStore 类
2. 实现方法：
   - `create_version()`: 创建新版本，自动递增版本号
   - `get_version_by_id()`: 获取版本详情
   - `get_versions_by_document()`: 获取文档所有版本
   - `get_latest_version()`: 获取最新版本
   - `get_effective_version_at_date()`: 获取指定日期生效的版本
   - `update_version_status()`: 更新版本状态
   - `approve_version()`: 审批通过版本
   - `obsolete_version()`: 作废版本
   - `compare_versions()`: 对比两个版本差异
3. 实现审批历史记录自动写入
4. 实现版本状态流转验证（防止非法状态变更）
5. 支持事务操作，确保数据一致性

**表结构参考** (DocumentVersion 模型):
```python
id = Column(String(36), primary_key=True)
document_id = Column(String(36), nullable=False)
version_number = Column(Integer, nullable=False)
version_label = Column(String(50))
filename = Column(String(255), nullable=False)
file_hash = Column(String(64), nullable=False)
file_size = Column(Integer)
file_type = Column(String(50))
status = Column(String(20), default='draft')
title = Column(String(255))
description = Column(Text)
doc_type = Column(String(50))
doc_code = Column(String(50))
change_summary = Column(Text)
change_details = Column(Text)
previous_version_id = Column(String(36), ForeignKey('document_versions.id'))
effective_date = Column(DateTime)
review_date = Column(DateTime)
is_latest = Column(Boolean, default=False)
prepared_by = Column(String(50))
reviewed_by = Column(String(50))
approved_by = Column(String(50))
approved_date = Column(DateTime)
kb_id = Column(String(36), ForeignKey('knowledge_bases.id'))
created_by = Column(String(50))
created_at = Column(DateTime, default=datetime.now)
updated_at = Column(DateTime, default=datetime.now)
```

**验收标准**:
- [ ] 所有 CRUD 操作正常
- [ ] 状态流转验证正确（如：draft→review→approved→effective）
- [ ] 审批历史自动记录
- [ ] 事务回滚正常

**依赖**: 任务1

**开发规范**:
- PEP 8 规范，使用类型注解
- 函数和类添加 docstring
- 使用 `with db_manager.get_session() as session:` 管理事务
- 错误处理：数据库异常 500，唯一约束冲突 409，资源不存在 404

**参考文档**:
- architecture_v1.1.0.md 第2.1节 - 数据库表结构
- todo_v1.1.0.md 任务1

---

## 任务组2：后端 API 开发（P0）

### 任务3：实现文档版本管理 API
**优先级**: P0  
**文件**: `api/routes/document_versions.py` (新建)  
**当前状态**: 无版本管理 API  
**目标状态**: 完整的版本管理 REST API

**详细需求**:
1. API: POST /api/v1/documents/{id}/versions
   - 上传新版本
   - 自动检测文件哈希重复
   - 自动递增版本号
   - 支持填写变更说明
2. API: GET /api/v1/documents/{id}/versions
   - 获取文档版本历史列表
   - 支持分页、排序
3. API: GET /api/v1/documents/versions/{version_id}
   - 获取版本详情
   - 包含审批历史
4. API: POST /api/v1/documents/versions/{version_id}/approve
   - 审批通过版本
   - 自动将上一版本标记为 obsolete
   - 记录审批人、审批时间
5. API: POST /api/v1/documents/versions/{version_id}/reject
   - 审批拒绝，返回 draft 状态
6. API: POST /api/v1/documents/versions/{version_id}/obsolete
   - 作废版本（质量经理权限）
7. API: GET /api/v1/documents/versions/{v1_id}/compare/{v2_id}
   - 对比两个版本差异
   - 返回新增/删除/修改的内容块
8. API: GET /api/v1/documents/versions/{version_id}/download
   - 下载特定版本的原始文件

**验收标准**:
- [ ] 所有 API 返回正确数据格式
- [ ] 状态流转正确
- [ ] 权限控制生效（审批需要特定角色）
- [ ] 版本对比功能正常

**依赖**: 任务2

---

### 任务4：实现文件去重检测 API
**优先级**: P0  
**文件**: `api/routes/upload.py` (修改)  
**当前状态**: 无去重检测  
**目标状态**: 上传前自动检测重复文件

**详细需求**:
1. API: POST /api/v1/upload/check-duplicate
   - 请求: {file_hash, filename, kb_id}
   - 响应: 
     ```json
     {
       "type": "exact_match|name_match|new_file",
       "message": "提示信息",
       "existingDocument": { /* 现有文档信息 */ },
       "suggestions": ["作为新版本上传", "重命名上传", "取消"]
     }
     ```
2. 修改现有上传接口，集成去重检测
3. 支持三种处理方式：
   - 完全相同的文件（哈希相同）：提示已存在，提供"查看现有版本"、"强制重新上传"
   - 同名不同内容（哈希不同）：提示"创建为新版本"或"重命名"
   - 新文件：正常上传流程
4. 记录去重检测日志

**验收标准**:
- [ ] 能正确识别相同文件（哈希匹配）
- [ ] 能正确识别同名文件（名称匹配）
- [ ] 响应包含处理建议
- [ ] 前端能正确展示选项

**依赖**: 任务2

---

## 任务组3：RAG 服务升级（P0）

### 任务5：修改 RAG 服务支持版本管理
**优先级**: P0  
**文件**: `services/rag_service.py` (修改), `core/vectordb.py` (修改)  
**当前状态**: 搜索所有文档，无版本过滤  
**目标状态**: 默认只搜索最新生效版本

**详细需求**:
1. 修改向量库文档元数据结构，添加版本信息：
   - version_id, version_number, version_label
   - status, effective_date, is_latest
2. 修改 RAGService.search() 方法：
   - 默认只搜索 is_latest=true 且 status=effective 的文档
   - 添加参数 version_strategy: latest_effective | specific_date | all_versions
   - 添加参数 specific_date: 指定日期，搜索该日期生效的版本
3. 修改 RAGService.answer() 方法：
   - 在答案中标注引用文档的版本信息
   - 如果引用的是历史版本，提示用户"该版本已作废，查看最新版本"
4. 实现版本对比搜索（用于回答"新旧版本有什么区别"）

**向量库元数据结构**:
```json
{
  "id": "chunk_uuid",
  "text": "文本内容",
  "metadata": {
    "filename": "GJZ-QP-01.docx",
    "file_type": "docx",
    "page": 1,
    "doc_id": "文档组ID",
    "version_id": "版本ID",
    "version_number": 2,
    "version_label": "V2.1",
    "status": "effective",
    "effective_date": "2024-01-15",
    "is_latest": true,
    "kb_id": "知识库ID"
  }
}
```

**验收标准**:
- [ ] 默认只返回最新生效版本的结果
- [ ] 支持按日期搜索历史版本
- [ ] 答案中包含版本信息标注
- [ ] 作废版本有明确提示

**依赖**: 任务3

---

## 任务组4：前端界面开发（P0）

### 任务6：实现文档版本管理界面
**优先级**: P0  
**文件**: `src/views/documents/DocumentVersions.vue` (新建)  
**当前状态**: 无版本管理界面  
**目标状态**: 完整的版本管理 UI

**详细需求**:
1. 文档列表页增强：
   - 显示当前版本号、版本标签、状态
   - 显示生效日期、下次复审日期
   - 状态标签颜色区分（生效中-绿色、审核中-黄色、已作废-灰色）
2. 版本历史页面：
   - 时间轴展示所有版本
   - 显示版本号、版本标签、状态、生效日期
   - 显示变更摘要
   - 支持点击查看版本详情
   - 支持对比任意两个版本
3. 版本详情页面：
   - 显示完整的版本元数据
   - 显示审批历史（时间轴）
   - 显示文档分发/培训记录
   - 操作按钮：[下载] [审批] [作废] [上传新版本]
4. 版本对比页面：
   - 左右对比展示两个版本内容
   - 高亮显示新增、删除、修改的部分
   - 显示变更统计（新增X处、删除Y处、修改Z处）

**验收标准**:
- [ ] 界面符合 Element Plus 设计规范
- [ ] 版本时间轴清晰展示
- [ ] 版本对比功能正常
- [ ] 响应式布局正常

**依赖**: 任务3

---

### 任务7：实现上传去重交互
**优先级**: P0  
**文件**: `src/components/upload/FileUpload.vue` (修改), `src/stores/upload.ts` (修改)  
**当前状态**: 无去重提示  
**目标状态**: 智能去重提示和引导

**详细需求**:
1. 文件选择后自动计算哈希（使用 Web Crypto API）
2. 调用去重检测 API
3. 根据检测结果展示不同对话框：
   - **完全相同的文件**：
     ```
     该文件已存在
     文档: GJZ-QP-01 记录控制程序
     当前版本: V2.1 (生效中)
     [查看现有版本] [作为新版本上传] [取消]
     ```
   - **同名不同内容**：
     ```
     检测到同名文档
     现有版本: GJZ-QP-01 记录控制程序 V2.1
     是否创建为新版本 V2.2？
     [创建新版本] [重命名上传] [取消]
     ```
4. 上传表单增强：
   - 如果是新版本，显示上一版本的变更历史
   - 必填项：变更摘要、变更详细说明
   - 选填项：生效日期、版本标签
   - 自动填充：版本号（上一版本+1）

**验收标准**:
- [ ] 文件哈希计算正确
- [ ] 去重提示准确
- [ ] 用户操作流程顺畅
- [ ] 表单验证完整

**依赖**: 任务4

---

## 任务组5：审批与培训（P1）

### 任务8：实现审批工作流界面
**优先级**: P1  
**文件**: `src/views/documents/DocumentReview.vue` (新建)  
**当前状态**: 无审批功能  
**目标状态**: 完整的文档审批工作流

**详细需求**:
1. 待审批列表：
   - 显示所有待审批的文档版本
   - 显示提交人、提交时间、变更摘要
   - 支持筛选、排序
2. 审批详情页：
   - 显示文档完整信息
   - 显示与上一版本的对比
   - 显示变更说明
   - 审批操作：[通过] [拒绝]
   - 必须填写审批意见
3. 审批历史：
   - 显示所有已审批的记录
   - 支持按时间、文档、审批人筛选
4. 我的提交：
   - 显示我提交的所有版本
   - 显示审批状态
   - 草稿状态可编辑

**验收标准**:
- [ ] 审批流程完整
- [ ] 权限控制正确（只有特定角色可审批）
- [ ] 审批意见记录完整
- [ ] 审批后状态更新正确

**依赖**: 任务6

---

### 任务9：实现文档培训/分发功能
**优先级**: P1  
**文件**: `api/routes/documents.py` (新增), `core/document_distribution.py` (新建)  
**当前状态**: 无培训管理功能  
**目标状态**: 新版本发布后自动触发培训流程

**详细需求**:
1. 当文档版本变为 effective 时，自动创建培训任务
2. 根据文档类型确定需要培训的人员
3. API: GET /api/v1/documents/versions/{version_id}/distribution
   - 获取分发/培训状态
4. API: POST /api/v1/documents/distribution/{id}/acknowledge
   - 用户确认已阅读/培训完成
5. 前端：
   - 我的培训任务列表
   - 文档阅读确认界面
   - 培训完成统计

**验收标准**:
- [ ] 新版本生效后自动创建培训任务
- [ ] 用户能查看自己的培训任务
- [ ] 确认阅读后状态更新
- [ ] 统计报表正确

**依赖**: 任务3

---

## 任务组6：复审与问答增强（P1）

### 任务10：实现文档复审提醒功能
**优先级**: P1  
**文件**: `core/scheduler.py` (新建)  
**当前状态**: 无定时任务  
**目标状态**: 自动提醒即将到期的文档复审

**详细需求**:
1. 使用 APScheduler 实现定时任务
2. 每天检查 review_date 即将到期的文档（提前30天、7天、1天）
3. 发送通知（先实现日志记录，后续集成邮件/消息推送）
4. API: GET /api/v1/documents/pending-review
   - 获取即将需要复审的文档列表
5. 前端：
   - 仪表盘显示待复审文档数量
   - 待复审文档列表
   - [发起复审] 按钮，创建新版本

**验收标准**:
- [ ] 定时任务正常运行
- [ ] 到期提醒准确
- [ ] 复审流程正常

**依赖**: 任务3

---

### 任务11：增强问答界面（版本信息展示）
**优先级**: P1  
**文件**: `src/views/chat/ChatView.vue` (修改)  
**当前状态**: 答案不显示版本信息  
**目标状态**: 明确标注答案来源版本

**详细需求**:
1. 答案卡片增强：
   - 显示引用的文档版本号（如 V2.1）
   - 显示版本状态（生效中/已作废）
   - 如果是历史版本，显示警告提示
2. 来源文档列表：
   - 显示文档版本标签
   - 点击可查看该版本详情
3. 版本对比快捷入口：
   - 如果用户询问"新旧版本区别"，展示对比按钮
   - 点击打开版本对比弹窗
4. 历史版本追溯：
   - 支持用户指定日期查询
   - 界面提供日期选择器

**验收标准**:
- [ ] 答案中显示版本信息
- [ ] 作废版本有明显提示
- [ ] 版本对比入口可用
- [ ] 日期追溯功能正常

**依赖**: 任务5, 任务6

---

## 任务组7：测试与文档（P1）

### 任务12：编写版本管理单元测试
**优先级**: P1  
**文件**: `tests/unit/test_document_version_store.py`, `tests/unit/test_document_versions_api.py`  
**详细需求**:
1. 测试 DocumentVersionStore 所有方法
2. 测试状态流转验证
3. 测试版本对比逻辑
4. 测试去重检测逻辑
5. 覆盖率 > 80%

**验收标准**:
- [ ] 所有测试通过
- [ ] 覆盖率达标

---

### 任务13：编写版本管理集成测试
**优先级**: P1  
**文件**: `tests/integration/test_version_management.py`  
**详细需求**:
1. 测试完整的上传→审批→生效→作废流程
2. 测试多版本并行场景
3. 测试问答时版本过滤
4. 测试权限控制

**验收标准**:
- [ ] 集成测试通过
- [ ] 端到端流程正常

---

## 任务依赖关系

```
任务1 (数据库表结构)
    ↓
任务2 (数据访问层)
    ↓
    ├── 任务3 (版本管理API)
    │       ↓
    │       ├── 任务6 (版本管理界面)
    │       │       ↓
    │       │       └── 任务8 (审批界面)
    │       │
    │       ├── 任务9 (培训功能)
    │       ├── 任务10 (复审提醒)
    │       └── 任务5 (RAG服务)
    │               ↓
    │               └── 任务11 (问答增强)
    │
    └── 任务4 (去重API)
            ↓
            └── 任务7 (上传去重交互)
```

---

## 输出要求

完成每个任务组后汇报：
1. 完成状态
2. 修改的文件列表
3. 测试情况
4. 遇到的问题
