FROM python:3.9-slim

WORKDIR /app

# 使用国内镜像源加速
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY backend/ ./backend/
COPY start.py .

# 创建存储markdown文件的目录
RUN mkdir -p backend/qa_files

# 暴露FastAPI服务端口
EXPOSE 8000

# 启动后端服务
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"] 