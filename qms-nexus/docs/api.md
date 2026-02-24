# QMS-Nexus API 文档

> **版本**: v1.1.0  
> **更新日期**: 2026-02-24  
> **文档状态**: 已集成文档版本管理功能

## 在线文档
启动后访问：http://localhost:8000/docs

> **提示**：本文档提供静态参考，最新的 API 文档请访问在线 Swagger UI：http://localhost:8000/docs

## 版本说明

### v1.1.0 主要更新
- ✅ 完整的文档版本生命周期管理（起草→审核→批准→生效→作废）
- ✅ 文件去重检测（基于SHA256哈希）
- ✅ 审批历史记录（满足医疗器械行业合规要求）
- ✅ 版本对比功能
- ✅ RAG服务版本管理（默认只搜索最新生效版本）
- ✅ 版本对比搜索（智能分析版本差异）

## 接口清单

### 1. 健康检查
```http
GET /health
```
响应：
```json
{"status": "ok"}
```

---

## 文件上传接口

### 2.1 标准文件上传
```http
POST /api/v1/upload
Content-Type: multipart/form-data
```
参数：
- `file`：≤50 MB，支持 PDF/Word/Excel/PPT
- `collection`：目标知识库名称（默认 qms_docs）
- `skip_duplicate_check`：是否跳过去重检测（默认 false）
- `force_upload`：强制上传（忽略重复检测，默认 false）

响应：
```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "task_id": "uuid",
    "status": "Pending",
    "collection": "qms_docs",
    "file_hash": "sha256_hash"
  }
}
```
错误码：
- 400：不支持的文件类型
- 409：文件已存在（检测到重复）
- 413：文件过大

### 2.2 去重检测
```http
POST /api/v1/upload/check-duplicate
Content-Type: application/json
```
请求体：
```json
{
  "file_hash": "sha256_hash_string",
  "filename": "GJZ-QP-01.docx",
  "kb_id": "default"
}
```

响应：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "type": "exact_match",
    "message": "该文件已存在，内容与现有版本完全相同",
    "existing_document": {
      "id": "doc_id",
      "title": "记录控制程序",
      "current_version": {
        "version_id": "ver_id",
        "version_number": 2,
        "version_label": "V2.1",
        "status": "effective"
      }
    },
    "existing_version": {
      "version_id": "ver_id",
      "version_number": 2,
      "version_label": "V2.1",
      "status": "effective",
      "file_hash": "sha256_hash",
      "created_at": "2024-01-15T10:00:00"
    },
    "suggestions": [
      {"action": "view", "label": "查看现有版本"},
      {"action": "upload_as_new_version", "label": "作为新版本上传"},
      {"action": "force_upload", "label": "强制重新上传"},
      {"action": "cancel", "label": "取消"}
    ]
  }
}
```

检测类型：
- `exact_match`：完全相同的文件（哈希相同）
- `name_match`：同名不同内容（文件名相同，哈希不同）
- `new_file`：新文件

### 2.3 文件去重检测（直接上传）
```http
POST /api/v1/upload/check-duplicate-file
Content-Type: multipart/form-data
```
参数：
- `file`：要检测的文件
- `kb_id`：知识库ID（默认 default）

响应格式与 `/check-duplicate` 相同

### 2.4 智能上传
```http
POST /api/v1/upload/smart
Content-Type: multipart/form-data
```
参数：
- `file`：上传的文件
- `collection`：目标知识库名称
- `document_id`：文档组ID（创建新版本时提供）
- `change_summary`：变更摘要
- `change_details`：变更详细说明
- `version_label`：版本标签
- `force_upload`：强制上传（忽略重复检测）

响应：
```json
{
  "code": 200,
  "message": "新版本创建成功",
  "data": {
    "task_id": "uuid",
    "status": "Completed",
    "version_id": "ver_uuid",
    "version_number": 2,
    "version_label": "V2.0",
    "status": "draft"
  }
}
```

### 2.5 任务状态查询
```http
GET /api/v1/upload/status/{task_id}
```
响应：
```json
{
  "task_id": "uuid",
  "status": "Completed",
  "collection": "qms_docs"
}
```

---

## 文档版本管理接口

### 3.1 创建新版本
```http
POST /api/v1/documents/{document_id}/versions
Content-Type: multipart/form-data
```
参数：
- `file`：版本文件（必填）
- `change_summary`：变更摘要（必填）
- `change_details`：变更详细说明
- `version_label`：版本标签（如 V2.1）
- `effective_date`：生效日期（ISO格式）
- `current_user`：当前用户

响应：
```json
{
  "code": 200,
  "message": "版本创建成功",
  "data": {
    "version_id": "ver_uuid",
    "version_number": 2,
    "version_label": "V2.0",
    "status": "draft",
    "file_hash": "sha256_hash"
  }
}
```

### 3.2 获取版本历史
```http
GET /api/v1/documents/{document_id}/versions
```
查询参数：
- `status`：按状态筛选
- `page`：页码（默认1）
- `page_size`：每页数量（默认20，最大100）
- `sort_by`：排序字段（version_number/created_at）
- `sort_order`：排序方向（asc/desc）

响应：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "ver_uuid",
        "document_id": "doc_uuid",
        "version_number": 2,
        "version_label": "V2.0",
        "filename": "doc.docx",
        "file_hash": "sha256_hash",
        "file_size": 10240,
        "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "status": "effective",
        "title": "文档标题",
        "change_summary": "修订内容",
        "change_details": "详细变更说明",
        "previous_version_id": "prev_ver_uuid",
        "effective_date": "2024-01-15T00:00:00",
        "review_date": "2025-01-15T00:00:00",
        "is_latest": true,
        "prepared_by": "user1",
        "reviewed_by": "user2",
        "approved_by": "user3",
        "approved_date": "2024-01-15T10:00:00",
        "kb_id": "default",
        "created_by": "user1",
        "created_at": "2024-01-10T09:00:00",
        "updated_at": "2024-01-15T10:00:00"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

### 3.3 获取版本详情
```http
GET /api/v1/documents/versions/{version_id}
```

响应：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "version": {
      "id": "ver_uuid",
      "document_id": "doc_uuid",
      "version_number": 2,
      "version_label": "V2.0",
      "filename": "doc.docx",
      "file_hash": "sha256_hash",
      "file_size": 10240,
      "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "status": "effective",
      "title": "文档标题",
      "change_summary": "修订内容",
      "change_details": "详细变更说明",
      "previous_version_id": "prev_ver_uuid",
      "effective_date": "2024-01-15T00:00:00",
      "review_date": "2025-01-15T00:00:00",
      "is_latest": true,
      "prepared_by": "user1",
      "reviewed_by": "user2",
      "approved_by": "user3",
      "approved_date": "2024-01-15T10:00:00",
      "kb_id": "default",
      "created_by": "user1",
      "created_at": "2024-01-10T09:00:00",
      "updated_at": "2024-01-15T10:00:00"
    },
    "approval_history": [
      {
        "id": 1,
        "action": "create",
        "action_by": "user1",
        "action_at": "2024-01-10T09:00:00",
        "comment": "创建版本 V2.0",
        "from_status": null,
        "to_status": "draft"
      },
      {
        "id": 2,
        "action": "submit",
        "action_by": "user1",
        "action_at": "2024-01-12T10:00:00",
        "comment": "提交审核",
        "from_status": "draft",
        "to_status": "review"
      },
      {
        "id": 3,
        "action": "publish",
        "action_by": "user3",
        "action_at": "2024-01-15T10:00:00",
        "comment": "审批通过",
        "from_status": "approved",
        "to_status": "effective"
      }
    ],
    "previous_version": null
  }
}
```

### 3.4 提交审核
```http
POST /api/v1/documents/versions/{version_id}/submit
Content-Type: multipart/form-data
```
参数：
- `comment`：提交说明
- `current_user`：当前用户

响应：
```json
{
  "code": 200,
  "message": "版本已提交审核",
  "data": {
    "version_id": "ver_uuid",
    "status": "review",
    "submitted_by": "user1",
    "submitted_at": "2024-01-12T10:00:00"
  }
}
```

### 3.5 审批通过
```http
POST /api/v1/documents/versions/{version_id}/approve
Content-Type: application/json
```
请求体：
```json
{
  "comment": "审批意见"
}
```

响应：
```json
{
  "code": 200,
  "message": "版本审批通过",
  "data": {
    "version_id": "ver_uuid",
    "status": "effective",
    "approved_by": "user3",
    "approved_at": "2024-01-15T10:00:00"
  }
}
```

### 3.6 审批拒绝
```http
POST /api/v1/documents/versions/{version_id}/reject
Content-Type: application/json
```
请求体：
```json
{
  "comment": "拒绝原因（必填）"
}
```

响应：
```json
{
  "code": 200,
  "message": "版本已退回草稿状态",
  "data": {
    "version_id": "ver_uuid",
    "status": "draft",
    "reject_reason": "拒绝原因",
    "rejected_by": "user2",
    "rejected_at": "2024-01-14T15:00:00"
  }
}
```

### 3.7 作废版本
```http
POST /api/v1/documents/versions/{version_id}/obsolete
Content-Type: application/json
```
请求体：
```json
{
  "reason": "作废原因"
}
```

响应：
```json
{
  "code": 200,
  "message": "版本已作废",
  "data": {
    "version_id": "ver_uuid",
    "status": "obsolete",
    "reason": "作废原因",
    "obsoleted_by": "user3",
    "obsoleted_at": "2024-01-20T10:00:00"
  }
}
```

### 3.8 版本对比
```http
GET /api/v1/documents/versions/{v1_id}/compare/{v2_id}
```

响应：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "v1_id": "ver_uuid_1",
    "v2_id": "ver_uuid_2",
    "v1_version_label": "V1.0",
    "v2_version_label": "V2.0",
    "added": [],
    "removed": [],
    "modified": [
      {
        "type": "file_size",
        "v1": 10240,
        "v2": 11264,
        "diff": 1024
      },
      {
        "type": "change_summary",
        "v1": "初始版本",
        "v2": "修订内容"
      }
    ],
    "statistics": {
      "added_count": 0,
      "removed_count": 0,
      "modified_count": 2
    },
    "change_summary": "从 V1.0 升级到 V2.0：修订内容"
  }
}
```

### 3.9 下载版本
```http
GET /api/v1/documents/versions/{version_id}/download
```

响应：文件流（Content-Disposition: attachment）

---

## 数据模型

### 文档版本 (DocumentVersion)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 版本唯一标识（UUID） |
| document_id | string | 文档组ID（同一文件的不同版本共享） |
| version_number | integer | 版本号（1, 2, 3...） |
| version_label | string | 版本标签（如 V1.0, V2.1） |
| filename | string | 文件名 |
| file_hash | string | SHA256哈希（用于去重） |
| file_size | integer | 文件大小（字节） |
| file_type | string | 文件MIME类型 |
| status | string | 版本状态 |
| title | string | 文档标题 |
| change_summary | string | 变更摘要 |
| change_details | string | 变更详细说明 |
| previous_version_id | string | 上一版本ID |
| effective_date | datetime | 生效日期 |
| review_date | datetime | 复审日期 |
| is_latest | boolean | 是否最新版本 |
| prepared_by | string | 编制人 |
| reviewed_by | string | 审核人 |
| approved_by | string | 批准人 |
| approved_date | datetime | 批准日期 |
| kb_id | string | 知识库ID |
| created_by | string | 创建人 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 审批历史 (ApprovalHistory)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 记录ID |
| document_version_id | string | 版本ID |
| action | string | 操作类型（create/submit/review/approve/reject/publish/obsolete） |
| action_by | string | 操作人 |
| action_at | datetime | 操作时间 |
| comment | string | 审批意见 |
| from_status | string | 原状态 |
| to_status | string | 新状态 |

## 版本状态流转

```
draft → review → approved → effective → obsolete
  ↑       |         |          |
  └───────┴─────────┴──────────┘ (reject 返回 draft)
```

状态说明：
- `draft`：草稿，编制中
- `review`：审核中
- `approved`：已批准，待生效
- `effective`：生效中
- `obsolete`：已作废

### 状态流转规则

| 当前状态 | 允许的目标状态 | 操作说明 |
|----------|----------------|----------|
| draft | review | 提交审核 |
| review | approved | 审核通过 |
| review | draft | 审核拒绝（退回修改） |
| approved | effective | 批准生效 |
| effective | obsolete | 作废版本 |

---

## 其他接口

### 4. 语义检索

#### 4.1 标准检索
```http
GET /api/v1/search?q=关键词&filter_tags=标签1,标签2&top_k=5
```
响应：
```json
[
  {
    "text": "...",
    "source": "文件名, 第1页",
    "tags": [],
    "score": 0.87
  }
]
```

#### 4.2 版本过滤检索（v1.1.0新增）
```http
GET /api/v1/search?q=关键词&version_strategy=latest_effective&top_k=5
```

查询参数：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | 是 | 搜索关键词 |
| filter_tags | string | 否 | 标签过滤，多个标签用逗号分隔 |
| top_k | integer | 否 | 返回结果数量，默认5 |
| version_strategy | string | 否 | 版本策略：latest_effective/specific_date/all_versions，默认 latest_effective |
| specific_date | datetime | 否 | 指定日期，用于 specific_date 策略 |

响应：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "text": "...",
      "score": 0.92,
      "source": "[来源：GJZ-QP-01 V2.1, 第3页]",
      "filename": "GJZ-QP-01.docx",
      "page": 3,
      "version_id": "ver_uuid",
      "version_number": 2,
      "version_label": "V2.1",
      "status": "effective",
      "effective_date": "2024-01-15T00:00:00",
      "is_latest": true,
      "warning": null
    }
  ]
}
```

**警告提示说明**：
- 当 `status` 为 `obsolete` 时，`warning` 返回 "该版本已作废，建议查看最新版本"
- 当 `is_latest` 为 `false` 时，`warning` 返回 "该文档已有新版本"

### 5. RAG 问答

#### 5.1 标准问答
```http
POST /api/v1/ask
Content-Type: application/json

{
  "question": "客户投诉如何处理？",
  "collection": "qms_docs",
  "skip_correction": false
}
```
响应：
```json
{
  "answer": "根据知识库...",
  "sources": ["文件名, 第1页"],
  "is_corrected": false,
  "correction_id": null
}
```

#### 5.2 版本管理问答（v1.1.0新增）
```http
POST /api/v1/ask
Content-Type: application/json

{
  "question": "客户投诉如何处理？",
  "collection": "qms_docs",
  "version_strategy": "latest_effective",
  "specific_date": "2024-01-15T00:00:00",
  "include_version_info": true
}
```

请求参数说明：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 问题内容 |
| collection | string | 否 | 知识库名称，默认 qms_docs |
| version_strategy | string | 否 | 版本策略：latest_effective/specific_date/all_versions，默认 latest_effective |
| specific_date | datetime | 否 | 指定日期，用于 specific_date 策略 |
| include_version_info | boolean | 否 | 是否包含版本信息，默认 true |

version_strategy 说明：
- `latest_effective`：只搜索最新生效版本（默认）
- `specific_date`：搜索指定日期生效的版本
- `all_versions`：搜索所有版本（用于对比）

响应：
```json
{
  "answer": "根据最新生效的文档版本...",
  "sources": ["GJZ-QP-01 V2.1, 第3页"],
  "is_corrected": false,
  "metadata": {
    "version_strategy": "latest_effective",
    "sources": [
      {
        "document_name": "GJZ-QP-01.docx",
        "version_id": "ver_uuid",
        "version_number": 2,
        "version_label": "V2.1",
        "status": "effective",
        "is_latest": true,
        "page": 3,
        "score": 0.92,
        "warning": null
      }
    ]
  }
}
```

#### 5.3 版本对比问答（v1.1.0新增）
```http
POST /api/v1/ask/compare-versions
Content-Type: application/json

{
  "document_id": "doc_uuid",
  "v1_id": "ver_uuid_v1",
  "v2_id": "ver_uuid_v2",
  "collection": "qms_docs"
}
```

用于回答"新旧版本有什么区别"这类问题。

响应：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "summary": "V2.0版本主要修订了客户投诉处理流程，增加了紧急投诉的响应时限要求...",
    "added_sections": [
      "新增紧急投诉处理流程",
      "新增投诉分类标准"
    ],
    "removed_sections": [
      "删除旧版纸质记录要求"
    ],
    "modified_sections": [
      "修改投诉响应时限：从48小时缩短至24小时",
      "修改责任人：由质量经理改为客服主管"
    ],
    "key_changes": [
      "响应时限缩短",
      "责任人调整",
      "新增分类标准"
    ],
    "v1_info": {
      "version_id": "ver_uuid_v1",
      "version_label": "V1.0",
      "version_number": 1,
      "status": "obsolete",
      "change_summary": "初始版本"
    },
    "v2_info": {
      "version_id": "ver_uuid_v2",
      "version_label": "V2.0",
      "version_number": 2,
      "status": "effective",
      "change_summary": "修订客户投诉处理流程"
    },
    "stats": {
      "v1_chunks": 15,
      "v2_chunks": 18
    }
  }
}
```

### 6. 动态标签 CRUD
```http
GET    /api/v1/tags
POST   /api/v1/tags
PUT    /api/v1/tags/{name}
DELETE /api/v1/tags/{name}
```

### 7. 系统统计
```http
GET /api/v1/stats
```
响应：
```json
{
  "totalDocuments": 42,
  "parsedDocuments": 38,
  "totalChats": 156,
  "activeUsers": 12,
  "totalUsers": 12,
  "totalApiKeys": 2,
  "systemUptime": "5小时",
  "memoryUsage": {
    "used": 8589934592,
    "total": 17179869184,
    "percentage": 50.0
  },
  "diskUsage": {
    "used": 107374182400,
    "total": 536870912000,
    "percentage": 20.0
  },
  "growthRate": {
    "documents": 15.5,
    "chats": 23.0
  }
}
```

字段说明：
| 字段 | 类型 | 说明 |
|------|------|------|
| totalDocuments | integer | 总文档数 |
| parsedDocuments | integer | 已解析文档数（状态为 Completed） |
| totalChats | integer | 问答次数 |
| activeUsers | integer | 活跃用户数 |
| totalUsers | integer | 总用户数 |
| totalApiKeys | integer | API Key 数量 |
| systemUptime | string | 系统运行时间 |
| memoryUsage | object | 内存使用情况 |
| diskUsage | object | 磁盘使用情况 |
| growthRate.documents | float | 文档增长率（较上月） |
| growthRate.chats | float | 问答增长率（较上月） |

### 8. 系统指标
```http
GET /metrics
```
Prometheus 格式，含上传/检索 QPS、延迟

---

## 调用示例

### curl 上传文件：
```bash
# 标准上传
curl -F "file=@sample.pdf" http://localhost:8000/api/v1/upload

# 去重检测
curl -X POST http://localhost:8000/api/v1/upload/check-duplicate \
  -H "Content-Type: application/json" \
  -d '{"file_hash":"abc123...","filename":"sample.pdf","kb_id":"default"}'

# 创建新版本
curl -F "file=@sample_v2.pdf" \
  -F "change_summary=修订内容" \
  -F "change_details=详细变更说明" \
  http://localhost:8000/api/v1/documents/{document_id}/versions

# 审批通过
curl -X POST http://localhost:8000/api/v1/documents/versions/{version_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"comment":"审批通过"}'
```

### Python 调用示例：
```python
import requests

# 去重检测
r = requests.post(
    "http://localhost:8000/api/v1/upload/check-duplicate",
    json={
        "file_hash": "sha256_hash",
        "filename": "doc.pdf",
        "kb_id": "default"
    }
)
print(r.json())

# 语义检索
r = requests.get(
    "http://localhost:8000/api/v1/search",
    params={"q": "质量风险"}
)
print(r.json())

# 语义检索 - 只搜索最新生效版本
r = requests.get(
    "http://localhost:8000/api/v1/search",
    params={
        "q": "客户投诉处理",
        "version_strategy": "latest_effective",
        "top_k": 5
    }
)
print(r.json())

# 语义检索 - 搜索指定日期生效的版本
r = requests.get(
    "http://localhost:8000/api/v1/search",
    params={
        "q": "客户投诉处理",
        "version_strategy": "specific_date",
        "specific_date": "2024-01-15T00:00:00"
    }
)
print(r.json())

# 获取版本历史
r = requests.get(
    f"http://localhost:8000/api/v1/documents/{document_id}/versions"
)
print(r.json())

# RAG问答 - 使用版本策略
r = requests.post(
    "http://localhost:8000/api/v1/ask",
    json={
        "question": "客户投诉如何处理？",
        "collection": "qms_docs",
        "version_strategy": "latest_effective",
        "include_version_info": True
    }
)
print(r.json())

# 版本对比搜索 - 对比两个版本的差异
r = requests.post(
    "http://localhost:8000/api/v1/ask/compare-versions",
    json={
        "document_id": "doc_uuid",
        "v1_id": "ver_uuid_v1",
        "v2_id": "ver_uuid_v2",
        "collection": "qms_docs"
    }
)
print(r.json())
```

---

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如文件重复） |
| 413 | 文件过大 |
| 500 | 服务器内部错误 |

---

## 更新日志

### v1.1.0 (2026-02-24)
- 新增文档版本管理API，支持完整的版本生命周期管理
  - 版本创建、查询、审批、作废
  - 版本历史追溯和对比
  - 审批历史记录（满足FDA 21 CFR Part 11合规要求）
- 新增文件去重检测API
  - 基于SHA256哈希的精确匹配
  - 文件名匹配检测
  - 智能上传建议
- 上传接口集成去重检测
- 支持版本状态流转：draft → review → approved → effective → obsolete
- RAG服务支持版本管理
  - 语义检索支持版本策略过滤（latest_effective/specific_date/all_versions）
  - 问答接口支持版本策略参数
  - 默认只搜索最新生效版本
  - 答案中标注引用文档的版本信息
  - 作废版本显示警告提示
- 新增版本对比搜索API
  - 支持对比两个版本的差异
  - 使用LLM智能分析新增/删除/修改内容
  - 用于回答"新旧版本有什么区别"类问题

### v1.0.0 (2026-02)
- 初始版本
- 文件上传和解析
- 语义检索和RAG问答
- 标签管理
- 系统监控
