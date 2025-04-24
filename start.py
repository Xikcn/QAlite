import os
import subprocess
import sys
import threading
import time
import json
from pathlib import Path
import webbrowser  # 添加导入webbrowser模块
import re

# 定义配置文件路径
CONFIG_FILE = Path("qalite_config.json")

# 显示启动信息
print("="*50)
print("正在启动QAlite...")
print("="*50)

def get_conda_envs():
    """获取所有可用的conda环境"""
    try:
        # 使用conda env list命令获取所有环境
        # Windows系统使用conda.bat
        conda_cmd = "conda.bat" if sys.platform == "win32" else "conda"
        
        result = subprocess.run(
            [conda_cmd, "env", "list", "--json"], 
            capture_output=True, 
            text=True,
            shell=True
        )
        if result.returncode != 0:
            print(f"获取conda环境失败: {result.stderr}")
            return []
        
        # 解析JSON输出
        try:
            env_data = json.loads(result.stdout)
            envs = [os.path.basename(env) for env in env_data.get("envs", [])]
            return envs
        except json.JSONDecodeError:
            print(f"解析conda环境列表失败，尝试直接解析输出")
            # 如果JSON解析失败，尝试通过普通命令获取
            result = subprocess.run(
                [conda_cmd, "env", "list"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode != 0:
                return []
            
            # 解析输出行
            envs = []
            for line in result.stdout.splitlines():
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.split()
                if parts:
                    envs.append(parts[0])
            return envs
    except Exception as e:
        print(f"获取conda环境时出错: {str(e)}")
        return []

def check_requirements():
    """检查必要的依赖是否已安装"""
    backend_dir = Path("backend")
    requirements_file = backend_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print("警告: 未找到backend/requirements.txt文件")
        return
    
    print("检查后端依赖...")
    try:
        with open(requirements_file, 'r') as f:
            requirements = [line.strip() for line in f if line.strip()]
        
        print(f"需要的依赖: {', '.join(requirements)}")
        print("请确保您选择的conda环境中已安装这些依赖")
        print("您可以使用以下命令安装依赖:")
        print(f"conda activate <环境名> && pip install -r {requirements_file}")
    except Exception as e:
        print(f"读取依赖文件时出错: {str(e)}")

def start_backend(conda_env):
    """启动后端服务"""
    backend_dir = Path("backend")
    
    # 构建激活conda环境并启动后端的命令
    if sys.platform == "win32":
        cmd = f"call conda.bat activate {conda_env} && cd {backend_dir} && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    else:
        cmd = f"source activate {conda_env} && cd {backend_dir} && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    
    print(f"正在启动后端服务 (环境: {conda_env})...")
    
    # 在Windows上使用不同的shell
    if sys.platform == "win32":
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, executable="/bin/bash")
    
    # 实时输出后端日志
    for line in iter(process.stdout.readline, b''):
        # 在Windows系统上使用GBK解码，其他系统使用UTF-8
        if sys.platform == "win32":
            decoded_line = line.decode('gbk', errors='replace').strip()
        else:
            decoded_line = line.decode('utf-8', errors='replace').strip()
        print(f"[后端] {decoded_line}")

def start_frontend():
    """启动前端服务"""
    frontend_dir = Path("frontend")
    
    # 检查前端依赖
    package_json = frontend_dir / "package.json"
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print("警告: 前端依赖可能尚未安装")
        print("正在安装前端依赖...")
        
        if sys.platform == "win32":
            install_cmd = f"cd {frontend_dir} && npm install"
        else:
            install_cmd = f"cd {frontend_dir} && npm install"
        
        try:
            subprocess.run(install_cmd, shell=True, check=True)
            print("前端依赖安装完成")
        except subprocess.CalledProcessError:
            print("前端依赖安装失败，请手动运行 'cd frontend && npm run dev'")
            return
    
    # 进入前端目录并启动开发服务器，设置为生产模式以禁用Vue DevTools
    if sys.platform == "win32":
        cmd = f"cd {frontend_dir} && set NODE_ENV=production&& npm run dev"
    else:
        cmd = f"cd {frontend_dir} && NODE_ENV=production npm run dev"
    
    print("正在启动前端服务...")
    
    # 在Windows上使用不同的shell
    if sys.platform == "win32":
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, executable="/bin/bash")
    
    # 输出前端日志但不自动打开浏览器
    for line in iter(process.stdout.readline, b''):
        # 在Windows系统上使用GBK解码，其他系统使用UTF-8
        if sys.platform == "win32":
            decoded_line = line.decode('gbk', errors='replace').strip()
        else:
            decoded_line = line.decode('utf-8', errors='replace').strip()
        
        print(f"[前端] {decoded_line}")

def save_config(conda_env):
    """保存配置到文件"""
    config = {
        "conda_env": conda_env,
        "last_used": time.time()
    }
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        print(f"配置已保存: 使用环境 '{conda_env}'")
    except Exception as e:
        print(f"保存配置时出错: {str(e)}")

def load_config():
    """从文件加载配置"""
    if not CONFIG_FILE.exists():
        return None
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        print(f"已加载保存的配置: 环境 '{config.get('conda_env')}'")
        return config
    except Exception as e:
        print(f"加载配置时出错: {str(e)}")
        return None

def main():
    print("QAlite 一键启动工具")
    print("="*50)
    
    # 检查依赖
    check_requirements()
    
    # 尝试加载保存的配置
    config = load_config()
    if config and "conda_env" in config:
        # 使用保存的环境
        selected_env = config["conda_env"]
        print(f"使用上次选择的环境: {selected_env}")
        # 使用保存的环境时直接启动，无需确认
        print(f"正在使用环境 '{selected_env}' 启动应用...")
    else:
        # 获取conda环境列表
        conda_envs = get_conda_envs()
        
        if not conda_envs:
            print("未找到可用的conda环境，或者无法获取环境列表")
            manual_input = input("您想手动输入conda环境名称吗? (y/n): ").lower()
            if manual_input != 'y':
                return
            
            selected_env = input("请输入conda环境名称: ").strip()
            if not selected_env:
                print("环境名称不能为空")
                return
        else:
            # 显示环境列表供用户选择
            print("\n可用的conda环境:")
            for i, env in enumerate(conda_envs, 1):
                print(f"{i}. {env}")
            print(f"{len(conda_envs)+1}. 手动输入环境名称")
            
            # 让用户选择环境
            try:
                choice = int(input("\n请选择用于启动后端的conda环境 (输入序号): "))
                if choice < 1 or choice > len(conda_envs) + 1:
                    print("无效的选择")
                    return
                
                if choice <= len(conda_envs):
                    selected_env = conda_envs[choice-1]
                else:
                    selected_env = input("请输入conda环境名称: ").strip()
                    if not selected_env:
                        print("环境名称不能为空")
                        return
                
                print(f"已选择环境: {selected_env}")
            except ValueError:
                print("请输入有效的数字")
                return
            except KeyboardInterrupt:
                print("\n操作已取消")
                return
        
        # 首次选择环境时需要确认
        confirm = input(f"是否使用环境 '{selected_env}' 启动应用? (y/n): ").lower()
        if confirm != 'y':
            print("操作已取消")
            return
        
        # 保存选择的环境
        save_config(selected_env)
    
    # 启动前端和后端
    backend_thread = threading.Thread(target=start_backend, args=(selected_env,), daemon=True)
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    
    # 定义前端URL - 这里假设前端运行在固定端口
    frontend_url = "http://localhost:5173"
    
    # 启动服务
    backend_thread.start()
    print("后端服务启动中...")
    time.sleep(2)  # 给后端启动一些时间
    
    # 启动前端服务
    frontend_thread.start()
    print("前端服务启动中...")
    time.sleep(2)  # 给前端启动一些时间
    
    # 启动浏览器访问前端
    print(f"正在打开浏览器访问前端: {frontend_url}")
    webbrowser.open(frontend_url)
    
    # 输出提示信息
    print("\n服务已启动! 按 Ctrl+C 可以停止服务")
    print(f"提示: 删除 {CONFIG_FILE} 文件可重置环境配置，下次启动时重新选择环境")
    
    # 保持程序运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n收到终止信号，正在关闭服务...")

if __name__ == "__main__":
    main() 