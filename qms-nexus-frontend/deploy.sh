#!/bin/bash

# QMS-Nexus 前端部署脚本
# 适用于 Nginx 部署方式

set -e

echo "======================================"
echo "QMS-Nexus 前端部署脚本"
echo "======================================"
echo ""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
NGINX_CONF_DIR="/etc/nginx/conf.d"
NGINX_HTML_DIR="/usr/share/nginx/html"
BACKUP_DIR="/backup/qms-nexus-$(date +%Y%m%d-%H%M%S)"

# 函数：打印信息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

# 函数：打印警告
print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 函数：打印错误
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函数：检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 函数：检查Nginx配置
check_nginx_config() {
    print_info "检查Nginx配置..."
    if nginx -t 2>/dev/null; then
        print_info "Nginx配置检查通过"
        return 0
    else
        print_error "Nginx配置检查失败"
        nginx -t
        return 1
    fi
}

# 函数：创建备份
create_backup() {
    print_info "创建备份..."
    
    if [ -d "$NGINX_HTML_DIR" ]; then
        sudo mkdir -p "$BACKUP_DIR"
        sudo cp -r "$NGINX_HTML_DIR"/* "$BACKUP_DIR/"
        print_info "备份已创建: $BACKUP_DIR"
    else
        print_warning "Nginx HTML目录不存在，跳过备份"
    fi
}

# 函数：构建应用
build_app() {
    print_info "构建前端应用..."
    
    # 检查node_modules是否存在
    if [ ! -d "node_modules" ]; then
        print_info "安装依赖..."
        npm ci --only=production
    fi
    
    # 执行构建
    npm run build
    
    if [ $? -eq 0 ]; then
        print_info "构建成功"
    else
        print_error "构建失败"
        exit 1
    fi
}

# 函数：部署静态文件
deploy_static() {
    print_info "部署静态文件..."
    
    # 创建目标目录
    sudo mkdir -p "$NGINX_HTML_DIR"
    
    # 复制文件
    sudo cp -r dist/* "$NGINX_HTML_DIR/"
    
    # 设置权限
    sudo chown -R nginx:nginx "$NGINX_HTML_DIR"
    
    print_info "静态文件部署完成"
}

# 函数：配置Nginx
configure_nginx() {
    print_info "配置Nginx..."
    
    # 检查nginx.conf文件是否存在
    if [ ! -f "nginx.conf" ]; then
        print_error "nginx.conf文件不存在，请先创建配置文件"
        exit 1
    fi
    
    # 备份旧配置
    if [ -f "$NGINX_CONF_DIR/qms-nexus.conf" ]; then
        sudo cp "$NGINX_CONF_DIR/qms-nexus.conf" "$NGINX_CONF_DIR/qms-nexus.conf.backup"
        print_info "已备份旧Nginx配置"
    fi
    
    # 复制新配置
    sudo cp nginx.conf "$NGINX_CONF_DIR/qms-nexus.conf"
    
    # 检查配置
    if check_nginx_config; then
        # 重载Nginx
        sudo systemctl reload nginx
        print_info "Nginx配置已更新并重载"
    else
        print_error "Nginx配置有误，已回滚"
        # 回滚配置
        if [ -f "$NGINX_CONF_DIR/qms-nexus.conf.backup" ]; then
            sudo cp "$NGINX_CONF_DIR/qms-nexus.conf.backup" "$NGINX_CONF_DIR/qms-nexus.conf"
            sudo systemctl reload nginx
        fi
        exit 1
    fi
}

# 函数：健康检查
health_check() {
    print_info "执行健康检查..."
    
    # 等待Nginx启动
    sleep 3
    
    # 检查首页
    if curl -f http://localhost/system >/dev/null 2>&1; then
        print_info "首页访问正常"
    else
        print_error "首页访问失败"
        return 1
    fi
    
    # 检查dashboard
    if curl -f http://localhost/system/dashboard >/dev/null 2>&1; then
        print_info "Dashboard访问正常"
    else
        print_error "Dashboard访问失败"
        return 1
    fi
    
    # 检查旧路由重定向
    if curl -f -L http://localhost/documents >/dev/null 2>&1; then
        print_info "旧路由重定向正常"
    else
        print_error "旧路由重定向失败"
        return 1
    fi
    
    print_info "健康检查通过"
}

# 函数：显示部署信息
show_deployment_info() {
    echo ""
    echo "======================================"
    echo "部署完成！"
    echo "======================================"
    echo ""
    echo "访问地址:"
    echo "  系统首页: http://localhost/system"
    echo "  Dashboard: http://localhost/system/dashboard"
    echo "  文档列表: http://localhost/system/documents"
    echo "  智能问答: http://localhost/system/chat"
    echo ""
    echo "重要路由:"
    echo "  旧路由 /documents → 自动重定向到 /system/documents"
    echo "  旧路由 /chat → 自动重定向到 /system/chat"
    echo ""
    echo "Nginx配置:"
    echo "  配置文件: $NGINX_CONF_DIR/qms-nexus.conf"
    echo "  静态文件: $NGINX_HTML_DIR"
    echo ""
    echo "备份目录:"
    echo "  $BACKUP_DIR"
    echo ""
}

# 主函数
main() {
    echo "开始部署 QMS-Nexus 前端..."
    echo ""
    
    # 检查必要命令
    if ! command_exists npm; then
        print_error "npm 命令未找到，请先安装Node.js"
        exit 1
    fi
    
    if ! command_exists nginx; then
        print_error "nginx 命令未找到，请先安装Nginx"
        exit 1
    fi
    
    if ! command_exists curl; then
        print_error "curl 命令未找到，请先安装curl"
        exit 1
    fi
    
    # 执行部署步骤
    create_backup
    build_app
    deploy_static
    configure_nginx
    
    # 健康检查
    if health_check; then
        show_deployment_info
        print_info "部署成功！"
        exit 0
    else
        print_error "健康检查失败，请检查部署"
        exit 1
    fi
}

# 处理脚本参数
case "${1:-}" in
    --backup)
        create_backup
        ;;
    --build)
        build_app
        ;;
    --deploy)
        deploy_static
        ;;
    --config)
        configure_nginx
        ;;
    --health)
        health_check
        ;;
    --help)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --backup   仅创建备份"
        echo "  --build    仅构建应用"
        echo "  --deploy   仅部署静态文件"
        echo "  --config   仅配置Nginx"
        echo "  --health   仅执行健康检查"
        echo "  --help     显示帮助信息"
        echo ""
        echo "无参数时执行完整部署流程"
        ;;
    "")
        main
        ;;
    *)
        print_error "未知选项: $1"
        echo "使用 --help 查看帮助信息"
        exit 1
        ;;
esac
