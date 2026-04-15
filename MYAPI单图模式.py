import os
import sys

# 修复 Python 3.13+ Windows 下 Tcl/Tk 路径问题（tcl 在 tcl\ 目录而非 Lib\）
if sys.platform == 'win32':
    _base = getattr(sys, 'base_prefix', sys.prefix)
    _tcl_dir = os.path.join(_base, 'tcl', 'tcl8.6')
    if os.path.exists(os.path.join(_tcl_dir, 'init.tcl')):
        os.environ['TCL_LIBRARY'] = _tcl_dir
        os.environ['TK_LIBRARY'] = os.path.join(_base, 'tcl', 'tk8.6')

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageTk
import base64
import datetime
import re


# 确保工作目录为脚本所在目录（解决双击运行时找不到配置文件的问题）
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe文件
    script_dir = os.path.dirname(sys.executable)
else:
    # 如果是.py文件
    script_dir = os.path.dirname(os.path.abspath(__file__))

# 切换到脚本所在目录
os.chdir(script_dir)

# 依赖检测和自动安装函数（使用当前解释器，bat 已负责激活环境）
def check_and_install_dependencies():
    """检测并自动安装缺失的依赖"""
    try:
        import subprocess
    except ImportError:
        print("警告: 无法检测依赖，请手动安装依赖库")
        return True
    
    python_exe = sys.executable  # 使用当前解释器（bat 已激活 Conda/venv）
    
    # 读取requirements.txt
    requirements_file = os.path.join(script_dir, "requirements.txt")
    if not os.path.exists(requirements_file):
        print("警告: requirements.txt 不存在，跳过依赖检测")
        return True
    
    missing_packages = []
    required_packages = []
    
    # 包名到模块名的映射
    package_to_module = {
        'Pillow': 'PIL',
        'google-genai': 'google.genai',
        'tkinterdnd2': 'tkinterdnd2',
    }
    
    # 解析requirements.txt
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # 处理版本要求，如 "package>=1.0.0" -> "package"
                package_name = line.split('>=')[0].split('==')[0].split('<=')[0].split('>')[0].split('<')[0].split('!')[0].split('[')[0].strip()
                required_packages.append((package_name, line))
    except Exception as e:
        print(f"读取requirements.txt失败: {e}")
        return True
    
    # 检测缺失的包（使用虚拟环境的Python）
    print("检测依赖库...")
    for package_name, full_spec in required_packages:
        try:
            # 获取模块名
            module_name = package_to_module.get(package_name, package_name)
            
            # 使用虚拟环境的Python检查包是否存在
            check_result = subprocess.run(
                [python_exe, '-c', f'import {module_name}'],
                capture_output=True,
                timeout=10
            )
            
            if check_result.returncode == 0:
                print(f"  ✓ {package_name}: 已安装")
            else:
                missing_packages.append(full_spec)
                print(f"  ✗ {package_name}: 未安装")
        except Exception as e:
            missing_packages.append(full_spec)
            print(f"  ✗ {package_name}: 检测失败 ({str(e)[:50]})")
    
    # 如果有缺失的包，尝试自动安装（使用虚拟环境的Python）
    if missing_packages:
        print(f"\n检测到 {len(missing_packages)} 个缺失的依赖包")
        print("正在自动安装缺失的依赖...")
        print("=" * 60)
        
        try:
            # 使用虚拟环境的pip安装
            for package in missing_packages:
                print(f"正在安装: {package}")
                result = subprocess.run(
                    [python_exe, '-m', 'pip', 'install', package],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    print(f"  ✓ {package}: 安装成功")
                else:
                    print(f"  ✗ {package}: 安装失败")
                    error_msg = result.stderr[:200] if result.stderr else result.stdout[:200]
                    if error_msg:
                        print(f"    错误信息: {error_msg}")
            
            print("=" * 60)
            print("依赖安装完成！")
            print("提示: 如果仍有问题，请重新运行程序")
            print("=" * 60)
            
            # 继续运行，不退出（因为可能只是部分包缺失）
            return True
        except Exception as e:
            print(f"自动安装失败: {e}")
            print("\n请手动运行以下命令安装依赖:")
            print(f"  {python_exe} -m pip install {' '.join(missing_packages)}")
            print("\n或运行: 安装依赖.bat")
            
            if sys.platform == 'win32':
                try:
                    input("\n按回车键继续（可能会出错）...")
                except:
                    pass
            return True  # 继续运行，让用户看到具体错误
    else:
        print("所有依赖已安装 ✓")
        return True

# 检测并安装依赖（在导入其他库之前）
if __name__ == "__main__" or True:  # 确保总是执行
    print("=" * 60)
    print("单图分析打标工具 - 依赖检测")
    print("=" * 60)
    check_and_install_dependencies()
    print()

# 尝试导入拖拽库
def try_import_dnd():
    """尝试导入拖拽库，包括从虚拟环境"""
    try:
        # 首先尝试直接导入
        from tkinterdnd2 import DND_FILES, TkinterDnD
        return True, DND_FILES, TkinterDnD
    except ImportError:
        # 如果失败，尝试添加虚拟环境路径
        try:
            import sys
            import os

            # 检查是否存在虚拟环境
            script_dir = os.path.dirname(os.path.abspath(__file__))
            current_dir = os.getcwd()

            venv_paths = [
                # 当前目录的虚拟环境
                os.path.join(current_dir, '.venv', 'Lib', 'site-packages'),
                os.path.join(current_dir, 'venv', 'Lib', 'site-packages'),
                os.path.join(current_dir, '.venv', 'lib', 'python3.11', 'site-packages'),
                os.path.join(current_dir, 'venv', 'lib', 'python3.11', 'site-packages'),
                # 脚本所在目录的虚拟环境
                os.path.join(script_dir, '.venv', 'Lib', 'site-packages'),
                os.path.join(script_dir, 'venv', 'Lib', 'site-packages'),
                os.path.join(script_dir, '.venv', 'lib', 'python3.11', 'site-packages'),
                os.path.join(script_dir, 'venv', 'lib', 'python3.11', 'site-packages'),
                # 检查Python版本特定的路径
                os.path.join(current_dir, '.venv', 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages'),
                os.path.join(script_dir, '.venv', 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages')
            ]

            for venv_path in venv_paths:
                if os.path.exists(venv_path) and venv_path not in sys.path:
                    sys.path.insert(0, venv_path)
                    try:
                        from tkinterdnd2 import DND_FILES, TkinterDnD
                        print(f"从虚拟环境加载拖拽库: {venv_path}")
                        return True, DND_FILES, TkinterDnD
                    except ImportError:
                        continue

            return False, None, None
        except Exception as e:
            print(f"尝试加载拖拽库时出错: {e}")
            return False, None, None

# 尝试导入拖拽功能
DND_AVAILABLE, DND_FILES, TkinterDnD = try_import_dnd()

if not DND_AVAILABLE:
    print("警告: tkinterdnd2 未安装，拖拽功能将不可用。可以通过 'pip install tkinterdnd2' 安装。")
    DND_FILES = None
    TkinterDnD = None

class ImageAnalysisTool:
    def __init__(self, root):
        try:
            print("  [初始化] 设置窗口属性...")
            self.root = root
            self.root.title("单图分析打标工具 - 多模型支持  作者: zealman")
            self.root.geometry("1260x900")
            self.root.minsize(1080, 820)
            
            print("  [初始化] 加载自定义字体...")
            # 加载自定义字体
            self.load_custom_font()
            
            print("  [初始化] 设置窗口居中...")
            # 设置窗口居中
            self.center_window()
            
            print("  [初始化] 设置样式...")
            # 设置样式
            self.setup_styles()
            
            print("  [初始化] 加载配置文件...")
            # 加载配置
            self.config = self.load_config()
            
            # 模型配置
            self.selected_model = "doubao"

            # 批量处理控制标志
            self.batch_processing = False
            self.stop_batch_processing = False
            
            # 批量处理状态管理
            self.process_mode = "process_all"  # 处理模式：process_all, process_missing_only, overwrite_all
            self.concurrent_workers = 2  # 默认并发数
            
            # 线程安全锁
            self.batch_lock = threading.Lock()
            
            print("  [初始化] 创建界面组件...")
            # 创建界面
            self.create_widgets()
            
            print("  [初始化] 加载保存的配置...")
            # 加载保存的配置
            try:
                self.load_saved_config()
            except Exception as e:
                print(f"  警告: 加载保存的配置时出错: {e}")
                import traceback
                traceback.print_exc()
            
            print("  [初始化] 设置窗口关闭事件...")
            # 设置窗口关闭事件
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            print("  ✓ 初始化完成")
        except Exception as e:
            print(f"\n❌ 初始化程序时出错: {e}")
            import traceback
            traceback.print_exc()
            # 尝试显示错误信息
            try:
                messagebox.showerror("初始化错误", f"程序初始化失败:\n{str(e)}\n\n详细信息请查看控制台输出")
            except:
                pass
            # 不要raise，让程序继续运行，避免闪退
            print("  警告: 初始化过程中出现错误，但程序将继续运行")

    def load_custom_font(self):
        """加载自定义字体"""
        try:
            # 尝试使用系统字体
            self.custom_font = "Microsoft YaHei"
        except:
            self.custom_font = "Arial"

    def center_window(self):
        """窗口居中显示"""
        try:
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            # 如果窗口尺寸为1x1（未初始化），使用默认尺寸
            if width <= 1 or height <= 1:
                width = 1260
                height = 900
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f'{width}x{height}+{x}+{y}')
        except Exception as e:
            print(f"  警告: 窗口居中失败: {e}，使用默认位置")

    def setup_styles(self):
        """设置现代化样式"""
        style = ttk.Style()
        
        # 设置主题
        try:
            style.theme_use('clam')
        except:
            style.theme_use('default')
        
        # 自定义样式
        style.configure('Title.TLabel',
                       font=(self.custom_font, 14, 'bold'),
                       foreground='#2c3e50')

        style.configure('Subtitle.TLabel',
                       font=(self.custom_font, 9),
                       foreground='#34495e')

        style.configure('Header.TLabelframe.Label',
                       font=(self.custom_font, 10, 'bold'),
                       foreground='#2c3e50')

        style.configure('Custom.TButton',
                       font=(self.custom_font, 9),
                       padding=(8, 3))

        style.configure('Action.TButton',
                       font=(self.custom_font, 10, 'bold'),
                       padding=(15, 6))
        
        # 设置颜色
        style.configure('Success.TLabel', foreground='#27ae60')
        style.configure('Error.TLabel', foreground='#e74c3c')
        style.configure('Info.TLabel', foreground='#3498db')

    def load_config(self):
        """加载配置（公共 API 配置 + 单图模式独立配置）"""
        try:
            import config_api
            config = {}
            config.update(config_api.load_api_config())
            config.update(config_api.load_dan_config())
            return config
        except ImportError:
            # 回退到旧逻辑
            return self._load_config_legacy()

    def _load_config_legacy(self):
        """旧版单文件配置加载（兼容）"""
        default = {
            "selected_model": "doubao",
            "doubao_api_key": "", "doubao_model": "doubao-1-5-thinking-vision-pro-250428",
            "autodl_api_key": "", "autodl_model": "Qwen3.5-397B-A17B",
            "aliyun_api_key": "", "aliyun_model": "qwen-vl-plus",
            "system_prompt": "请详细分析这张图片，描述图片的内容、风格、色彩、构图等特征。",
            "concurrent_workers": 2,
            "single_mode": {"image": ""}, "batch_mode": {"folder": ""},
        }
        try:
            with open("config-dan.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in default.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception as e:
            print(f"加载配置失败: {e}")
            return default

    def save_config(self):
        """保存配置到 config-api.json 和 config-dan.json"""
        try:
            import config_api
            config_api.save_api_config(self.config)
            config_api.save_dan_config(self.config)
        except ImportError:
            with open("config-dan.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)

    def on_closing(self):
        """窗口关闭事件处理"""
        if self.batch_processing:
            if messagebox.askokcancel("退出确认", "批量处理正在进行中，确定要退出吗？"):
                self.stop_batch_processing = True
                self.root.destroy()
        else:
            self.root.destroy()

    def create_widgets(self):
        """创建现代化GUI界面"""
        try:
            print("    [创建组件] 主框架...")
            # 主滚动框架
            self.create_scrollable_frame()
            
            print("    [创建组件] 标题区域...")
            # 标题区域
            self.create_header()
            
            print("    [创建组件] 配置区域...")
            # 配置区域
            self.create_config_section()
            
            print("    [创建组件] 模式选择区域...")
            # 模式选择区域
            self.create_mode_section()
            
            print("    [创建组件] 工作区域...")
            # 工作区域
            self.create_work_section()
            
            print("    [创建组件] 操作按钮区域...")
            # 操作按钮区域
            self.create_action_section()
            
            print("    [创建组件] 底部信息区域...")
            # 底部信息区域
            self.create_info_section()

            print("    [创建组件] 设置拖拽功能...")
            # 绑定拖拽事件（延迟执行，确保所有组件都已创建）
            self.root.after(100, self.setup_drag_drop)
            print("    ✓ 所有组件创建完成")
        except Exception as e:
            print(f"    ❌ 创建组件时出错: {e}")
            import traceback
            traceback.print_exc()
            raise

    def create_scrollable_frame(self):
        """创建主框架"""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=6, pady=6)

        # 让工作区 notebook 承担主要的伸缩空间，避免下方预览/结果区域被压缩
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(4, weight=1)

    def create_header(self):
        """创建标题区域"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        header_frame.columnconfigure(0, weight=1)

        # 主标题
        title_label = ttk.Label(header_frame, text="单图分析打标工具", style='Title.TLabel')
        title_label.grid(row=0, column=0)

        # 分隔线
        separator = ttk.Separator(header_frame, orient='horizontal')
        separator.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(8, 0))

    def create_config_section(self):
        """创建配置区域"""
        config_frame = ttk.Frame(self.main_frame)
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 12))
        config_frame.columnconfigure(1, weight=1)
        # 配置区域保持紧凑，避免占用工作区空间
        config_frame.rowconfigure(3, weight=0)

        # 模型选择
        ttk.Label(config_frame, text="选择模型:", font=(self.custom_font, 9)).grid(row=0, column=0, sticky=tk.W, padx=(8, 5), pady=5)
        
        # 第一行：国内模型
        model_frame_1 = ttk.Frame(config_frame)
        model_frame_1.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 8), pady=(0, 0))
        model_frame_1.configure(height=30)  # 固定高度
        
        self.model_var = tk.StringVar(value="doubao")
        
        # 国内模型
        self.doubao_check = ttk.Radiobutton(model_frame_1, text="豆包", variable=self.model_var, value="doubao", command=self.on_model_change)
        self.doubao_check.pack(side=tk.LEFT, padx=(0, 15))
        
        self.autodl_check = ttk.Radiobutton(model_frame_1, text="AutoDL", variable=self.model_var, value="autodl", command=self.on_model_change)
        self.autodl_check.pack(side=tk.LEFT, padx=(0, 15))
        
        self.aliyun_check = ttk.Radiobutton(model_frame_1, text="阿里云", variable=self.model_var, value="aliyun", command=self.on_model_change)
        self.aliyun_check.pack(side=tk.LEFT, padx=(0, 15))

        # 当前模型 API Key / 模型名称（随选择切换，保存到 config-api.json）
        self.api_cred_frame = ttk.LabelFrame(config_frame, text="当前模型 API", padding=(8, 6))
        self.api_cred_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=8, pady=(4, 8))
        self.api_cred_frame.columnconfigure(1, weight=1)
        ttk.Label(self.api_cred_frame, text="API Key:", font=(self.custom_font, 9)).grid(row=0, column=0, sticky=tk.W, padx=(0, 6), pady=2)
        self.api_key_entry = ttk.Entry(self.api_cred_frame, font=(self.custom_font, 9), show="*")
        self.api_key_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(self.api_cred_frame, text="模型名称:", font=(self.custom_font, 9)).grid(row=1, column=0, sticky=tk.W, padx=(0, 6), pady=2)
        self.api_model_id_entry = ttk.Entry(self.api_cred_frame, font=(self.custom_font, 9))
        self.api_model_id_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        api_btn_row = ttk.Frame(self.api_cred_frame)
        api_btn_row.grid(row=2, column=0, columnspan=2, sticky=tk.E, pady=(6, 0))
        ttk.Button(api_btn_row, text="保存 API 配置", command=self.on_save_api_credentials_click).pack(side=tk.RIGHT)
        self._last_selected_model_for_api = None

        # 系统提示词
        ttk.Label(config_frame, text="系统提示词:", font=(self.custom_font, 9)).grid(row=3, column=0, sticky=(tk.W, tk.N), padx=(8, 5), pady=(5, 0))
        
        # 创建可调整大小的提示词输入框
        prompt_frame = ttk.Frame(config_frame)
        prompt_frame.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 8), pady=5)
        prompt_frame.columnconfigure(0, weight=1)
        prompt_frame.rowconfigure(0, weight=1)
        
        self.prompt_text = tk.Text(prompt_frame, height=6, font=(self.custom_font, 9), wrap=tk.WORD)
        self.prompt_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加垂直滚动条
        prompt_scrollbar = ttk.Scrollbar(prompt_frame, orient="vertical", command=self.prompt_text.yview)
        prompt_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.prompt_text.configure(yscrollcommand=prompt_scrollbar.set)
        
        # 绑定失去焦点事件，自动保存配置
        self.prompt_text.bind("<FocusOut>", lambda e: self.auto_save_config())

        # 提示词补充多选（系统提示词下方，文字从 config-api.json 加载）
        try:
            import config_api
            supplement_texts = [
                (self.config.get(tkey, config_api.DEFAULT_PROMPT_SUPPLEMENT_TEXTS[i]), f"prompt_supplement_{i+1}")
                for i, tkey in enumerate(config_api.PROMPT_SUPPLEMENT_TEXT_KEYS)
            ]
        except Exception:
            supplement_texts = [
                ("1纯文本输出,不要评论,不要发表序言", "prompt_supplement_1"),
                ("2不要使用任何 Markdown 格式", "prompt_supplement_2"),
                ("3输出纯英文版本", "prompt_supplement_3"),
                ("4输出纯中文json版本", "prompt_supplement_4"),
            ]
        supplement_frame = ttk.Frame(config_frame)
        supplement_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(0, 8), pady=(0, 4))  # 与提示词输入框左对齐
        supplement_frame.columnconfigure(4, weight=1)  # 空白列吸收益出空间
        self.supplement_vars = {}
        for i, (text, key) in enumerate(supplement_texts):
            var = tk.BooleanVar(value=self.config.get(key, key != "prompt_supplement_4"))
            self.supplement_vars[key] = var
            cb = ttk.Checkbutton(supplement_frame, text=text, variable=var, command=self.auto_save_config)
            cb.grid(row=0, column=i, sticky=tk.W, padx=(0, 12))
        self._supplement_items = supplement_texts  # [(display_text, config_key), ...]

    def create_mode_section(self):
        """创建模式选择区域"""
        self.work_notebook = ttk.Notebook(self.main_frame)
        self.work_notebook.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 12))

        # 创建单图模式TAB
        self.single_frame = ttk.Frame(self.work_notebook)
        self.work_notebook.add(self.single_frame, text="🖼️ 单图分析")

        # 结果区略宽于预览区，减少文本框显得过窄
        self.single_frame.columnconfigure(0, weight=4)
        self.single_frame.columnconfigure(1, weight=5)
        self.single_frame.rowconfigure(0, weight=1)

        # 创建批量模式TAB
        self.batch_frame = ttk.Frame(self.work_notebook)
        self.work_notebook.add(self.batch_frame, text="📁 批量分析")

        self.batch_frame.columnconfigure(0, weight=1)
        self.batch_frame.rowconfigure(1, weight=1)

        # 创建处理日志TAB
        self.log_frame = ttk.Frame(self.work_notebook)
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)
        self.work_notebook.add(self.log_frame, text="📝 处理日志")

        # 绑定TAB切换事件
        self.work_notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def create_work_section(self):
        """创建工作区域内容"""
        # 创建单图模式内容
        self.create_single_mode_content()

        # 创建批量模式内容
        self.create_batch_mode_content()

        # 创建处理日志内容
        self.create_log_tab_content()

    def create_log_tab_content(self):
        """创建处理日志TAB内容"""
        try:
            log_container = ttk.Frame(self.log_frame)
            log_container.pack(fill="both", expand=True, padx=12, pady=12)
            log_container.columnconfigure(0, weight=1)
            log_container.rowconfigure(0, weight=1)

            self.log_text = scrolledtext.ScrolledText(log_container, height=24, font=(self.custom_font, 9), wrap=tk.WORD)
            self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            btn_frame = ttk.Frame(log_container)
            btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(8, 0))

            clear_btn = ttk.Button(btn_frame, text="清空日志", command=self.clear_log, style='Custom.TButton')
            clear_btn.pack(side=tk.LEFT)

            copy_btn = ttk.Button(btn_frame, text="复制全部", command=self.copy_log, style='Custom.TButton')
            copy_btn.pack(side=tk.LEFT, padx=(8, 0))

            self.append_log("日志系统已就绪")
        except Exception as e:
            print(f"创建日志TAB失败: {str(e)}")

    def _sanitize_log_text(self, text):
        """移除不需要展示的响应元数据字段"""
        try:
            if not isinstance(text, str):
                text = str(text)
            # 尝试作为JSON移除字段
            try:
                obj = json.loads(text)
            except Exception:
                obj = None

            sensitive_keys = {
                "role", "created", "id", "model", "service_tier", "object",
                "usage", "prompt_tokens_details", "completion_tokens_details",
                "prompt_tokens", "completion_tokens", "total_tokens"
            }

            if obj is not None:
                def remove_keys(o):
                    if isinstance(o, dict):
                        return {k: remove_keys(v) for k, v in o.items() if k not in sensitive_keys}
                    if isinstance(o, list):
                        return [remove_keys(i) for i in o]
                    return o
                cleaned = remove_keys(obj)
                try:
                    return json.dumps(cleaned, ensure_ascii=False, indent=2)
                except Exception:
                    text = str(cleaned)

            # 文本模式，使用正则移除
            patterns = [
                r'"role"\s*:\s*"(?:assistant|system)"[,]?',
                r'"created"\s*:\s*[^,}\n]+[,]?',
                r'"id"\s*:\s*"[^"]+"[,]?',
                r'"model"\s*:\s*"[^"]+"[,]?',
                r'"service_tier"\s*:\s*"[^"]+"[,]?',
                r'"object"\s*:\s*"[^"]+"[,]?',
                r'"usage"\s*:\s*\{[\s\S]*?\}(,)?',
                r'"prompt_tokens_details"\s*:\s*\{[\s\S]*?\}(,)?',
                r'"completion_tokens_details"\s*:\s*\{[\s\S]*?\}(,)?',
            ]
            cleaned_text = text
            for pat in patterns:
                cleaned_text = re.sub(pat, '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r',\s*\}', '}', cleaned_text)
            cleaned_text = re.sub(r',\s*\]', ']', cleaned_text)
            cleaned_text = re.sub(r'\n\n+', '\n', cleaned_text)
            return cleaned_text.strip()
        except Exception:
            return text if isinstance(text, str) else str(text)

    def append_log(self, message, detail=None):
        """线程安全地追加日志到日志TAB和控制台"""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            base = f"[{timestamp}] {message}"
            if detail is None:
                full_text = base
            else:
                try:
                    detail_text = detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False, indent=2)
                except Exception:
                    detail_text = str(detail)
                detail_text = self._sanitize_log_text(detail_text)
                full_text = base + "\n" + detail_text
            print(full_text)

            def _do_append():
                try:
                    if hasattr(self, 'log_text') and self.log_text:
                        self.log_text.insert(tk.END, full_text + "\n")
                        self.log_text.see(tk.END)
                except Exception:
                    pass

            if hasattr(self, 'root') and self.root:
                self.root.after(0, _do_append)
            else:
                _do_append()
        except Exception as e:
            print(f"写日志失败: {str(e)}")

    def clear_log(self):
        """清空日志内容"""
        try:
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.delete(1.0, tk.END)
        except Exception as e:
            print(f"清空日志失败: {str(e)}")

    def copy_log(self):
        """复制全部日志到剪贴板"""
        try:
            if hasattr(self, 'log_text') and self.log_text:
                content = self.log_text.get(1.0, tk.END)
                self.root.clipboard_clear()
                self.root.clipboard_append(content)
                messagebox.showinfo("提示", "日志已复制到剪贴板")
        except Exception as e:
            print(f"复制日志失败: {str(e)}")

    def create_single_mode_content(self):
        """创建单图模式内容"""
        # 使用左右分栏布局
        # 左侧：图片选择和预览
        left_frame = ttk.Frame(self.single_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(8, 4), pady=8)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)

        # 右侧：分析结果预览
        right_frame = ttk.Frame(self.single_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(4, 8), pady=8)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        # 配置单图模式的行权重
        self.single_frame.rowconfigure(0, weight=1)

        # 左侧 - 图片选择区域
        image_frame = ttk.LabelFrame(left_frame, text="📷 图片选择")
        image_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        image_frame.columnconfigure(1, weight=1)

        # 图片路径输入
        ttk.Label(image_frame, text="图片路径:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.image_entry = ttk.Entry(image_frame)
        self.image_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        # 绑定失去焦点事件，自动保存配置
        self.image_entry.bind("<FocusOut>", lambda e: self.auto_save_config())

        browse_btn = ttk.Button(image_frame, text="浏览", command=self.browse_image)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)

        # 左侧 - 图片预览区域
        preview_frame = ttk.LabelFrame(left_frame, text="🔍 图片预览")
        preview_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.image_preview = ttk.Label(preview_frame, text="请选择图片文件", anchor="center")
        self.image_preview.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)

        # 右侧 - 单图分析结果预览
        result_preview_frame = ttk.LabelFrame(right_frame, text="📄 分析结果预览")
        result_preview_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_preview_frame.columnconfigure(0, weight=1)
        result_preview_frame.rowconfigure(0, weight=1)

        self.single_result_text = scrolledtext.ScrolledText(result_preview_frame, height=20, font=(self.custom_font, 9), wrap=tk.WORD)
        self.single_result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=8, pady=8)

    def create_batch_mode_content(self):
        """创建批量模式内容"""
        # 配置批量模式的行权重
        self.batch_frame.rowconfigure(1, weight=1)

        # 文件夹选择区域
        folder_frame = ttk.LabelFrame(self.batch_frame, text="📁 文件夹选择")
        folder_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=8, pady=(8, 4))
        folder_frame.columnconfigure(1, weight=1)

        # 文件夹路径输入
        ttk.Label(folder_frame, text="图片文件夹:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.folder_entry = ttk.Entry(folder_frame)
        self.folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        # 绑定失去焦点事件，自动保存配置
        self.folder_entry.bind("<FocusOut>", lambda e: self.auto_save_config())

        browse_folder_btn = ttk.Button(folder_frame, text="浏览", command=self.browse_folder)
        browse_folder_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 并发数选择
        concurrent_frame = ttk.Frame(folder_frame)
        concurrent_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        ttk.Label(concurrent_frame, text="并发数:", font=(self.custom_font, 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.concurrent_var = tk.StringVar(value="2")
        self.concurrent_combo = ttk.Combobox(concurrent_frame, textvariable=self.concurrent_var,
                                            values=["2", "4", "5", "10"],
                                            state="readonly", width=10, font=(self.custom_font, 9))
        self.concurrent_combo.pack(side=tk.LEFT)
        self.concurrent_combo.bind("<<ComboboxSelected>>", lambda e: self.auto_save_config())

        # 批量处理信息和进度显示
        info_frame = ttk.LabelFrame(self.batch_frame, text="ℹ️ 批量处理状态")
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=8, pady=(4, 8))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(1, weight=1)

        # 说明文字
        info_text = ttk.Label(info_frame, text="批量模式将分析文件夹中的所有图片文件，分析结果将保存为与图片同名的txt文件。",
                             justify="center", font=(self.custom_font, 10))
        info_text.grid(row=0, column=0, pady=(10, 5), padx=10)

        # 批量处理结果显示区域
        self.batch_result_text = scrolledtext.ScrolledText(info_frame, height=16, font=(self.custom_font, 9), wrap=tk.WORD)
        self.batch_result_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=(5, 10))

    def create_action_section(self):
        """创建操作按钮区域"""
        action_frame = ttk.Frame(self.main_frame)
        action_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        action_frame.columnconfigure(0, weight=1)

        # 按钮容器
        button_frame = ttk.Frame(action_frame)
        button_frame.grid(row=0, column=0)

        # 开始分析按钮
        self.analyze_button = ttk.Button(button_frame, text="🚀 开始分析",
                                        command=self.start_analysis, style='Action.TButton')
        self.analyze_button.pack(side=tk.LEFT, padx=(0, 10))

        # 停止按钮（批量模式用）
        self.stop_button = ttk.Button(button_frame, text="⏹️ 停止处理",
                                     command=self.stop_processing, style='Custom.TButton', state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))

        # 删除所有txt按钮
        self.delete_txt_button = ttk.Button(button_frame, text="🗑️ 删除TXT",
                                           command=self.delete_all_txt_files,
                                           style='Custom.TButton')
        self.delete_txt_button.pack(side=tk.LEFT, padx=(0, 10))

        # 清空结果按钮
        clear_button = ttk.Button(button_frame, text="🗑️ 清空结果",
                                 command=self.clear_results, style='Custom.TButton')
        clear_button.pack(side=tk.LEFT)

    def create_info_section(self):
        """创建底部信息区域（简化版）"""
        info_frame = ttk.Frame(self.main_frame)
        info_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 12))

        # 进度显示
        self.progress_var = tk.StringVar(value="就绪 - 请选择图片进行分析")
        progress_label = ttk.Label(info_frame, textvariable=self.progress_var, style='Info.TLabel')
        progress_label.pack(side=tk.LEFT, padx=8)

    def setup_drag_drop(self):
        """设置拖拽功能"""
        if not DND_AVAILABLE:
            print("警告: tkinterdnd2 未安装，拖拽功能将不可用。可以通过 'pip install tkinterdnd2' 安装。")
            return

        try:
            # 检查是否为TkinterDnD窗口
            if not hasattr(self.root, 'drop_target_register'):
                print("当前窗口不支持拖拽功能")
                return

            # 为图片输入框设置拖拽
            if hasattr(self.image_entry, 'drop_target_register'):
                self.image_entry.drop_target_register(DND_FILES)
                self.image_entry.dnd_bind('<<Drop>>', self.on_image_drop)

            # 为图片预览区域设置拖拽
            if hasattr(self.image_preview, 'drop_target_register'):
                self.image_preview.drop_target_register(DND_FILES)
                self.image_preview.dnd_bind('<<Drop>>', self.on_image_drop)

            # 为文件夹输入框设置拖拽
            if hasattr(self.folder_entry, 'drop_target_register'):
                self.folder_entry.drop_target_register(DND_FILES)
                self.folder_entry.dnd_bind('<<Drop>>', self.on_folder_drop)

            # 为整个窗口设置拖拽作为备用
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_window_drop)

            print("拖拽功能已启用")
        except Exception as e:
            print(f"拖拽功能设置失败: {str(e)}")

    def on_image_drop(self, event):
        """处理图片拖拽事件"""
        try:
            # 获取拖拽的文件路径
            files = self.parse_drop_files(event.data)
            if not files:
                return

            # 取第一个文件
            file_path = files[0]

            # 检查是否为图片文件
            if self.is_image_file(file_path):
                self.image_entry.delete(0, tk.END)
                self.image_entry.insert(0, file_path)
                self.update_image_preview(file_path)
                print(f"已拖入图片: {os.path.basename(file_path)}")
            else:
                print("拖入的文件不是支持的图片格式")

        except Exception as e:
            print(f"处理拖拽文件时出错: {str(e)}")

    def on_folder_drop(self, event):
        """处理文件夹拖拽事件"""
        try:
            # 获取拖拽的文件路径
            files = self.parse_drop_files(event.data)
            if not files:
                return

            # 取第一个路径
            path = files[0]

            # 检查是否为文件夹
            if os.path.isdir(path):
                self.folder_entry.delete(0, tk.END)
                self.folder_entry.insert(0, path)
                # 保存配置
                self.config["batch_mode"]["folder"] = path
                self.save_config()
                print(f"已拖入文件夹: {os.path.basename(path)}")
            elif self.is_image_file(path):
                # 如果拖入的是图片文件，则使用其所在目录
                folder_path = os.path.dirname(path)
                self.folder_entry.delete(0, tk.END)
                self.folder_entry.insert(0, folder_path)
                self.config["batch_mode"]["folder"] = folder_path
                self.save_config()
                print(f"已拖入图片文件，使用其所在目录: {os.path.basename(folder_path)}")
            else:
                print("请拖入文件夹或图片文件")

        except Exception as e:
            print(f"处理拖拽文件夹时出错: {str(e)}")

    def on_window_drop(self, event):
        """处理窗口拖拽事件"""
        try:
            # 获取当前选中的标签页
            current_tab = self.work_notebook.tab(self.work_notebook.select(), "text")

            if "单图分析" in current_tab:
                # 单图模式，处理为图片拖拽
                self.on_image_drop(event)
            else:
                # 批量模式，处理为文件夹拖拽
                self.on_folder_drop(event)

        except Exception as e:
            print(f"处理窗口拖拽时出错: {str(e)}")

    def parse_drop_files(self, data):
        """解析拖拽的文件数据"""
        try:
            # 处理不同格式的拖拽数据
            if isinstance(data, str):
                # 处理Windows路径格式
                if data.startswith('{') and data.endswith('}'):
                    # 移除大括号并分割文件路径
                    files = data.strip('{}').split('} {')
                    # 清理路径
                    files = [f.strip('{}').strip() for f in files if f.strip()]
                else:
                    # 简单的字符串路径
                    files = [data.strip()]
                return files
            elif isinstance(data, (list, tuple)):
                return [str(f).strip('{}').strip() for f in data]
            else:
                return [str(data).strip('{}').strip()]
        except Exception as e:
            print(f"解析拖拽数据时出错: {str(e)}")
            return []

    def is_image_file(self, file_path):
        """检查文件是否为支持的图片格式"""
        if not os.path.isfile(file_path):
            return False

        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in image_extensions

    def on_tab_change(self, event):
        """TAB切换处理"""
        selected_tab = event.widget.tab('current')['text']
        if "单图分析" in selected_tab:
            self.progress_var.set("就绪 - 请选择图片进行分析")
        else:
            self.progress_var.set("就绪 - 请选择包含图片的文件夹")
        
        # TAB切换后自动保存配置
        self.auto_save_config()

    def browse_image(self):
        """浏览选择图片"""
        file_path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp")]
        )
        if file_path:
            self.image_entry.delete(0, tk.END)
            self.image_entry.insert(0, file_path)
            self.update_image_preview(file_path)

    def browse_folder(self):
        """浏览选择文件夹"""
        folder_path = filedialog.askdirectory(title="选择图片文件夹")
        if folder_path:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_path)
            # 保存配置
            self.config["batch_mode"]["folder"] = folder_path
            self.save_config()

    def update_image_preview(self, image_path):
        """更新图片预览"""
        try:
            # 打开图片
            image = Image.open(image_path)

            original_size = image.size

            # 根据当前预览区域动态缩放，窗口放大后预览不会仍然很小
            self.image_preview.update_idletasks()
            preview_width = max(self.image_preview.winfo_width() - 24, 420)
            preview_height = max(self.image_preview.winfo_height() - 24, 320)
            preview_size = (preview_width, preview_height)
            image.thumbnail(preview_size, Image.Resampling.LANCZOS)

            # 转换为PhotoImage
            photo = ImageTk.PhotoImage(image)

            # 更新预览
            self.image_preview.configure(image=photo, text="")
            self.image_preview.image = photo  # 保持引用

            # 显示文件信息
            file_size = os.path.getsize(image_path)
            file_size_mb = file_size / (1024 * 1024)
            info_text = f"文件: {os.path.basename(image_path)}\n大小: {file_size_mb:.2f} MB\n尺寸: {original_size[0]}x{original_size[1]}"

            print(f"已加载图片: {info_text.replace(chr(10), ', ')}")

        except Exception as e:
            self.image_preview.configure(image="", text=f"预览失败: {str(e)}")
            print(f"图片预览失败: {str(e)}")



    def _get_effective_prompt(self):
        """获取有效提示词（系统提示词 + 勾选的补充内容）"""
        base = self.prompt_text.get(1.0, tk.END).strip()
        parts = [base] if base else []
        if hasattr(self, 'supplement_vars') and hasattr(self, '_supplement_items'):
            for text, key in self._supplement_items:
                if self.supplement_vars.get(key, tk.BooleanVar()).get():
                    parts.append(text)
        return "\n".join(parts).strip()

    def auto_save_config(self):
        """自动保存配置"""
        try:
            if hasattr(self, "api_key_entry") and hasattr(self, "_last_selected_model_for_api") and self._last_selected_model_for_api:
                self._flush_api_credentials_for_model(self.model_var.get())
            self.config["selected_model"] = self.model_var.get()
            self.config["system_prompt"] = self.prompt_text.get(1.0, tk.END).strip()
            if hasattr(self, 'supplement_vars'):
                for key, var in self.supplement_vars.items():
                    self.config[key] = var.get()
            
            # 保存并发数配置
            if hasattr(self, 'concurrent_var'):
                try:
                    self.config["concurrent_workers"] = int(self.concurrent_var.get())
                except:
                    self.config["concurrent_workers"] = 2

            # 检查当前选中的TAB来判断模式
            current_tab = self.work_notebook.tab(self.work_notebook.select(), "text")
            if "单图分析" in current_tab:
                # 保存图片路径
                if not self.config.get("single_mode"):
                    self.config["single_mode"] = {}
                self.config["single_mode"]["image"] = self.image_entry.get()
            elif "批量分析" in current_tab:
                self.config["batch_mode"]["folder"] = self.folder_entry.get()

            self.save_config()
            # 不显示日志消息，避免频繁提示
        except Exception as e:
            # 如果自动保存失败，记录错误但不中断程序
            print(f"自动保存配置失败: {e}")



    def load_saved_config(self):
        """加载保存的配置到界面"""
        try:
            if hasattr(self, 'model_var'):
                self.model_var.set(self.config.get("selected_model", "doubao"))
            
            if hasattr(self, 'prompt_text'):
                self.prompt_text.delete(1.0, tk.END)
                self.prompt_text.insert(1.0, self.config.get("system_prompt", ""))
            if hasattr(self, 'supplement_vars'):
                for key, var in self.supplement_vars.items():
                    var.set(self.config.get(key, key != "prompt_supplement_4"))

            # 加载单图模式配置
            single_config = self.config.get("single_mode", {})
            if single_config.get("image") and hasattr(self, 'image_entry'):
                image_path = single_config["image"]
                if image_path and os.path.exists(image_path):
                    self.image_entry.insert(0, image_path)
                    if hasattr(self, 'update_image_preview'):
                        self.update_image_preview(image_path)
                else:
                    print(f"保存的图片路径不存在: {image_path}")

            # 加载批量模式配置
            batch_config = self.config.get("batch_mode", {})
            if batch_config.get("folder") and hasattr(self, 'folder_entry'):
                self.folder_entry.insert(0, batch_config["folder"])
            
            # 加载并发数配置
            if hasattr(self, 'concurrent_var'):
                concurrent_workers = self.config.get("concurrent_workers", 2)
                self.concurrent_var.set(str(concurrent_workers))
                self.concurrent_workers = concurrent_workers
            
            if hasattr(self, "api_key_entry"):
                self._last_selected_model_for_api = self.model_var.get()
                self._load_api_credentials_for_model(self._last_selected_model_for_api)

            # 更新模型名称显示和颜色（延迟执行，确保所有组件都已创建）
            self.root.after(200, self._delayed_update_models)
        except Exception as e:
            print(f"加载保存的配置时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _delayed_update_models(self):
        """延迟更新模型名称和颜色"""
        try:
            if hasattr(self, 'update_model_names'):
                self.update_model_names()
            # 确保颜色更新在模型名称更新之后
            self.root.after(100, self.update_model_colors)
        except Exception as e:
            print(f"延迟更新模型信息时出错: {e}")
            import traceback
            traceback.print_exc()

    def update_model_names(self):
        """更新模型名称显示"""
        try:
            # 检查必要的组件是否存在
            if not hasattr(self, 'doubao_check'):
                print("警告: 模型选择组件尚未创建，跳过更新")
                return
            
            # 获取模型名称用于显示
            doubao_name = self.config.get("doubao_model", "doubao-1-5-thinking-vision-pro-250428")
            autodl_name = self.config.get("autodl_model", "Qwen3.5-397B-A17B")
            aliyun_name = self.config.get("aliyun_model", "qwen-vl-plus")
            
            # 更新单选按钮的显示文本（逐个检查是否存在）
            if hasattr(self, 'doubao_check'):
                self.doubao_check.config(text=f"豆包 ({doubao_name})")
            if hasattr(self, 'autodl_check'):
                self.autodl_check.config(text=f"AutoDL ({autodl_name})")
            if hasattr(self, 'aliyun_check'):
                self.aliyun_check.config(text=f"阿里云 ({aliyun_name})")
            
            # 更新选中状态的文字颜色（不在这里调用，避免重复）
        except Exception as e:
            print(f"更新模型名称显示失败: {e}")
            import traceback
            traceback.print_exc()

    def update_model_colors(self):
        """更新模型选择按钮的颜色"""
        try:
            # 检查必要的组件是否存在
            if not hasattr(self, 'model_var') or not hasattr(self, 'doubao_check'):
                print("警告: 模型选择组件尚未创建，跳过颜色更新")
                return
            
            selected_model = self.model_var.get()
            print(f"当前选中的模型: {selected_model}")
            
            # 使用样式来设置颜色
            style = ttk.Style()
            
            # 重置所有按钮为默认颜色
            style.configure('Doubao.TRadiobutton', foreground='black')
            style.configure('Autodl.TRadiobutton', foreground='black')
            style.configure('Aliyun.TRadiobutton', foreground='black')
            
            # 设置选中按钮为绿色（逐个检查组件是否存在）
            if selected_model == "doubao" and hasattr(self, 'doubao_check'):
                print("设置豆包按钮为绿色")
                style.configure('Doubao.TRadiobutton', foreground='green')
                self.doubao_check.configure(style='Doubao.TRadiobutton')
            elif selected_model == "autodl" and hasattr(self, 'autodl_check'):
                print("设置 AutoDL 按钮为绿色")
                style.configure('Autodl.TRadiobutton', foreground='green')
                self.autodl_check.configure(style='Autodl.TRadiobutton')
            elif selected_model == "aliyun" and hasattr(self, 'aliyun_check'):
                print("设置阿里云按钮为绿色")
                style.configure('Aliyun.TRadiobutton', foreground='green')
                self.aliyun_check.configure(style='Aliyun.TRadiobutton')
            
            print("颜色更新完成")
        except Exception as e:
            print(f"更新模型颜色失败: {e}")
            import traceback
            traceback.print_exc()

    def _flush_api_credentials_for_model(self, model_id):
        if not model_id or not hasattr(self, "api_key_entry"):
            return
        try:
            import config_api
            keys = config_api.MODEL_CREDENTIAL_KEYS.get(model_id)
            if not keys:
                return
            k_key, m_key = keys
            self.config[k_key] = self.api_key_entry.get().strip()
            self.config[m_key] = self.api_model_id_entry.get().strip()
        except Exception as e:
            print(f"写入 API 配置失败: {e}")

    def _load_api_credentials_for_model(self, model_id):
        if not model_id or not hasattr(self, "api_key_entry"):
            return
        try:
            import config_api
            keys = config_api.MODEL_CREDENTIAL_KEYS.get(model_id)
            if not keys:
                return
            k_key, m_key = keys
            name = config_api.MODEL_DISPLAY_NAMES.get(model_id, model_id)
            self.api_cred_frame.configure(text=f"{name} — API 配置")
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.insert(0, self.config.get(k_key, "") or "")
            self.api_model_id_entry.delete(0, tk.END)
            self.api_model_id_entry.insert(0, self.config.get(m_key, "") or "")
        except Exception as e:
            print(f"加载 API 配置到界面失败: {e}")

    def on_save_api_credentials_click(self):
        try:
            mid = self.model_var.get()
            self._flush_api_credentials_for_model(mid)
            self.save_config()
            self.update_model_names()
            self.update_model_colors()
            messagebox.showinfo("已保存", "API Key 与模型名称已写入 config-api.json")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def on_model_change(self):
        """处理模型选择变化"""
        new = self.model_var.get()
        old = getattr(self, "_last_selected_model_for_api", None)
        if old is not None and old != new:
            self._flush_api_credentials_for_model(old)
        self._last_selected_model_for_api = new
        self._load_api_credentials_for_model(new)
        print("模型选择发生变化")
        self.update_model_colors()
        self.auto_save_config()

    def call_api(self, image_path, prompt):
        """根据选择的模型调用相应的API"""
        selected_model = self.config.get("selected_model", "doubao")
        self.append_log("开始调用模型", selected_model)
        
        if selected_model == "doubao":
            return self.call_doubao_api(image_path, prompt)
        elif selected_model == "autodl":
            return self.call_autodl_api(image_path, prompt)
        elif selected_model == "aliyun":
            return self.call_aliyun_api(image_path, prompt)
        else:
            return "错误: 未知的模型类型"

    def call_doubao_api(self, image_path, prompt):
        """调用豆包API"""
        try:
            # 读取图片文件并编码为base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # 获取图片MIME类型
            def get_mime_type(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.bmp': 'image/bmp',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                return mime_types.get(ext, 'image/png')

            mime_type = get_mime_type(image_path)

            # 准备请求数据
            api_key = self.config.get("doubao_api_key", "")
            if not api_key:
                return "错误: 未配置豆包API Key，请在配置文件中设置"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # 构建豆包API请求数据
            content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]

            data = {
                "model": self.config.get("doubao_model", "doubao-1-5-thinking-vision-pro-250428"),
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            }

            data["thinking"] = {"type": "disabled"}

            # 发送请求（带重试机制）
            print("正在发送请求到豆包API...")
            print(f"图片大小: {len(image_data)} 字符")

            timeout = 120  # API超时120秒
            print(f"请求超时设置: {timeout}秒")

            # 重试机制
            max_retries = 3
            retry_delay = 2  # 重试延迟（秒）
            
            for attempt in range(max_retries):
                try:
                    # 使用Session来保持连接
                    session = requests.Session()
                    session.headers.update(headers)
                    
                    # 设置连接池配置
                    adapter = requests.adapters.HTTPAdapter(
                        pool_connections=1,
                        pool_maxsize=1,
                        max_retries=0  # 禁用requests内置重试，使用自定义重试
                    )
                    session.mount('https://', adapter)
                    
                    response = session.post("https://ark.cn-beijing.volces.com/api/v3/chat/completions", 
                                           json=data, timeout=timeout)
                    
                    print(f"API响应状态码: {response.status_code}")

                    if response.status_code == 200:
                        result = response.json()
                        print(f"豆包API响应完整内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                        
                        if "choices" in result and len(result["choices"]) > 0:
                            if "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                                content = result["choices"][0]["message"]["content"]
                                print(f"API调用成功，返回内容长度: {len(content)} 字符")
                                print(f"返回内容前100字符: {content[:100]}...")
                                print(f"返回内容后100字符: {content[-100:] if len(content) > 100 else content}")
                                return content
                            else:
                                print("API响应格式异常")
                                print(f"响应结构: {result}")
                                return f"API响应格式异常: {result}"
                        else:
                            print("API响应格式异常")
                            print(f"响应结构: {result}")
                            return f"API响应格式异常: {result}"
                    else:
                        error_detail = response.text
                        print(f"API调用失败: {response.status_code}")
                        # 对于4xx错误，不重试
                        if 400 <= response.status_code < 500:
                            return f"API调用失败: {response.status_code} - {error_detail}"
                        # 对于5xx错误，继续重试
                        if attempt < max_retries - 1:
                            print(f"服务器错误，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})...")
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2  # 指数退避
                            continue
                        return f"API调用失败: {response.status_code} - {error_detail}"

                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    error_msg = str(e)
                    # 检查是否是连接重置错误
                    if "ConnectionResetError" in error_msg or "10054" in error_msg or "Connection aborted" in error_msg:
                        if attempt < max_retries - 1:
                            print(f"连接被重置，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})...")
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2  # 指数退避
                            continue
                        else:
                            return f"API调用异常: 连接被重置，已重试{max_retries}次仍失败。可能是图片太大或网络不稳定，请尝试：\n1. 压缩图片大小\n2. 检查网络连接\n3. 稍后重试\n\n原始错误: {error_msg}"
                    else:
                        # 其他连接错误
                        if attempt < max_retries - 1:
                            print(f"连接错误，{retry_delay}秒后重试 ({attempt + 1}/{max_retries})...")
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                        else:
                            return f"API调用异常: {error_msg}"

        except Exception as e:
            print(f"API调用异常: {str(e)}")
            return f"API调用异常: {str(e)}"

    def call_autodl_api(self, image_path, prompt):
        """调用 AutoDL OpenAI 兼容 API（https://www.autodl.art/api/v1/chat/completions）"""
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            def get_mime_type(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.bmp': 'image/bmp',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                return mime_types.get(ext, 'image/png')

            mime_type = get_mime_type(image_path)
            api_key = self.config.get("autodl_api_key", "")
            if not api_key:
                return "错误: 未配置 AutoDL API Key，请在界面保存 API 配置"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            # 与多数 VL 网关一致：同一 user 消息内同时包含图片与文本（避免 system+纯图导致失败）
            data = {
                "model": self.config.get("autodl_model", "Qwen3.5-397B-A17B"),
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}",
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                "max_tokens": 4096,
                "stream": False,
            }

            print("正在发送请求到 AutoDL API...")
            print(f"图片大小: {len(image_data)} 字符")
            # VL 推理较慢时易读超时：连接 30s，读取 300s
            _autodl_timeout = (30, 300)
            response = requests.post(
                "https://www.autodl.art/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=_autodl_timeout,
            )
            print(f"API响应状态码: {response.status_code}")

            try:
                result = response.json()
            except Exception:
                return f"API调用失败: {response.status_code} - {response.text[:2000]}"

            if result.get("error"):
                err = result["error"]
                if isinstance(err, dict):
                    return f"API错误: {err.get('message', err)}"
                return f"API错误: {err}"

            if response.status_code != 200:
                return f"API调用失败: {response.status_code} - {response.text[:2000]}"

            if "choices" in result and len(result["choices"]) > 0:
                msg = result["choices"][0].get("message") or {}
                content = msg.get("content")
                if content:
                    print(f"API调用成功，返回内容长度: {len(content)} 字符")
                    return content
                # 部分模型 content 在别处
                if msg.get("refusal"):
                    return f"API拒绝: {msg['refusal']}"
            return f"API响应无有效内容: {json.dumps(result, ensure_ascii=False)[:2000]}"
        except requests.exceptions.Timeout as e:
            print(f"API调用超时: {str(e)}")
            return (
                f"API调用超时: {str(e)}。"
                "若图片较大或网络较慢，可重试、压缩图片或稍后重试。"
            )
        except Exception as e:
            print(f"API调用异常: {str(e)}")
            return f"API调用异常: {str(e)}"

    def call_aliyun_api(self, image_path, prompt):
        """调用阿里云API"""
        try:
            # 读取图片文件并编码为base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # 获取图片MIME类型
            def get_mime_type(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.bmp': 'image/bmp',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                return mime_types.get(ext, 'image/png')

            mime_type = get_mime_type(image_path)

            # 准备请求数据
            api_key = self.config.get("aliyun_api_key", "")
            if not api_key:
                return "错误: 未配置阿里云API Key，请在配置文件中设置"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # 构建阿里云API请求数据
            data = {
                "model": self.config.get("aliyun_model", "qwen-vl-plus"),
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }

            # 发送请求
            print("正在发送请求到阿里云API...")
            print(f"图片大小: {len(image_data)} 字符")

            response = requests.post("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", 
                                   headers=headers, json=data, timeout=120)

            print(f"API响应状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"阿里云API响应完整内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if "choices" in result and len(result["choices"]) > 0:
                    if "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                        content = result["choices"][0]["message"]["content"]
                        print(f"API调用成功，返回内容长度: {len(content)} 字符")
                        print(f"返回内容前100字符: {content[:100]}...")
                        print(f"返回内容后100字符: {content[-100:] if len(content) > 100 else content}")
                        return content
                    else:
                        print("API响应格式异常")
                        print(f"响应结构: {result}")
                        return f"API响应格式异常: {result}"
                else:
                    print("API响应格式异常")
                    print(f"响应结构: {result}")
                    return f"API响应格式异常: {result}"
            else:
                error_detail = response.text
                print(f"API调用失败: {response.status_code}")
                return f"API调用失败: {response.status_code} - {error_detail}"

        except Exception as e:
            print(f"API调用异常: {str(e)}")
            return f"API调用异常: {str(e)}"

    def start_analysis(self):
        """开始分析"""
        # 检查当前模式
        current_tab = self.work_notebook.tab(self.work_notebook.select(), "text")

        if "单图分析" in current_tab:
            self.start_single_analysis()
        else:
            self.start_batch_analysis()

    def start_single_analysis(self):
        """开始单图分析"""
        # 验证输入
        selected_model = self.config.get("selected_model", "doubao")
        if selected_model == "doubao" and not self.config.get("doubao_api_key"):
            messagebox.showerror("错误", "请先在配置文件中配置豆包API Key")
            return
        elif selected_model == "autodl" and not self.config.get("autodl_api_key"):
            messagebox.showerror("错误", "请先配置 AutoDL API Key")
            return
        elif selected_model == "aliyun" and not self.config.get("aliyun_api_key"):
            messagebox.showerror("错误", "请先在配置文件中配置阿里云API Key")
            return

        image_path = self.image_entry.get().strip()
        if not image_path or not os.path.exists(image_path):
            messagebox.showerror("错误", "请选择有效的图片文件")
            return

        prompt = self._get_effective_prompt()
        if not prompt:
            messagebox.showerror("错误", "请输入系统提示词")
            return

        # 禁用按钮
        self.analyze_button.config(state="disabled", text="🔄 分析中...")

        # 清空之前的结果
        self.single_result_text.delete(1.0, tk.END)

        self.append_log("单图-开始分析")

        # 在新线程中执行分析
        threading.Thread(target=self._single_analysis_worker, args=(image_path, prompt), daemon=True).start()

    def _single_analysis_worker(self, image_path, prompt):
        """单图分析工作线程"""
        try:
            print("开始处理单图分析")
            print(f"图片: {os.path.basename(image_path)}")
            self.progress_var.set("正在调用API...")
            self.append_log("单图-开始调用API", {"image": os.path.basename(image_path), "model": self.config.get("selected_model", "doubao")})

            # 调用API
            result = self.call_api(image_path, prompt)

            if result.startswith("API调用失败") or result.startswith("API调用异常"):
                print("API调用失败")
                self.progress_var.set("分析失败")
                self.append_log("单图-失败", result[:2000])
            else:
                print("单图分析完成")
                self.single_result_text.insert(tk.END, result)
                self.progress_var.set("分析完成")
                self.append_log("单图-完成，返回文本长度", len(result))

        except Exception as e:
            print(f"处理异常: {str(e)}")
            self.progress_var.set("处理异常")
        finally:
            self.analyze_button.config(state="normal", text="🚀 开始分析")

    def start_batch_analysis(self):
        """开始批量分析"""
        # 验证输入
        selected_model = self.config.get("selected_model", "doubao")
        if selected_model == "doubao" and not self.config.get("doubao_api_key"):
            messagebox.showerror("错误", "请先在配置文件中配置豆包API Key")
            return
        elif selected_model == "autodl" and not self.config.get("autodl_api_key"):
            messagebox.showerror("错误", "请先配置 AutoDL API Key")
            return
        elif selected_model == "aliyun" and not self.config.get("aliyun_api_key"):
            messagebox.showerror("错误", "请先在配置文件中配置阿里云API Key")
            return

        folder_path = self.folder_entry.get().strip()
        if not folder_path or not os.path.exists(folder_path):
            messagebox.showerror("错误", "请选择有效的文件夹")
            return

        prompt = self._get_effective_prompt()
        if not prompt:
            messagebox.showerror("错误", "请输入系统提示词")
            return

        # 获取图片文件列表
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']
        image_files = []

        for file in os.listdir(folder_path):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(file)

        if not image_files:
            messagebox.showerror("错误", "文件夹中没有找到图片文件")
            return

        # 获取txt文件列表
        txt_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith('.txt'):
                txt_files.append(file)

        print(f"找到 {len(image_files)} 个图片文件")
        print(f"找到 {len(txt_files)} 个txt文件")

        # 检查图片数量和txt数量是否相同
        if len(image_files) == len(txt_files):
            # 图片数量和txt数量相同，询问是否覆盖
            result = messagebox.askyesno("文件覆盖确认", 
                                       f"检测到图片数量({len(image_files)})和txt数量({len(txt_files)})相同。\n\n是否覆盖现有的txt文件？\n\n选择'是'覆盖所有文件，选择'否'取消操作。",
                                       icon='warning', default='no')
            if not result:
                print("用户取消了批量处理")
                return
            else:
                print("用户确认覆盖现有文件，开始处理")
                self.process_mode = "overwrite_all"
        elif len(txt_files) > 0:
            # 存在txt文件但数量不同，询问处理方式
            result = messagebox.askyesno("处理方式选择", 
                                       f"检测到图片数量({len(image_files)})和txt数量({len(txt_files)})不同。\n\n是否仅处理无txt的图片？\n\n选择'是'仅处理无txt的图片，选择'否'全部重新覆盖处理。",
                                       icon='question', default='yes')
            if result:
                print("用户选择仅处理无txt的图片")
                self.process_mode = "process_missing_only"
            else:
                print("用户选择全部重新覆盖处理")
                self.process_mode = "overwrite_all"
        else:
            # 没有txt文件，直接开始处理
            print("没有发现txt文件，开始处理所有图片")
            self.process_mode = "process_all"

        # 根据处理模式决定要处理的文件
        files_to_process = []
        
        if self.process_mode == "process_missing_only":
            # 仅处理无txt的图片
            for image_file in image_files:
                name_without_ext = os.path.splitext(image_file)[0]
                txt_file = os.path.join(folder_path, f"{name_without_ext}.txt")
                if not os.path.exists(txt_file):
                    files_to_process.append(image_file)
            
            print(f"将处理 {len(files_to_process)} 个无txt的图片文件")
        else:
            # 处理所有图片（覆盖模式或全新处理）
            files_to_process = image_files
            print(f"将处理所有 {len(files_to_process)} 个图片文件")

        if not files_to_process:
            messagebox.showinfo("提示", "没有需要处理的文件")
            return

        # 确认批量处理
        if not messagebox.askyesno("确认", f"确定要开始批量分析 {len(files_to_process)} 个图片文件吗？"):
            return

        # 设置批量处理状态
        self.batch_processing = True
        self.stop_batch_processing = False

        # 更新按钮状态
        self.analyze_button.config(state="disabled", text="🔄 批量分析中...")
        self.stop_button.config(state="normal")

        # 清空之前的结果
        self.batch_result_text.delete(1.0, tk.END)

        # 在新线程中执行批量分析
        try:
            self.work_notebook.select(self.log_frame)
        except Exception:
            pass
        # 获取并发数
        try:
            concurrent_workers = int(self.concurrent_var.get())
        except:
            concurrent_workers = 2
        
        self.append_log("批量-开始", {
            "folder": folder_path, 
            "count": len(files_to_process), 
            "mode": self.process_mode, 
            "model": self.config.get("selected_model", "doubao"),
            "concurrent": concurrent_workers
        })
        threading.Thread(target=self._batch_analysis_worker, args=(folder_path, files_to_process, prompt, concurrent_workers), daemon=True).start()

    def _process_single_image(self, folder_path, image_file, prompt, index, total):
        """处理单个图片（用于并发处理）"""
        try:
            if self.stop_batch_processing:
                return False, image_file, "已停止"
            
            image_path = os.path.join(folder_path, image_file)
            print(f"[并发] 处理文件 {index}/{total}: {image_file}")
            self.append_log("批量-开始处理", {"index": index, "total": total, "file": image_file})

            # 调用API
            result = self.call_api(image_path, prompt)

            if result.startswith("API调用失败") or result.startswith("API调用异常"):
                print(f"[并发] 失败: {image_file} - {result[:100]}")
                return False, image_file, result
            else:
                # 保存结果到文件
                name_without_ext = os.path.splitext(image_file)[0]
                output_file = os.path.join(folder_path, f"{name_without_ext}.txt")
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result)
                    print(f"[并发] 成功: {image_file} - 结果已保存到 {output_file}")
                    return True, image_file, output_file
                except Exception as e:
                    error_msg = f"保存文件失败: {str(e)}"
                    print(f"[并发] {error_msg}")
                    return False, image_file, error_msg

        except Exception as e:
            error_msg = f"处理异常: {str(e)}"
            print(f"[并发] {error_msg}")
            return False, image_file, error_msg

    def _batch_analysis_worker(self, folder_path, image_files, prompt, concurrent_workers):
        """批量分析工作线程（支持并发）"""
        try:
            print(f"开始批量分析，共 {len(image_files)} 个文件，并发数: {concurrent_workers}")
            processed_count = 0
            failed_count = 0
            total_files = len(image_files)

            # 使用线程池进行并发处理
            with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
                # 提交所有任务
                future_to_file = {}
                for i, image_file in enumerate(image_files):
                    if self.stop_batch_processing:
                        break
                    future = executor.submit(self._process_single_image, folder_path, image_file, prompt, i+1, total_files)
                    future_to_file[future] = image_file

                # 处理完成的任务
                for future in as_completed(future_to_file):
                    if self.stop_batch_processing:
                        # 取消未完成的任务
                        for f in future_to_file:
                            if not f.done():
                                f.cancel()
                        break

                    image_file = future_to_file[future]
                    try:
                        success, file_name, result = future.result()
                        
                        with self.batch_lock:
                            if success is True:
                                # 成功处理
                                processed_count += 1
                                output_file = result
                                self.append_log("批量-成功", {"saved_to": output_file, "file": file_name})
                                
                                # 更新UI（线程安全）
                                self.root.after(0, lambda f=file_name, o=output_file, r=result: self._update_batch_result_ui(f, o, r, True))
                                
                            elif success is False:
                                # 处理失败
                                failed_count += 1
                                error_msg = result
                                self.append_log("批量-失败", {"file": file_name, "error": error_msg[:500]})
                                
                                # 更新UI（线程安全）
                                self.root.after(0, lambda f=file_name, e=error_msg: self._update_batch_result_ui(f, None, e, False))
                            
                            # 更新进度
                            current = processed_count + failed_count
                            progress_text = f"正在处理 {current}/{total_files} (成功: {processed_count}, 失败: {failed_count})"
                            self.root.after(0, lambda t=progress_text: self.progress_var.set(t))
                            
                    except Exception as e:
                        failed_count += 1
                        error_msg = f"获取结果异常: {str(e)}"
                        print(f"[并发] {error_msg}")
                        self.append_log("批量-异常", {"file": image_file, "error": error_msg})
                        self.root.after(0, lambda f=image_file, e=error_msg: self._update_batch_result_ui(f, None, e, False))

            # 处理完成
            if not self.stop_batch_processing:
                print(f"批量分析完成，成功处理 {processed_count} 个文件，失败 {failed_count} 个文件")
                final_text = f"批量分析完成 - 成功: {processed_count}/{total_files}, 失败: {failed_count}"
                self.root.after(0, lambda t=final_text: self.progress_var.set(t))
                self.append_log("批量-完成", {"success": processed_count, "failed": failed_count, "total": total_files})
            else:
                print(f"批量分析已停止 - 已处理 {processed_count} 个文件，失败 {failed_count} 个文件")
                final_text = f"批量分析已停止 - 已处理: {processed_count}/{total_files}, 失败: {failed_count}"
                self.root.after(0, lambda t=final_text: self.progress_var.set(t))
                self.append_log("批量-停止", {"success": processed_count, "failed": failed_count, "total": total_files})

        except Exception as e:
            error_msg = f"批量处理异常: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self.progress_var.set("批量处理异常"))
            self.append_log("批量-异常", {"error": error_msg})
        finally:
            # 恢复按钮状态
            self.batch_processing = False
            self.root.after(0, lambda: self.analyze_button.config(state="normal", text="🚀 开始分析"))
            self.root.after(0, lambda: self.stop_button.config(state="disabled"))

    def _update_batch_result_ui(self, file_name, output_file, result, success):
        """更新批量结果UI（线程安全）"""
        try:
            if success:
                self.batch_result_text.insert(tk.END, f"✅ {file_name} - 分析完成\n")
                if output_file:
                    self.batch_result_text.insert(tk.END, f"   保存位置: {output_file}\n")
                # result在成功时是output_file路径，不需要显示长度
                self.batch_result_text.insert(tk.END, "\n")
            else:
                self.batch_result_text.insert(tk.END, f"❌ {file_name} - 处理失败\n")
                if result:
                    error_msg = str(result)
                    error_preview = error_msg[:200] + ("..." if len(error_msg) > 200 else "")
                    self.batch_result_text.insert(tk.END, f"   错误: {error_preview}\n")
                self.batch_result_text.insert(tk.END, "\n")
            self.batch_result_text.see(tk.END)
        except Exception as e:
            print(f"更新UI失败: {str(e)}")

    def stop_processing(self):
        """停止批量处理"""
        if self.batch_processing:
            self.stop_batch_processing = True
            print("正在停止批量处理...")

    def clear_results(self):
        """清空结果"""
        self.single_result_text.delete(1.0, tk.END)
        self.batch_result_text.delete(1.0, tk.END)
        self.progress_var.set("就绪")
        print("结果已清空")

    def delete_all_txt_files(self):
        """删除文件夹中所有以.txt结尾的文件"""
        folder_path = self.folder_entry.get().strip()
        if not folder_path or not os.path.exists(folder_path):
            messagebox.showerror("错误", "请选择有效的文件夹")
            return

        txt_files_to_delete = []
        for file in os.listdir(folder_path):
            if file.lower().endswith('.txt'):
                txt_files_to_delete.append(os.path.join(folder_path, file))

        if not txt_files_to_delete:
            messagebox.showinfo("提示", "文件夹中没有找到.txt文件。")
            return

        if messagebox.askyesno("确认删除", f"确定要删除 {len(txt_files_to_delete)} 个.txt文件吗？"):
            for txt_file in txt_files_to_delete:
                try:
                    os.remove(txt_file)
                    print(f"已删除文件: {txt_file}")
                except Exception as e:
                    print(f"删除文件失败: {txt_file} - {e}")
            messagebox.showinfo("提示", f"已删除 {len(txt_files_to_delete)} 个.txt文件。")
            self.batch_result_text.delete(1.0, tk.END) # 清空结果文本框
            self.progress_var.set("就绪 - 请选择包含图片的文件夹") # 更新进度提示


def main():
    """主函数"""
    import sys
    import os
    
    # 在Windows下，如果是双击运行，确保窗口不会立即关闭
    if sys.platform == 'win32':
        # 尝试重定向输出到控制台（如果是从文件管理器双击运行）
        try:
            # 尝试附加到现有控制台
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.AllocConsole()
            sys.stdout = open('CONOUT$', 'w', encoding='utf-8')
            sys.stderr = open('CONOUT$', 'w', encoding='utf-8')
            sys.stdin = open('CONIN$', 'r', encoding='utf-8')
        except:
            pass
    
    print("=" * 60)
    print("单图分析打标工具 - 启动中...")
    print("=" * 60)
    
    root = None
    try:
        print("[1/5] 检查依赖库...")
        # 检查已导入的库
        try:
            import tkinter
            print("  ✓ tkinter: 已导入")
        except:
            print("  ✗ tkinter: 未导入")
        
        try:
            from PIL import Image
            print("  ✓ PIL/Pillow: 已导入")
        except:
            print("  ✗ PIL/Pillow: 未导入 (请运行: pip install pillow)")
        
        try:
            import requests
            print("  ✓ requests: 已导入")
        except:
            print("  ✗ requests: 未导入 (请运行: pip install requests)")
        
        print(f"  {'✓' if DND_AVAILABLE else '✗ (可选)'} tkinterdnd2: {'已导入' if DND_AVAILABLE else '未安装 (可选)'}")
        
        print("[2/5] 初始化窗口...")
        # 如果支持拖拽功能，使用TkinterDnD
        if DND_AVAILABLE and TkinterDnD:
            try:
                root = TkinterDnD.Tk()
                print("  ✓ 拖拽功能已启用")
            except Exception as e:
                print(f"  ⚠ 无法初始化拖拽功能: {e}")
                root = tk.Tk()
                print("  ✓ 使用标准Tkinter窗口")
        else:
            root = tk.Tk()
            if not DND_AVAILABLE:
                print("  ⚠ tkinterdnd2 未安装，拖拽功能不可用")
            else:
                print("  ✓ 使用标准Tkinter窗口")
        
        print("[3/5] 创建应用程序实例...")
        try:
            app = ImageAnalysisTool(root)
            print("  ✓ 应用程序初始化成功")
        except Exception as e:
            print(f"  ❌ 应用程序初始化失败: {e}")
            import traceback
            traceback.print_exc()
            # 尝试显示错误对话框
            try:
                messagebox.showerror("初始化错误", 
                                   f"程序初始化失败:\n\n{str(e)}\n\n"
                                   "详细信息请查看控制台输出")
            except:
                pass
            print("\n" + "=" * 60)
            input("按回车键退出...")
            return
        
        print("[4/5] 准备显示窗口...")
        print("  ✓ 所有初始化完成")
        
        print("[5/5] 启动主循环...")
        print("=" * 60)
        print("程序运行中，关闭窗口或按Ctrl+C退出")
        print("=" * 60)
        
        try:
            root.mainloop()
        except Exception as e:
            print(f"\n程序运行时出错: {e}")
            import traceback
            traceback.print_exc()
            input("按回车键退出...")
        
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        print("请确保已安装所有必需的依赖库:")
        print("  pip install pillow requests")
        if "tkinterdnd2" in str(e).lower():
            print("  pip install tkinterdnd2")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
    except Exception as e:
        print(f"\n❌ 程序启动失败: {e}")
        print("\n详细错误信息:")
        import traceback
        traceback.print_exc()
        
        # 尝试显示错误消息框
        if root:
            try:
                import tkinter.messagebox as msgbox
                msgbox.showerror("启动错误", 
                               f"程序启动失败:\n\n{str(e)}\n\n"
                               "详细信息请查看控制台输出")
            except:
                pass
        
        print("\n" + "=" * 60)
        input("按回车键退出...")


if __name__ == "__main__":
    main()
