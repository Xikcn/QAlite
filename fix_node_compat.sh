#!/bin/bash

echo "=============================================="
echo "QAlite 低版本Node.js兼容性修复脚本"
echo "=============================================="
echo "本脚本将安装兼容低版本Node.js的前端依赖"
echo "适用于遇到以下错误的情况:"
echo "SyntaxError: Unexpected token '||='"
echo ""

cd frontend

echo "步骤1: 确保配置文件存在..."
if [ ! -f package.json ]; then
  echo "错误: 未找到package.json文件"
  exit 1
fi

echo "步骤2: 清理现有node_modules..."
if [ -d node_modules ]; then
  echo "正在删除node_modules文件夹..."
  rm -rf node_modules
fi

echo "步骤3: 安装兼容版本依赖..."
npm run compat-install

if [ $? -ne 0 ]; then
  echo "安装失败，请手动执行以下命令:"
  echo "cd frontend"
  echo "npm ci --legacy-peer-deps"
  read -p "按任意键继续..." key
  exit 1
fi

echo ""
echo "兼容性修复完成!"
echo "现在您可以运行python start.py启动应用"
echo ""
read -p "按任意键继续..." key 