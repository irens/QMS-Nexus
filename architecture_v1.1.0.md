# QMS-Nexus v1.1.0 系统架构设计文档

## 版本信息
- **版本**: v1.1.0
- **主题**: 医疗器械文档版本管理系统
- **创建日期**: 2026-02-24
- **状态**: 设计中
- **上一版本**: [architecture.md v1.0.0](./architecture.md)

---

## 1. 版本概述

### 1.1 变更摘要

v1.1.0 版本在 v1.0.0 基础上增加了**完整的文档版本管理系统**，满足医疗器械行业对文档控制的严格要求。

### 1.2 核心新增功能

| 功能模块 | 说明 | 合规依据 |
|---------|------|---------|
| 文档版本控制 | 完整的版本生命周期管理（起草→审核→批准→生效→作废） | ISO 13485:2016 4.2.3 |
| 文件去重检测 | 基于内容哈希的智能去重，防止重复存储 | 数据完整性 |
| 审批工作流 | 多级审批、审批历史记录、电子签名 | FDA 21 CFR Part 11 |
| 版本追溯 | 支持历史版本查询、版本对比 | ISO 13485:2016 4.2.4 |
| 培训管理 | 新版本发布后自动触发培训确认 | GMP 要求 |
| 复审提醒 | 自动提醒即将到期的文档复审 | 持续改进 |

### 1.3 与 v1.0.0 的主要差异

```
v1.0.0                          v1.1.0
─────────────────────────────────────────────────────────
documents 表（单层）      →     documents + document_versions（版本化）
无版本概念                →     完整版本生命周期管理
上传即生效                →     上传→审批→生效流程
问答搜索所有文档          →     默认只搜索最新生效版本
无去重机制                →     智能去重检测
无审批流程                →     多级审批工作流
```

---

## 2. 数据模型变更

### 2.1 文档版本表 (document_versions)

**新增表**，替代原 documents 表作为文档版本存储。

```sql
CREATE TABLE document_versions (
    -- 主键
    id TEXT PRIMARY KEY,                    -- 版本唯一ID
    
    -- 文档组标识
    document_id TEXT NOT NULL,              -- 文档组ID（同一文件的不同版本共享）
    
    -- 版本信息
    version_number INTEGER NOT NULL,        -- 版本号：1, 2, 3...
    version_label TEXT,                     -- 版本标签：V1.0, V1.1, V2.0
    
    -- 文件信息
    filename TEXT NOT NULL,                 -- 文件名
    file_hash TEXT NOT NULL,                -- SHA256 哈希，用于去重
    file_size INTEGER,                      -- 文件大小（字节）
    file_type TEXT,                         -- 文件类型
    
    -- 版本状态（核心）
    status TEXT NOT NULL DEFAULT 'draft',   -- draft/review/approved/effective/obsolete/archived
    
    -- 内容元数据
    title TEXT,                             -- 文档标题
    description TEXT,                       -- 文档描述
    doc_type TEXT,                          -- 质量手册/程序文件/作业指导书/记录表单
    doc_code TEXT,                          -- 文档编号：如 GJZ-QP-01
    
    -- 变更记录
    change_summary TEXT,                    -- 变更摘要（必填）
    change_details TEXT,                    -- 变更详细说明
    previous_version_id TEXT,               -- 上一版本ID（外键）
    
    -- 时间控制
    effective_date TIMESTAMP,               -- 生效日期
    review_date TIMESTAMP,                  -- 复审日期
    
    -- 标识位
    is_latest BOOLEAN DEFAULT FALSE,        -- 是否最新版本
    
    -- 审批信息（电子签名）
    prepared_by TEXT,                       -- 编制人
    reviewed_by TEXT,                       -- 审核人
    approved_by TEXT,                       -- 批准人
    approved_date TIMESTAMP,                -- 批准日期
    
    -- 知识库关联
    kb_id TEXT DEFAULT 'default',
    
    -- 审计字段
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    UNIQUE(document_id, version_number),
    FOREIGN KEY (previous_version_id) REFERENCES document_versions(id),
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
);

-- 索引
CREATE INDEX idx_doc_ver_status ON document_versions(status);
CREATE INDEX idx_doc_ver_effective_date ON document_versions(effective_date);
CREATE INDEX idx_doc_ver_kb_latest ON document_versions(kb_id, is_latest);
CREATE INDEX idx_doc_ver_file_hash ON document_versions(file_hash);
```

### 2.2 文档审批历史表 (document_approval_history)

**新增表**，记录所有审批操作，满足审计要求。

```sql
CREATE TABLE document_approval_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_version_id TEXT NOT NULL,      -- 版本ID
    action TEXT NOT NULL,                   -- submit/review/approve/reject/publish/obsolete
    action_by TEXT NOT NULL,                -- 操作人
    action_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comment TEXT,                           -- 审批意见
    from_status TEXT,                       -- 原状态
    to_status TEXT,                         -- 新状态
    FOREIGN KEY (document_version_id) REFERENCES document_versions(id)
);

CREATE INDEX idx_approval_history_version ON document_approval_history(document_version_id);
CREATE INDEX idx_approval_history_action_at ON document_approval_history(action_at);
```

### 2.3 文档分发/培训记录表 (document_distribution)

**新增表**，管理新版本的培训确认。

```sql
CREATE TABLE document_distribution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_version_id TEXT NOT NULL,      -- 版本ID
    user_id TEXT NOT NULL,                  -- 用户ID
    distribution_type TEXT DEFAULT 'read',  -- read/training/acknowledge
    status TEXT DEFAULT 'pending',          -- pending/completed
    distributed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,                 -- 完成时间
    FOREIGN KEY (document_version_id) REFERENCES document_versions(id)
);

CREATE INDEX idx_distribution_version ON document_distribution(document_version_id);
CREATE INDEX idx_distribution_user ON document_distribution(user_id);
```

### 2.4 向量库元数据扩展

ChromaDB 文档结构增加版本信息：

```json
{
  "id": "chunk_uuid",
  "text": "文本内容",
  "metadata": {
    "filename": "GJZ-QP-01.docx",
    "file_type": "docx",
    "page": 1,
    "doc_id": "文档组ID",
    "version_id": "版本ID",           // 新增
    "version_number": 2,              // 新增
    "version_label": "V2.1",          // 新增
    "status": "effective",            // 新增
    "effective_date": "2024-01-15",   // 新增
    "is_latest": true,                // 新增
    "kb_id": "知识库ID"
  }
}
```

---

## 3. API 设计变更

### 3.1 新增接口

#### 文档版本管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/documents/{id}/versions` | POST | 上传新版本 |
| `/documents/{id}/versions` | GET | 获取版本历史 |
| `/documents/versions/{version_id}` | GET | 版本详情 |
| `/documents/versions/{version_id}/approve` | POST | 审批通过 |
| `/documents/versions/{version_id}/reject` | POST | 审批拒绝 |
| `/documents/versions/{version_id}/obsolete` | POST | 作废版本 |
| `/documents/versions/{v1_id}/compare/{v2_id}` | GET | 版本对比 |
| `/documents/versions/{version_id}/download` | GET | 下载版本 |

#### 去重检测

| 接口 | 方法 | 说明 |
|------|------|------|
| `/upload/check-duplicate` | POST | 上传前检查重复 |

#### 培训管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/documents/versions/{version_id}/distribution` | GET | 获取分发状态 |
| `/documents/distribution/{id}/acknowledge` | POST | 确认阅读 |

#### 复审提醒

| 接口 | 方法 | 说明 |
|------|------|------|
| `/documents/pending-review` | GET | 待复审文档 |

### 3.2 修改接口

#### 问答接口增强

```python
class AskRequest(BaseModel):
    question: str
    kb_id: str = "default"
    version_strategy: str = "latest_effective"  # 新增
    specific_date: Optional[datetime] = None    # 新增
    include_version_info: bool = True           # 新增
```

---

## 4. 核心服务变更

### 4.1 新增服务

#### DocumentVersionStore

```python
class DocumentVersionStore:
    """文档版本数据访问层"""
    
    async def create_version(self, ...) -> DocumentVersion:
        """创建新版本，自动递增版本号"""
        
    async def approve_version(self, version_id: str, approver: str) -> bool:
        """审批通过，自动处理版本状态流转"""
        
    async def compare_versions(self, v1_id: str, v2_id: str) -> VersionDiff:
        """对比两个版本差异"""
        
    async def get_effective_version_at_date(
        self, 
        document_id: str, 
        date: datetime
    ) -> Optional[DocumentVersion]:
        """获取指定日期生效的版本"""
```

#### DocumentDistributionService

```python
class DocumentDistributionService:
    """文档分发/培训管理服务"""
    
    async def create_distribution_tasks(self, version_id: str):
        """版本生效时自动创建培训任务"""
        
    async def acknowledge(self, distribution_id: str, user_id: str):
        """用户确认阅读"""
```

### 4.2 修改服务

#### RAGService（增强）

```python
class RAGService:
    async def search(
        self, 
        query: str,
        version_strategy: str = "latest_effective",  # 新增
        specific_date: Optional[datetime] = None,    # 新增
        ...
    ) -> List[SearchResult]:
        """
        搜索策略：
        - latest_effective: 只搜索最新生效版本（默认）
        - specific_date: 搜索指定日期生效的版本
        - all_versions: 搜索所有版本（用于对比）
        """
```

---

## 5. 前端架构变更

### 5.1 新增页面

| 页面 | 路径 | 说明 |
|------|------|------|
| 版本历史 | `/documents/:id/versions` | 时间轴展示所有版本 |
| 版本详情 | `/documents/versions/:versionId` | 版本元数据、审批历史 |
| 版本对比 | `/documents/compare` | 左右对比两个版本 |
| 审批中心 | `/documents/review` | 待审批列表、审批操作 |
| 培训任务 | `/training` | 我的培训任务列表 |

### 5.2 组件增强

#### 上传组件

```typescript
// 新增功能
interface UploadEnhancement {
  calculateFileHash(file: File): Promise<string>  // 计算文件哈希
  checkDuplicate(hash: string): Promise<DuplicateCheckResult>
  showDuplicateDialog(result: DuplicateCheckResult): void
}
```

#### 问答组件

```typescript
// 新增功能
interface AnswerEnhancement {
  showVersionInfo: boolean      // 显示版本信息
  showObsoleteWarning: boolean  // 作废版本警告
  enableVersionCompare: boolean // 版本对比入口
}
```

---

## 6. 业务流程

### 6.1 文档版本生命周期

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  draft  │───→│ review  │───→│ approved│───→│effective│───→│obsolete │
│  (草稿)  │    │ (审核中) │    │ (已批准) │    │ (生效中) │    │ (已作废) │
└────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    └─────────┘
     │              │              │              │
     │              │ reject       │              │
     │              └──────────────┘              │
     │                                            │
     └────────────────────────────────────────────┘
                    (重新编辑后提交)
```

### 6.2 上传流程

```
用户选择文件
    ↓
计算文件 SHA256 哈希
    ↓
调用 /upload/check-duplicate
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   exact_match   │   name_match    │    new_file     │
│   (完全相同的文件) │   (同名不同内容)   │    (新文件)      │
└────────┬────────┴────────┬────────┴────────┬────────┘
         ↓                 ↓                 ↓
   提示"文件已存在"    提示"创建新版本？"     正常上传
   [查看] [新版本]     [是] [重命名]       填写元数据
   [取消]              [取消]
```

### 6.3 审批流程

```
编制人提交版本
    ↓
状态: draft → review
    ↓
审核人审批
    ↓
┌─────────────────┬─────────────────┐
│     通过         │      拒绝        │
│  review→approved │   review→draft  │
└────────┬────────┴────────┬────────┘
         ↓                 ↓
    批准人批准          编制人修改
         ↓                 ↓
  approved→effective      重新提交
         ↓
    上一版本 obsolete
         ↓
    创建培训任务
```

---

## 7. 合规性设计

### 7.1 ISO 13485:2016 对应条款

| 条款 | 要求 | 系统实现 |
|------|------|---------|
| 4.2.3 医疗器械文档 | 文档控制 | 版本管理、审批流程 |
| 4.2.4 文档控制 | 审批、分发、变更 | 审批工作流、培训确认、版本对比 |
| 7.3.7 设计和开发变更 | 变更控制 | 变更摘要、变更详情、历史追溯 |

### 7.2 FDA 21 CFR Part 11 对应条款

| 条款 | 要求 | 系统实现 |
|------|------|---------|
| 11.10(a) | 系统验证 | 审计追踪、审批历史 |
| 11.10(k) | 电子签名 | 审批人身份记录、时间戳 |
| 11.30 | 签名/记录关联 | 审批记录与版本绑定 |

---

## 8. 部署架构

与 v1.0.0 保持一致，新增定时任务服务：

```
┌─────────────────────────────────────────┐
│           定时任务服务 (Scheduler)        │
│  ┌─────────────────────────────────────┐ │
│  │  APScheduler                        │ │
│  │  - 文档复审提醒（每天）              │ │
│  │  - 自动生效检查（每小时）            │ │
│  │  - 备份任务（每天凌晨）              │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 9. 测试策略

### 9.1 版本管理测试

| 测试类型 | 测试内容 |
|---------|---------|
| 状态流转 | 验证所有合法和非法状态转换 |
| 并发控制 | 多用户同时操作同一版本 |
| 数据一致性 | 版本状态与向量库元数据同步 |
| 审批流程 | 多级审批、权限控制 |

### 9.2 去重检测测试

| 测试场景 | 预期结果 |
|---------|---------|
| 完全相同文件 | 识别为 exact_match |
| 同名不同内容 | 识别为 name_match |
| 不同名相同内容 | 识别为 exact_match |
| 新文件 | 识别为 new_file |

---

## 10. 迁移指南

### 10.1 从 v1.0.0 迁移到 v1.1.0

```python
# 1. 备份现有数据
# 2. 执行数据库迁移脚本
# 3. 将现有文档标记为 V1.0
# 4. 更新向量库元数据
# 5. 验证数据完整性
```

### 10.2 数据迁移脚本

```python
async def migrate_from_v1_0_0():
    """从 v1.0.0 迁移数据"""
    # 1. 创建新表
    # 2. 迁移 documents 数据到 document_versions
    # 3. 设置 version_number=1, version_label="V1.0"
    # 4. 设置 status="effective", is_latest=true
    # 5. 更新向量库 metadata
```

---

## 11. 附录

### 11.1 版本状态定义

| 状态 | 说明 | 可转换到 |
|------|------|---------|
| draft | 草稿，编制中 | review |
| review | 审核中 | approved, draft |
| approved | 已批准，待生效 | effective |
| effective | 生效中 | obsolete |
| obsolete | 已作废 | - |
| archived | 已归档 | - |

### 11.2 文件哈希算法

```python
# SHA-256 哈希计算
import hashlib

def calculate_file_hash(file_content: bytes) -> str:
    return hashlib.sha256(file_content).hexdigest()
```

---

## 参考文档

- [architecture.md v1.0.0](./architecture.md) - 基础架构设计
- [todo_v1.1.0.md](./todo_v1.1.0.md) - v1.1.0 任务清单
- ISO 13485:2016 - 医疗器械质量管理体系要求
- FDA 21 CFR Part 11 - 电子记录和电子签名
