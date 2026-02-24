# 弃用警告修复任务列表

## 阶段 1：datetime.utcnow() 修复（中优先级）

### 1.1 核心模块修复
- [ ] 修复 `core/document_version_store.py` 中的 `datetime.utcnow()` 调用
- [ ] 修复 `core/document_store.py` 中的 `datetime.utcnow()` 调用
- [ ] 修复 `core/feedback_store.py` 中的 `datetime.utcnow()` 调用

### 1.2 API 路由修复
- [ ] 修复 `api/routes/document_versions.py` 中的 `datetime.utcnow()` 调用
- [ ] 修复 `api/routes/documents.py` 中的 `datetime.utcnow()` 调用

### 1.3 测试文件修复
- [ ] 修复 `tests/unit/test_document_versions_api.py` 中的 `datetime.utcnow()` 调用
- [ ] 修复 `tests/unit/test_document_version_store.py` 中的 `datetime.utcnow()` 调用
- [ ] 修复 `tests/integration/test_version_management.py` 中的 `datetime.utcnow()` 调用

### 1.4 脚本文件修复
- [ ] 修复 `scripts/migrate_v1_0_0_to_v1_1_0.py` 中的 `datetime.utcnow()` 调用

## 阶段 2：Pydantic V2 配置修复（低优先级）

- [ ] 修复 `core/config.py` 中的 `class Config` 为 `model_config = ConfigDict(...)`

## 阶段 3：FastAPI lifespan 修复（低优先级）

- [ ] 将 `api/main.py` 中的 `@app.on_event("startup")` 改为 lifespan 事件处理器

## 阶段 4：验证与测试

- [ ] 运行完整测试套件验证修复
- [ ] 确认所有弃用警告已消除
- [ ] 验证功能正常

## 任务统计

| 阶段 | 任务数 | 优先级 |
|------|--------|--------|
| 阶段 1 | 9 | 中 |
| 阶段 2 | 1 | 低 |
| 阶段 3 | 1 | 低 |
| 阶段 4 | 3 | 高 |
| **总计** | **14** | |
