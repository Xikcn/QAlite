
@echo off
call conda activate edge_tool
echo ʹ��Conda����: edge_tool
pip list | findstr "fastapi uvicorn"
echo ������˷���...
uvicorn main:app --host 0.0.0.0 --port 8000
pause
