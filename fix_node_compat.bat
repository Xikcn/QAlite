@echo off
echo ==============================================
echo QAlite 低版本Node.js兼容性修复脚本
echo ==============================================
echo 本脚本将安装兼容低版本Node.js的前端依赖
echo 适用于遇到以下错误的情况:
echo SyntaxError: Unexpected token '||='
echo.

cd frontend

echo 步骤1: 确保配置文件存在...
if not exist package.json (
  echo 错误: 未找到package.json文件
  exit /b 1
)

echo 步骤2: 清理现有node_modules...
if exist node_modules (
  echo 正在删除node_modules文件夹...
  rmdir /s /q node_modules
)

echo 步骤3: 安装兼容版本依赖...
call npm run compat-install

if %ERRORLEVEL% NEQ 0 (
  echo 安装失败，请手动执行以下命令:
  echo cd frontend
  echo npm ci --legacy-peer-deps
  pause
  exit /b 1
)

echo.
echo 兼容性修复完成!
echo 现在您可以运行 start.bat 启动应用
echo.
pause 