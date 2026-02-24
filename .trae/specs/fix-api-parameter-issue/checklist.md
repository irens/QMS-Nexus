# 修复 API 参数混合问题验收清单

## 任务1：修改请求模型

- [ ] `ApproveRequest` 类添加了 `current_user` 字段
- [ ] `RejectRequest` 类添加了 `current_user` 字段
- [ ] `ObsoleteRequest` 类添加了 `current_user` 字段
- [ ] `SubmitRequest` 类添加了 `current_user` 字段（如存在）
- [ ] 所有字段都有正确的类型注解和描述

## 任务2：修改 API 函数签名

- [ ] `approve_version` 函数移除了 `current_user: str = Form(...)` 参数
- [ ] `reject_version` 函数移除了 `current_user: str = Form(...)` 参数
- [ ] `obsolete_version` 函数移除了 `current_user: str = Form(...)` 参数
- [ ] `submit_version` 函数移除了 `current_user: str = Form(...)` 参数
- [ ] 所有函数从 `request.current_user` 获取当前用户
- [ ] 函数内部逻辑正常工作

## 任务3：更新单元测试

- [ ] `TestApproveVersion` 类使用 `json={...}` 发送请求
- [ ] `TestRejectVersion` 类使用 `json={...}` 发送请求
- [ ] `TestObsoleteVersion` 类使用 `json={...}` 发送请求
- [ ] `TestSubmitVersion` 类使用 `json={...}` 发送请求
- [ ] 所有请求都包含 `current_user` 字段
- [ ] 测试断言正确

## 任务4：运行测试验证

- [ ] 所有单元测试通过
- [ ] 没有 422 错误
- [ ] 审批相关 API 正常工作
- [ ] 测试覆盖率未下降

## 回归测试

- [ ] 创建版本 API 正常工作
- [ ] 获取版本列表 API 正常工作
- [ ] 获取版本详情 API 正常工作
- [ ] 版本对比 API 正常工作
- [ ] 去重检测 API 正常工作
