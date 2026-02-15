# 多阶段构建QMS-Nexus前端
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine AS production

# 安装必要的工具
RUN apk add --no-cache bash

# 复制Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建后的文件
COPY --from=builder /app/dist /usr/share/nginx/html

# 创建健康检查脚本
RUN echo '#!/bin/bash' > /healthcheck.sh && \
    echo 'curl -f http://localhost/system || exit 1' >> /healthcheck.sh && \
    chmod +x /healthcheck.sh

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /healthcheck.sh

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]
