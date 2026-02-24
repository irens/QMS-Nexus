# 修复 API 参数混合问题任务清单

## 任务1：修改请求模型

**文件**: `api/routes/document_versions.py`

**详细需求**:
1. 修改 `ApproveRequest` 类，添加 `current_user` 字段
2. 修改 `RejectRequest` 类，添加 `current_user` 字段
3. 修改 `ObsoleteRequest` 类，添加 `current_user` 字段
4. 修改 `SubmitRequest` 类（如存在），添加 `current_user` 字段

**修改示例**:
```python
# ApproveRequest
class ApproveRequest(BaseModel):
    """审批通过请求"""
    comment: Optional[str] = Field(None, description="审批意见")
    current_user: str = Field(..., description="当前用户")

# RejectRequest
class RejectRequest(BaseModel):
    """审批拒绝请求"""
    comment: str = Field(..., description="拒绝原因（必填）")
    current_user: str = Field(..., description="当前用户")

# ObsoleteRequest
class ObsoleteRequest(BaseModel):
    """作废版本请求"""
    reason: Optional[str] = Field(None, description="作废原因")
    current_user: str = Field(..., description="当前用户")
```

---

## 任务2：修改 API 函数签名

**文件**: `api/routes/document_versions.py`

**详细需求**:
1. 修改 `approve_version` 函数，移除 `current_user: str = Form(...)` 参数
2. 修改 `reject_version` 函数，移除 `current_user: str = Form(...)` 参数
3. 修改 `obsolete_version` 函数，移除 `current_user: str = Form(...)` 参数
4. 修改 `submit_version` 函数，移除 `current_user: str = Form(...)` 参数

**修改示例**:
```python
# 修改前
@router.post("/versions/{version_id}/approve", response_model=StandardResponse)
async def approve_version(
    version_id: str,
    request: ApproveRequest,
    current_user: str = Form("system", description="当前用户"),
):
    ...

# 修改后
@router.post("/versions/{version_id}/approve", response_model=StandardResponse)
async def approve_version(
    version_id: str,
    request: ApproveRequest,
):
    current_user = request.current_user
    ...
```

---

## 任务3：更新单元测试

**文件**: `tests/unit/test_document_versions_api.py`

**详细需求**:
1. 修改 `TestApproveVersion` 类中的测试，使用 `json={...}` 代替 `data={...}`
2. 修改 `TestRejectVersion` 类中的测试，使用 `json={...}` 代替 `data={...}`
3. 修改 `TestObsoleteVersion` 类中的测试，使用 `json={...}` 代替 `data={...}`
4. 修改 `TestSubmitVersion` 类中的测试，使用 `json={...}` 代替 `data={...}`
5. 确保所有请求都包含 `current_user` 字段

**修改示例**:
```python
# 修改前
response = client.post(
    "/api/v1/documents/versions/ver-123456/approve",
    data={"comment": "批准发布", "current_user": "admin"},
)

# 修改后
response = client.post(
    "/api/v1/documents/versions/ver-123456/approve",
    json={"comment": "批准发布", "current_user": "admin"},
)
```

---

## 任务4：运行测试验证

**命令**:
```bash
cd qms-nexus
python -m pytest tests/unit/test_document_versions_api.py -v
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 没有 422 错误
- [ ] 审批相关 API 正常工作

---

## 任务依赖关系

```
任务1 (修改请求模型)
    ↓
任务2 (修改API函数签名)
    ↓
任务3 (更新单元测试)
    ↓
任务4 (运行测试验证)
```
