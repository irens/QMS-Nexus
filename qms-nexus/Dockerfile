# 多阶段构建：依赖阶段 + 运行阶段
FROM python:3.10-slim AS builder

# 系统依赖：编译工具与 MinerU 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境并安装 Python 依赖
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ---------------------------------
# 运行阶段
FROM python:3.10-slim

# 系统运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 复制虚拟环境
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# 工作目录
WORKDIR /app

# 复制源码
COPY . .

# 暴露端口
EXPOSE 8000

# 默认命令：启动 FastAPI
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]