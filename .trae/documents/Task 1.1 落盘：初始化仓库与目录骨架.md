### 立即执行（仅落盘，不改业务代码）
1. 创建 qms-nexus/ 根目录及全部子级文件夹
2. 写入 .gitignore、README.md、requirements.txt、docker 文件等初始模板
3. tree -L 2 截图验收，确保与架构方案一致
4. 完成后自动进入 Task 1.2（锁定依赖哈希）

### 风险与回滚
- 全部新增文件，无覆盖风险；可随时 git reset --hard 回滚