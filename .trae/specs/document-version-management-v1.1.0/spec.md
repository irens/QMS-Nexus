# 文档版本管理系统 v1.1.0 规格说明

## Why
医疗器械行业对文档控制有严格要求（ISO 13485:2016、FDA 21 CFR Part 11），需要完整的文档版本生命周期管理、审批工作流、审计追踪。当前系统无版本管理功能，无法满足合规要求。

## What Changes
- **新增** 文档版本管理表结构（document_versions, document_approval_history, document_distribution）
- **新增** 文件去重检测机制（基于 SHA256 哈希）
- **新增** 文档版本审批工作流（draft → review → approved → effective → obsolete）
- **新增** 版本历史追溯和版本对比功能
- **新增** 文档培训/分发管理
- **修改** RAG 问答默认只搜索最新生效版本
- **修改** 前端上传界面增加去重提示和版本管理 UI

## Impact
- 受影响模块：数据库、后端 API、前端界面、向量库、RAG 服务
- 受影响表：documents → document_versions（重构）
- 新增表：document_approval_history, document_distribution
- 新增 API：8个版本管理接口
- 新增前端页面：5个

## ADDED Requirements

### Requirement: 文档版本管理表结构
系统 SHALL 提供完整的文档版本数据模型，支持版本生命周期管理。

#### Scenario: 创建新版本
- **GIVEN** 用户上传新文档或新版本
- **WHEN** 系统接收文件并保存
- **THEN** 创建 document_versions 记录，包含版本号、版本标签、状态、文件哈希等

#### Scenario: 版本状态流转
- **GIVEN** 文档版本处于 draft 状态
- **WHEN** 提交审核 → 审核通过 → 批准生效
- **THEN** 状态依次变更为 review → approved → effective，并记录审批历史

### Requirement: 文件去重检测
系统 SHALL 基于文件内容哈希检测重复文件，防止重复存储。

#### Scenario: 完全相同文件检测
- **GIVEN** 用户上传文件
- **WHEN** 计算 SHA256 哈希并与现有文件对比
- **THEN** 如果哈希相同，提示"文件已存在"，提供查看/重新上传选项

#### Scenario: 同名不同内容检测
- **GIVEN** 用户上传文件名已存在但内容不同
- **WHEN** 检测到文件名匹配但哈希不匹配
- **THEN** 提示"创建为新版本？"，提供创建版本/重命名/取消选项

### Requirement: 版本审批工作流
系统 SHALL 提供多级审批流程，支持编制→审核→批准→生效的完整流程。

#### Scenario: 提交审核
- **GIVEN** 文档处于 draft 状态
- **WHEN** 编制人提交审核
- **THEN** 状态变为 review，通知审核人

#### Scenario: 审批通过
- **GIVEN** 文档处于 review 状态
- **WHEN** 审核人审批通过
- **THEN** 状态变为 approved，等待批准人批准

#### Scenario: 版本生效
- **GIVEN** 文档处于 approved 状态
- **WHEN** 批准人批准
- **THEN** 状态变为 effective，上一版本自动 obsolete，创建培训任务

### Requirement: 问答版本过滤
系统 SHALL 默认只使用最新生效版本回答用户问题。

#### Scenario: 默认搜索
- **GIVEN** 用户提问
- **WHEN** 执行 RAG 检索
- **THEN** 只搜索 is_latest=true 且 status=effective 的文档版本

#### Scenario: 历史版本追溯
- **GIVEN** 用户指定日期查询
- **WHEN** 执行 RAG 检索
- **THEN** 搜索该日期生效的文档版本

## MODIFIED Requirements

### Requirement: 文档上传接口
**原需求**: 上传即生效，无版本管理
**修改后**: 上传后处于 draft 状态，需经过审批流程后生效

### Requirement: 向量库元数据
**原需求**: 只存储 filename, doc_id 等基础信息
**修改后**: 增加 version_id, version_number, version_label, status, effective_date, is_latest

## REMOVED Requirements
无
