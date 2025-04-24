# QAlite 一键启动工具

这是一个用于简化 QAlite 项目启动过程的工具，支持同时启动前后端服务，并允许选择不同的 Conda 虚拟环境来运行后端。

## 功能特点

- 自动检测并列出可用的 Conda 环境
- 支持手动输入环境名称
- 自动安装缺失的前端依赖
- 显示后端所需的依赖
- 实时显示前后端日志
- 跨平台支持 (Windows、macOS、Linux)

## 使用方法

### Windows 系统

1. 双击 `start.bat` 文件
2. 按照提示选择 Conda 环境
3. 确认启动

或者在命令行中运行：

```
python start.py
```

### macOS/Linux 系统

1. 在终端中运行：

```
chmod +x start.sh  # 首次使用前给予执行权限
./start.sh
```

或者直接运行 Python 脚本：

```
python3 start.py
```

## 环境要求

- Python 3.8+
- Conda 环境管理器
- Node.js 和 npm (用于前端)

## 后端依赖

后端需要以下 Python 包：

- fastapi
- uvicorn
- pydantic
- python-multipart

可以使用以下命令安装：

```
conda activate <环境名>
pip install -r backend/requirements.txt
```

## 故障排除

### 找不到 Conda 环境

- 确保已安装 Conda 并添加到环境变量中
- 可以选择手动输入环境名称

### 前端启动失败

- 确保已安装 Node.js 和 npm
- 尝试手动安装前端依赖：`cd frontend && npm install`

### 后端启动失败

- 确保所选环境中已安装所需依赖
- 检查 `backend/requirements.txt` 文件中列出的依赖是否已安装

## 停止服务

在启动器窗口中按 `Ctrl+C` 可以停止所有服务。 