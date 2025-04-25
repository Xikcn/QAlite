import os
import subprocess
import sys
import threading
import time
import json
from pathlib import Path
import webbrowser  # 添加导入webbrowser模块
import re
import shutil  # 用于检查命令是否存在

# 定义配置文件路径
CONFIG_FILE = Path("qalite_config.json")
# 清华镜像站地址
PYPI_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"

# 显示启动信息
print("="*50)
print("正在启动QAlite...")
print("="*50)

def check_command_exists(command):
    """检查命令是否存在于系统PATH中"""
    return shutil.which(command) is not None

def check_python_environment():
    """检测是否安装了Python及其版本"""
    try:
        # 尝试运行python --version
        result = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print(f"检测到基础Python环境: {version}")
            return True, version
        
        # 如果python命令不可用，尝试python3
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print(f"检测到基础Python环境: {version}")
            return True, version
        
        print("未检测到可用的Python环境")
        return False, None
    except Exception as e:
        print(f"检测Python环境时出错: {str(e)}")
        return False, None

def check_node_environment():
    """检测是否安装了Node.js及npm"""
    try:
        # 检查Node.js版本
        node_result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            shell=True  # 添加shell=True以更可靠地在Windows上查找命令
        )
        # 检查npm版本
        npm_result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            shell=True  # 添加shell=True以更可靠地在Windows上查找命令
        )
        
        if node_result.returncode == 0 and npm_result.returncode == 0:
            node_version = node_result.stdout.strip()
            npm_version = npm_result.stdout.strip()
            print(f"检测到Node.js环境: {node_version}, npm: {npm_version}")
            return True, node_version, npm_version
        
        if node_result.returncode != 0:
            print("警告: 未检测到Node.js")
        if npm_result.returncode != 0:
            print("警告: 未检测到npm")
        
        return False, None, None
    except Exception as e:
        print(f"检测Node.js环境时出错: {str(e)}")
        return False, None, None

def check_package_installed(env, package):
    """检查指定环境中是否已安装某个包"""
    try:
        if env == "base_python":
            # 使用基础Python环境检查
            cmd = f"pip show {package}"
        else:
            # 使用conda环境检查
            if sys.platform == "win32":
                cmd = f"call conda.bat activate {env} && pip show {package}"
            else:
                cmd = f"source activate {env} && pip show {package}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def get_conda_envs():
    """获取所有可用的conda环境"""
    envs = []
    
    # 检查conda命令是否可用
    try:
        # 尝试检测conda是否存在
        conda_cmd = "conda.bat" if sys.platform == "win32" else "conda"
        result = subprocess.run(
            [conda_cmd, "--version"], 
            capture_output=True, 
            text=True,
            shell=True
        )
        if result.returncode != 0:
            print("未检测到conda环境")
            return envs
        
        print(f"检测到conda: {result.stdout.strip()}")
        
        # 使用conda env list命令获取所有环境
        try:
            result = subprocess.run(
                [conda_cmd, "env", "list", "--json"], 
                capture_output=True, 
                text=True,
                shell=True
            )
            if result.returncode != 0:
                print(f"获取conda环境失败: {result.stderr}")
                return envs
            
            # 解析JSON输出
            try:
                env_data = json.loads(result.stdout)
                envs = [os.path.basename(env) for env in env_data.get("envs", [])]
                print(f"检测到conda环境: {', '.join(envs)}")
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
                    return envs
                
                # 解析输出行
                for line in result.stdout.splitlines():
                    if line.startswith('#') or not line.strip():
                        continue
                    parts = line.split()
                    if parts:
                        envs.append(parts[0])
                print(f"检测到conda环境: {', '.join(envs)}")
                return envs
        except Exception as e:
            print(f"获取conda环境列表时出错: {str(e)}")
            return envs
    except Exception as e:
        print(f"检测conda时出错: {str(e)}")
        return envs

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
        print("请确保您选择的环境中已安装这些依赖")
        print("您可以使用以下命令安装依赖:")
        print(f"pip install -r {requirements_file} -i {PYPI_MIRROR}")
        print("或者如果使用conda环境:")
        print(f"conda activate <环境名> && pip install -r {requirements_file} -i {PYPI_MIRROR}")
        
        # 询问是否自动安装依赖
        auto_install = input("是否自动安装依赖? (y/n): ").lower()
        if auto_install == 'y':
            install_requirements(requirements_file)
    except Exception as e:
        print(f"读取依赖文件时出错: {str(e)}")

def install_requirements(requirements_file):
    """使用清华镜像站安装依赖"""
    print("正在安装依赖...")
    
    try:
        # 使用清华镜像站安装依赖
        cmd = f"pip install -r {requirements_file} -i {PYPI_MIRROR}"
        result = subprocess.run(cmd, shell=True, check=True, text=True)
        print("依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {str(e)}")
        print("请尝试手动安装依赖")

def install_frontend_dependencies():
    """安装前端依赖"""
    frontend_dir = Path("frontend")
    
    print("正在安装前端依赖...")
    try:
        # 在Windows上使用shell=True更可靠
        if sys.platform == "win32":
            install_cmd = f"cd {frontend_dir} && npm install"
        else:
            install_cmd = f"cd {frontend_dir} && npm install"
        
        subprocess.run(install_cmd, shell=True, check=True)
        
        # 确保vite已安装
        print("检查Vite是否已安装...")
        if not (frontend_dir / "node_modules" / ".vite").exists():
            print("Vite未安装或不完整，尝试单独安装...")
            vite_install_cmd = f"cd {frontend_dir} && npm install vite@latest --save-dev"
            subprocess.run(vite_install_cmd, shell=True, check=True)
        
        print("前端依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"前端依赖安装失败: {str(e)}")
        return False

def start_backend(conda_env):
    """启动后端服务"""
    backend_dir = Path("backend")
    
    # 根据环境类型构建启动命令
    if conda_env == "base_python":
        # 使用基础Python环境
        cmd = f"cd {backend_dir} && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    else:
        # 使用conda环境
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
        # 尝试安装，即使检测到没有Node.js也尝试
        success = install_frontend_dependencies()
        if not success:
            print("前端依赖安装失败，请手动运行 'cd frontend && npm install && npm run dev'")
            print("可能需要先安装Node.js: https://nodejs.org/")
            return False
    
    # 尝试查找package.json中的启动脚本
    print("正在启动前端服务...")
    try:
        with open(frontend_dir / "package.json", "r") as f:
            package_data = json.load(f)
            dev_script = package_data.get("scripts", {}).get("dev", "")
            
            # 使用package.json中定义的开发脚本，通常是"vite"
            if dev_script:
                print(f"使用package.json中的开发脚本: {dev_script}")
                if sys.platform == "win32":
                    cmd = f"cd {frontend_dir} && set NODE_ENV=production&& npm run dev"
                else:
                    cmd = f"cd {frontend_dir} && NODE_ENV=production npm run dev"
            else:
                print("未找到开发脚本，尝试直接使用npx vite")
                # 使用npx确保即使没有全局安装也能运行
                if sys.platform == "win32":
                    cmd = f"cd {frontend_dir} && set NODE_ENV=production&& npx vite"
                else:
                    cmd = f"cd {frontend_dir} && NODE_ENV=production npx vite"
    except Exception as e:
        print(f"读取package.json失败: {str(e)}，尝试直接启动vite")
        # 直接尝试启动vite
        if sys.platform == "win32":
            cmd = f"cd {frontend_dir} && set NODE_ENV=production&& npx vite"
        else:
            cmd = f"cd {frontend_dir} && NODE_ENV=production npx vite"
    
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
    
    return True

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
    
    # 1. 先检测所有可用环境
    print("正在检测可用的Python环境...")
    # 检查基础Python环境
    has_python, python_version = check_python_environment()
    # 获取conda环境列表
    conda_envs = get_conda_envs()
    # 检查Node.js环境
    has_node, node_version, npm_version = check_node_environment()
    
    # 2. 尝试加载保存的配置
    config = load_config()
    
    if config and "conda_env" in config:
        # 直接使用保存的环境，不再询问
        selected_env = config["conda_env"]
        print(f"使用上次选择的环境: '{selected_env}'")
        print(f"提示: 删除 {CONFIG_FILE} 文件可重置环境配置")
    else:
        # 没有保存的配置，需要用户选择环境
        env_options = []
        
        # 如果有基础Python环境，添加到选项中
        if has_python:
            env_options.append("base_python")
        
        # 添加conda环境
        env_options.extend(conda_envs)
        
        if not env_options:
            print("未找到可用的Python环境")
            manual_input = input("您想手动输入环境名称吗? (y/n): ").lower()
            if manual_input != 'y':
                return
            
            selected_env = input("请输入环境名称: ").strip()
            if not selected_env:
                print("环境名称不能为空")
                return
        else:
            # 显示环境列表供用户选择
            print("\n可用的Python环境:")
            if has_python:
                print(f"1. 系统Python环境 ({python_version})")
                start_idx = 2
            else:
                start_idx = 1
                
            for i, env in enumerate(conda_envs, start_idx):
                print(f"{i}. conda: {env}")
            print(f"{len(env_options)+1}. 手动输入环境名称")
            
            # 让用户选择环境
            try:
                choice = int(input("\n请选择用于启动后端的Python环境 (输入序号): "))
                if choice < 1 or choice > len(env_options) + 1:
                    print("无效的选择")
                    return
                
                if choice <= len(env_options):
                    selected_env = env_options[choice-1]
                else:
                    selected_env = input("请输入环境名称: ").strip()
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
        
        # 自动保存环境选择，不再询问是否保存
        print(f"保存环境 '{selected_env}' 为默认选择")
        save_config(selected_env)
    
    # 3. 选择完环境后检查依赖
    backend_dir = Path("backend")
    requirements_file = backend_dir / "requirements.txt"
    
    if requirements_file.exists():
        print("\n检查后端依赖...")
        try:
            with open(requirements_file, 'r') as f:
                requirements = [line.strip() for line in f if line.strip()]
                # 解析版本号
                required_packages = []
                for req in requirements:
                    if '==' in req:
                        package_name = req.split('==')[0]
                        required_packages.append(package_name)
                    else:
                        required_packages.append(req)
            
            print(f"需要的依赖: {', '.join(requirements)}")
            print(f"已选择环境: '{selected_env}'")
            
            # 检查是否已经安装了所需依赖
            missing_packages = []
            for package in required_packages:
                if not check_package_installed(selected_env, package):
                    missing_packages.append(package)
            
            if not missing_packages:
                print("恭喜！所需的依赖都已经安装在选定环境中。")
            else:
                print(f"缺少以下依赖: {', '.join(missing_packages)}")
                
                # 根据选择的环境提供安装命令
                if selected_env == "base_python":
                    print("您可以使用以下命令安装依赖:")
                    print(f"pip install -r {requirements_file} -i {PYPI_MIRROR}")
                else:
                    print("您可以使用以下命令安装依赖:")
                    if sys.platform == "win32":
                        print(f"call conda.bat activate {selected_env} && pip install -r {requirements_file} -i {PYPI_MIRROR}")
                    else:
                        print(f"source activate {selected_env} && pip install -r {requirements_file} -i {PYPI_MIRROR}")
                
                # 询问是否自动安装依赖
                auto_install = input("是否在所选环境中自动安装缺少的依赖? (y/n): ").lower()
                if auto_install == 'y':
                    print(f"正在为环境 '{selected_env}' 安装依赖...")
                    
                    if selected_env == "base_python":
                        # 使用基础Python环境安装
                        cmd = f"pip install -r {requirements_file} -i {PYPI_MIRROR}"
                    else:
                        # 使用conda环境安装
                        if sys.platform == "win32":
                            cmd = f"call conda.bat activate {selected_env} && pip install -r {requirements_file} -i {PYPI_MIRROR}"
                        else:
                            cmd = f"source activate {selected_env} && pip install -r {requirements_file} -i {PYPI_MIRROR}"
                    
                    try:
                        result = subprocess.run(cmd, shell=True, check=True, text=True)
                        print("依赖安装完成")
                    except subprocess.CalledProcessError as e:
                        print(f"依赖安装失败: {str(e)}")
                        print("请尝试手动安装依赖")
                        continue_choice = input("是否继续启动应用? (y/n): ").lower()
                        if continue_choice != 'y':
                            return
        except Exception as e:
            print(f"读取依赖文件时出错: {str(e)}")
    
    # 先检查并准备前端环境
    frontend_dir = Path("frontend")
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists() or not (frontend_dir / "node_modules" / ".vite").exists():
        print("前端依赖需要安装...")
        
        # 即使Node.js检测失败，也尝试直接运行npm命令
        # 因为Windows上的PATH环境变量检测可能存在问题
        if not has_node:
            print("尝试直接运行npm安装命令...")
        
        install_frontend = input("是否安装前端依赖? (y/n): ").lower()
        if install_frontend == 'y':
            if not install_frontend_dependencies():
                print("前端依赖安装失败，应用可能无法正常运行")
                proceed = input("是否继续尝试启动? (y/n): ").lower()
                if proceed != 'y':
                    return
    
    # 4. 启动前端和后端
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