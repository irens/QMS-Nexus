# 修复 API 参数混合问题 Spec

## Why
单元测试发现 API 路由中混合使用了 JSON body 和 Form 参数（如 `request: ApproveRequest` 和 `current_user: str = Form(...)`），这在 FastAPI 中会导致 422 错误。需要统一参数传递方式。

## What Changes
- **修改** `api/routes/document_versions.py` 中的审批相关 API
- **修改** `api/routes/upload.py` 中的上传相关 API（如需要）
- 将混合参数改为统一使用 JSON body 或统一使用 Form 参数

## Impact
- 受影响 API：
  - POST /api/v1/documents/versions/{version_id}/approve
  - POST /api/v1/documents/versions/{version_id}/reject
  - POST /api/v1/documents/versions/{version_id}/obsolete
  - POST /api/v1/documents/versions/{version_id}/submit
- 受影响测试：`tests/unit/test_document_versions_api.py`

## ADDED Requirements
无新增功能

## MODIFIED Requirements

### Requirement: 统一 API 参数传递方式
**原实现**: 混合使用 JSON body (`request: ApproveRequest`) 和 Form 参数 (`current_user: str = Form(...)`)
**修改后**: 统一使用 JSON body，将 `current_user` 放入请求体中

#### Scenario: 审批通过 API
- **GIVEN** API 接收审批请求
- **WHEN** 请求体包含 `comment` 和 `current_user`
- **THEN** 正常处理请求，不再返回 422 错误

#### Scenario: 审批拒绝 API
- **GIVEN** API 接收拒绝请求
- **WHEN** 请求体包含 `comment` 和 `current_user`
- **THEN** 正常处理请求，不再返回 422 错误

#### Scenario: 作废版本 API
- **GIVEN** API 接收作废请求
- **WHEN** 请求体包含 `reason` 和 `current_user`
- **THEN** 正常处理请求，不再返回 422 错误

#### Scenario: 提交审核 API
- **GIVEN** API 接收提交审核请求
- **WHEN** 请求体包含 `comment` 和 `current_user`
- **THEN** 正常处理请求，不再返回 422 错误

## REMOVED Requirements
无

## 具体修改方案

### 1. 修改请求模型

```python
# 修改前
class ApproveRequest(BaseModel):
    """审批通过请求"""
    comment: Optional[str] = Field(None, description="审批意见")

# 修改后
class ApproveRequest(BaseModel):
    """审批通过请求"""
    comment: Optional[str] = Field(None, description="审批意见")
    current_user: str = Field(..., description="当前用户")
```

### 2. 修改 API 函数签名

```python
# 修改前
@router.post("/versions/{version_id}/approve", response_model=StandardResponse)
async def approve_version(
    version_id: str,
    request: ApproveRequest,
    current_user: str = Form("system", description="当前用户"),
):

# 修改后
@router.post("/versions/{version_id}/approve", response_model=StandardResponse)
async def approve_version(
    version_id: str,
    request: ApproveRequest,
):
    current_user = request.current_user
```

### 3. 需要修改的 API 列表

1. `approve_version` - 审批通过
2. `reject_version` - 审批拒绝
3. `obsolete_version` - 作废版本
4. `submit_version` - 提交审核

### 4. 对应的测试修改

测试文件中需要将 `data={...}` 改为 `json={...}`，并包含 `current_user` 字段。
