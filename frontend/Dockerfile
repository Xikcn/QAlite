FROM node:16-alpine

WORKDIR /app

# 使用国内镜像源加速
RUN npm config set registry https://registry.npmmirror.com

# 复制package.json和package-lock.json
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci

# 复制所有前端源代码
COPY frontend/ ./

# 配置环境变量，确保前端可以连接到后端API
ENV VITE_API_URL=http://backend:8000

# 暴露前端服务端口
EXPOSE 5173

# 使用Vite开发服务器启动前端应用
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"] 