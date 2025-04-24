# QALite

一个轻量级的问答笔记应用，使用Vue 3前端和FastAPI后端。

## 功能特点

- 创建和管理Markdown格式的问答笔记
- 编辑、删除和搜索问答对
- 支持分开视图和合并视图模式
- 支持复习模式，帮助记忆和学习
- 自动保存输入内容
- 简洁美观的界面

## 快速启动

### 使用启动器

我们提供了一个便捷的启动器，可以一键启动前后端服务：

1. 双击 `launcher.bat` 运行启动器
2. 在启动器界面中，选择以下选项：
   - 【启动前后端服务】一键启动所有服务
   - 【仅启动前端】或【仅启动后端】分别启动单个服务
   - 【打开Markdown文件夹】直接打开存储笔记的文件夹
3. 服务启动后，浏览器会自动打开前端页面

### 手动启动

如果您想手动启动服务，请按照以下步骤操作：

#### 后端

1. 进入backend目录
2. 安装依赖: `pip install -r requirements.txt`
3. 启动服务: `python main.py`
4. 后端将在 http://localhost:8000 启动

#### 前端

1. 安装依赖: `npm install`
2. 启动服务: `npm run dev`
3. 前端将在 http://localhost:5173 启动

## 文件存储

所有的问答笔记以Markdown格式存储在 `backend/qa_files` 目录中，您可以直接使用文本编辑器或Markdown编辑器打开这些文件进行查看和编辑。

## 系统要求

- Python 3.7+
- Node.js 14+
- 依赖包：
  - 后端: fastapi, uvicorn, pandas, tabulate
  - 前端: vue3, vite

## 使用指南

### 编辑模式

- 创建新的问答对：点击"新建"按钮
- 导航：使用"上一个"和"下一个"按钮或鼠标滚轮
- 切换视图：使用"分开视图"/"合并视图"按钮
- 查找未完成：查找并跳转到未完成的问答对
- 删除：选择一个问答对后点击"删除"按钮

### 复习模式

- 进入复习模式：点击"复习模式"按钮
- 随机/顺序：选择复习顺序
- 显示/隐藏答案：控制答案的可见性
- 输入你的回答：在输入框中练习回答问题

## 许可证

[MIT License](LICENSE)

## 项目介绍

QAlite是一个用于管理QA（问答）格式的Markdown笔记的应用程序。它允许用户创建、编辑和搜索Markdown格式的问答笔记，特别适合整理面试、学习等知识点。

## 技术栈

- 前端：Vue 3 + Vite
- 后端：Python FastAPI

## 安装与运行

### 前提条件

- Node.js >= 16
- Python >= 3.8

### 后端安装

```bash
cd backend
pip install -r requirements.txt
```

### 前端安装

```bash
npm install
```

### 启动后端

```bash
cd backend
python run.py
```

或使用npm脚本：

```bash
npm run backend
```

### 启动前端

```bash
npm run dev
```

然后在浏览器中访问 http://localhost:5173/

## 使用说明

1. 首次使用时，点击左上角菜单按钮，然后创建一个新的Markdown文件
2. 在编辑界面中，问题和答案输入框并排显示
3. 使用鼠标滚轮向上或向下滚动，在问答对之间导航
4. 向下滚动到最后一个问答对时，自动创建新问答对
5. 使用右上角的删除按钮删除当前问答对
6. 点击顶部的搜索图标显示搜索栏，搜索问答内容

## 文件存储

所有Markdown文件将存储在后端的`qa_files`目录中，格式为标准Markdown表格。

## 大模型
| 问题  | 答案                          |
|-----|-------------------------------|
| 什么是防抖？ | 事件停止触发后延迟执行的函数  |
| 如何判断数组？ | `Array.isArray()` 或 `instanceof` |

## 一键运行便携版

无需安装Python和Node.js环境，只需下载便携版即可一键运行：

1. 从[GitHub Releases](https://github.com/你的用户名/QAlite/releases)页面下载最新的`QALite_Portable_Windows.zip`
2. 解压到任意文件夹
3. 双击`start.bat`启动应用
4. 浏览器将自动打开QALite应用页面

便携版特点：
- 内置所有必要的运行环境和依赖
- 无需安装任何额外软件（除了浏览器）
- 适合分享给不熟悉编程的用户

### 系统要求（便携版）
- Windows 10/11
- 现代浏览器（Chrome、Edge、Firefox等）