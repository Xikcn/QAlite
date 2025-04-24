
@echo off
call conda activate edge_tool
echo 使用Conda环境: edge_tool
pip list | findstr "fastapi uvicorn"
echo 启动后端服务...
uvicorn main:app --host 0.0.0.0 --port 8000
pause
