# 文档版本管理系统 v1.1.0 验收清单

## 任务组1：数据库架构升级

### 任务1：创建文档版本管理表结构
- [ ] document_versions 表创建成功，包含所有字段
- [ ] document_approval_history 表创建成功
- [ ] document_distribution 表创建成功
- [ ] 唯一约束 (document_id, version_number) 生效
- [ ] 索引创建成功（status, effective_date, kb_id_is_latest, file_hash）
- [ ] 外键约束正确设置
- [ ] 数据迁移脚本执行成功，现有文档标记为 V1.0
- [ ] 数据库迁移后无数据丢失

### 任务2：实现文档版本数据访问层
- [ ] DocumentVersionStore 类创建成功
- [ ] create_version() 方法正常，自动递增版本号
- [ ] get_version_by_id() 方法正常
- [ ] get_versions_by_document() 方法正常
- [ ] get_latest_version() 方法正常
- [ ] get_effective_version_at_date() 方法正常
- [ ] update_version_status() 方法正常
- [ ] approve_version() 方法正常
- [ ] obsolete_version() 方法正常
- [ ] compare_versions() 方法正常
- [ ] 审批历史自动记录
- [ ] 状态流转验证正确（非法状态变更被拒绝）
- [ ] 事务回滚正常

---

## 任务组2：后端 API 开发

### 任务3：实现文档版本管理 API
- [ ] POST /api/v1/documents/{id}/versions 接口正常
- [ ] GET /api/v1/documents/{id}/versions 接口正常
- [ ] GET /api/v1/documents/versions/{version_id} 接口正常
- [ ] POST /api/v1/documents/versions/{version_id}/approve 接口正常
- [ ] POST /api/v1/documents/versions/{version_id}/reject 接口正常
- [ ] POST /api/v1/documents/versions/{version_id}/obsolete 接口正常
- [ ] GET /api/v1/documents/versions/{v1_id}/compare/{v2_id} 接口正常
- [ ] GET /api/v1/documents/versions/{version_id}/download 接口正常
- [ ] 状态流转正确（draft→review→approved→effective→obsolete）
- [ ] 权限控制生效
- [ ] 版本对比返回新增/删除/修改内容

### 任务4：实现文件去重检测 API
- [ ] POST /api/v1/upload/check-duplicate 接口正常
- [ ] 能正确识别 exact_match（哈希相同）
- [ ] 能正确识别 name_match（文件名相同，哈希不同）
- [ ] 能正确识别 new_file（新文件）
- [ ] 响应包含处理建议
- [ ] 去重检测日志记录正常

---

## 任务组3：RAG 服务升级

### 任务5：修改 RAG 服务支持版本管理
- [ ] 向量库元数据包含 version_id, version_number, version_label
- [ ] 向量库元数据包含 status, effective_date, is_latest
- [ ] 默认只搜索 is_latest=true 且 status=effective 的文档
- [ ] version_strategy 参数支持 latest_effective
- [ ] version_strategy 参数支持 specific_date
- [ ] version_strategy 参数支持 all_versions
- [ ] 答案中标注引用文档的版本信息
- [ ] 引用作废版本时显示警告提示
- [ ] 版本对比搜索功能正常

---

## 任务组4：前端界面开发

### 任务6：实现文档版本管理界面
- [ ] 文档列表页显示版本号、版本标签、状态
- [ ] 文档列表页显示生效日期、复审日期
- [ ] 状态标签颜色区分正确（生效中-绿色、审核中-黄色、已作废-灰色）
- [ ] 版本历史页面时间轴展示正确
- [ ] 版本详情页面显示完整元数据
- [ ] 版本详情页面显示审批历史
- [ ] 版本对比页面左右对比正常
- [ ] 版本对比高亮新增/删除/修改部分
- [ ] 响应式布局正常

### 任务7：实现上传去重交互
- [ ] 文件哈希计算正确（Web Crypto API）
- [ ] 调用去重检测 API 正常
- [ ] exact_match 提示框显示正确
- [ ] name_match 提示框显示正确
- [ ] 上传表单显示上一版本变更历史
- [ ] 变更摘要、变更详细说明必填验证
- [ ] 版本号自动填充（上一版本+1）

---

## 任务组5：审批与培训

### 任务8：实现审批工作流界面
- [ ] 待审批列表显示正确
- [ ] 审批详情页显示版本对比
- [ ] 审批操作 [通过] [拒绝] 正常
- [ ] 审批意见必填验证
- [ ] 审批历史记录显示正确
- [ ] 我的提交列表显示正确
- [ ] 权限控制生效（只有特定角色可审批）

### 任务9：实现文档培训/分发功能
- [ ] 版本生效后自动创建培训任务
- [ ] GET /api/v1/documents/versions/{version_id}/distribution 接口正常
- [ ] POST /api/v1/documents/distribution/{id}/acknowledge 接口正常
- [ ] 我的培训任务列表显示正确
- [ ] 文档阅读确认功能正常
- [ ] 培训完成统计正确

---

## 任务组6：复审与问答增强

### 任务10：实现文档复审提醒功能
- [ ] APScheduler 定时任务正常运行
- [ ] 每天检查 review_date 即将到期的文档
- [ ] 提前30天、7天、1天提醒逻辑正确
- [ ] GET /api/v1/documents/pending-review 接口正常
- [ ] 仪表盘显示待复审文档数量
- [ ] 复审流程正常

### 任务11：增强问答界面（版本信息展示）
- [ ] 答案卡片显示文档版本号
- [ ] 答案卡片显示版本状态
- [ ] 作废版本显示警告提示
- [ ] 来源文档列表显示版本标签
- [ ] 版本对比快捷入口可用
- [ ] 日期选择器支持历史版本追溯

---

## 任务组7：测试与文档

### 任务12：编写版本管理单元测试
- [ ] DocumentVersionStore 方法测试覆盖
- [ ] 状态流转验证测试覆盖
- [ ] 版本对比逻辑测试覆盖
- [ ] 去重检测逻辑测试覆盖
- [ ] 测试覆盖率 > 80%
- [ ] 所有单元测试通过

### 任务13：编写版本管理集成测试
- [ ] 上传→审批→生效→作废流程测试通过
- [ ] 多版本并行场景测试通过
- [ ] 问答时版本过滤测试通过
- [ ] 权限控制测试通过
- [ ] 所有集成测试通过

---

## 合规性检查

### ISO 13485:2016 合规
- [ ] 文档版本控制符合 4.2.3 要求
- [ ] 审批历史记录符合 4.2.4 要求
- [ ] 变更控制符合 7.3.7 要求

### FDA 21 CFR Part 11 合规
- [ ] 审计追踪完整
- [ ] 电子签名记录（审批人、时间）
- [ ] 签名与记录关联

---

## 性能检查

- [ ] 版本历史查询 < 500ms（1000个版本）
- [ ] 版本对比 < 2s（大文档）
- [ ] 去重检测 < 100ms
- [ ] RAG 搜索版本过滤 < 100ms

---

## 最终验收

- [ ] 所有任务完成
- [ ] 所有验收标准通过
- [ ] 所有测试通过
- [ ] 文档完整
- [ ] 代码审查通过
