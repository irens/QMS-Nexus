# Trae Windows 环境配置

## 🪟 系统环境说明
- **操作系统**: Windows 11/10
- **Shell类型**: PowerShell 5.1+
- **Git版本**: Git for Windows 2.x+
- **Python环境**: Python 3.10+

## ⚙️ 命令风格规范

### 1. 路径分隔符
```powershell
# Windows风格 (推荐)
cd "d:\myproject\qms-nexus"

# 避免使用
# cd d:/myproject/qms-nexus  # Unix风格
# cd d:\myproject\qms-nexus  # 无引号，容易出问题
```

### 2. 命令连接符
```powershell
# PowerShell风格 (推荐)
cd "d:\myproject" ; git status

# 避免使用
# cd d:\myproject && git status  # 在PowerShell中可能不稳定
```

### 3. Git配置优化
```powershell
# 设置Git为Windows优化
git config --global core.autocrlf true
git config --global core.safecrlf warn
git config --global pull.rebase false

# 避免交互式命令
git config --global core.editor "notepad"  # 使用简单编辑器
git config --global format.commitMessageColumns 72
```

## 🎯 最佳实践指南

### Git提交流程
```powershell
# 1. 状态检查
cd "d:\myproject\qms-nexus" ; git status

# 2. 添加文件 (使用-A确保包含所有变更)
cd "d:\myproject\qms-nexus" ; git add -A

# 3. 提交 (使用-F避免编辑器交互)
cd "d:\myproject\qms-nexus" ; git commit -F commit_message.txt

# 4. 验证提交
cd "d:\myproject\qms-nexus" ; git log --oneline -n 3
```

### 避免常见问题
1. **路径引号**: 始终使用双引号包裹路径
2. **命令分隔**: 使用分号(;)而非双和号(&&)
3. **文件编码**: 确保提交信息文件为UTF-8编码
4. **换行符**: Windows使用CRLF，Git会自动处理

### 环境变量设置
```powershell
# 设置PowerShell执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 设置Git环境变量
$env:GIT_REDIRECT_STDERR = "2>&1"
$env:PAGER = "cat"  # 避免分页问题
```

## 🔧 故障排除

### 1. Git提交卡住问题
```powershell
# 如果git log卡住，使用--no-pager
git --no-pager log --oneline -n 3

# 或者设置环境变量避免分页
$env:PAGER = "cat"
```

### 2. 字符编码问题
```powershell
# 确保文件编码正确
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'UTF8'
```

### 3. 路径长度限制
```powershell
# Windows路径长度限制为260字符
# 使用短路径或启用长路径支持
# 在组策略中启用"启用Win32长路径"
```

## 📋 环境检查清单

- [ ] PowerShell执行策略已设置
- [ ] Git for Windows已安装
- [ ] 路径使用双引号包裹
- [ ] 命令使用分号分隔
- [ ] Git配置已优化
- [ ] 环境变量已设置

---

**配置更新时间**: 2026年2月14日
**适用环境**: Windows 10/11 + PowerShell 5.1+
**Git版本**: Git for Windows 2.x+