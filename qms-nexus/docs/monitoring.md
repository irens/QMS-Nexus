# 日志与监控使用说明

## 日志格式
所有日志统一 JSON 输出，包含：
- ts：毫秒时间戳
- level：级别
- msg：内容
- module / func：模块函数
- user：用户标识（可选）
- cost：耗时秒（可选）

## 监控访问
1. 启动服务：
   ```bash
   docker compose up -d
   ```
2. Prometheus：http://localhost:9090
3. Grafana：http://localhost:3000（admin/admin）
4. 已内置看板：QMS-Nexus 监控（上传/检索 QPS、延迟）

## 关键指标
- `qms_upload_total{status}` 上传次数
- `qms_search_total{status}` 检索次数
- `qms_upload_duration_seconds` 上传延迟分布
- `qms_search_duration_seconds` 检索延迟分布