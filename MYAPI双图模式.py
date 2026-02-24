import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import json
import os
import sys
import threading
from PIL import Image, ImageTk
import re
import datetime
import base64

# 确保工作目录为脚本所在目录（解决双击运行时找不到配置文件的问题）
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe文件
    script_dir = os.path.dirname(sys.executable)
else:
    # 如果是.py文件
    script_dir = os.path.dirname(os.path.abspath(__file__))

# 切换到脚本所在目录
os.chdir(script_dir)


def _filter_siliconflow_box(text):
    """过滤硅基流动模型输出的 <|begin_of_box|> 和 <|end_of_box|> 标记"""
    if not text or not isinstance(text, str):
        return text
    text = re.sub(r'^\s*<\|begin_of_box\|>\s*', '', text)
    text = re.sub(r'\s*<\|end_of_box\|>\s*$', '', text)
    return text

# 依赖检测和自动安装函数（使用当前解释器，bat 已负责激活环境）
def check_and_install_dependencies():
    """检测并自动安装缺失的依赖"""
    try:
        import subprocess
    except ImportError:
        print("警告: 无法检测依赖，请手动安装依赖库")
        return True
    
    python_exe = sys.executable  # 使用当前解释器（bat 已激活 Conda/venv）
    
    requirements_file = os.path.join(script_dir, "requirements.txt")
    if not os.path.exists(requirements_file):
        print("警告: requirements.txt 不存在，跳过依赖检测")
        return True
    
    missing_packages = []
    required_packages = []
    package_to_module = {
        'Pillow': 'PIL',
        'google-genai': 'google.genai',
        'tkinterdnd2': 'tkinterdnd2',
    }
    
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                package_name = line.split('>=')[0].split('==')[0].split('<=')[0].split('>')[0].split('<')[0].split('!')[0].split('[')[0].strip()
                required_packages.append((package_name, line))
    except Exception as e:
        print(f"读取requirements.txt失败: {e}")
        return True
    
    print("检测依赖库...")
    for package_name, full_spec in required_packages:
        try:
            module_name = package_to_module.get(package_name, package_name)
            check_result = subprocess.run(
                [python_exe, '-c', f'import {module_name}'],
                capture_output=True, timeout=10
            )
            if check_result.returncode == 0:
                print(f"  ✓ {package_name}: 已安装")
            else:
                missing_packages.append(full_spec)
                print(f"  ✗ {package_name}: 未安装")
        except Exception as e:
            missing_packages.append(full_spec)
            print(f"  ✗ {package_name}: 检测失败 ({str(e)[:50]})")
    
    if missing_packages:
        print(f"\n检测到 {len(missing_packages)} 个缺失的依赖包")
        print("正在自动安装缺失的依赖...")
        print("=" * 60)
        try:
            for package in missing_packages:
                print(f"正在安装: {package}")
                result = subprocess.run(
                    [python_exe, '-m', 'pip', 'install', package],
                    capture_output=True, text=True, timeout=300
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
            print("=" * 60)
        except Exception as e:
            print(f"自动安装失败: {e}")
            print(f"\n请手动运行: {python_exe} -m pip install {' '.join(missing_packages)}")
    else:
        print("所有依赖已安装 ✓")
    return True

# 检测并安装依赖
if __name__ == "__main__" or True:
    print("=" * 60)
    print("图片对比工具 - 依赖检测")
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

class ImageComparisonTool:
    def __init__(self, root):
        self.root = root
        self.root.title("双图对比分析打标工具 - 多模型支持  作者: zealman")
        self.root.geometry("1100x860")
        self.root.minsize(1000, 860)
        
        # 加载自定义字体
        self.load_custom_font()
        
        # 设置窗口居中
        self.center_window()
        
        # 设置样式
        self.setup_styles()
        
        # 加载配置
        self.config = self.load_config()
        
        # 模型配置
        self.selected_model = "doubao"

        # 批量处理控制标志
        self.batch_processing = False
        self.stop_batch_processing = False
        
        # 批量处理状态管理
        self.batch_processed_files = []  # 已处理的文件列表
        self.batch_current_index = 0     # 当前处理位置
        self.batch_total_files = 0       # 总文件数量
        self.batch_folders = {"a": "", "b": ""}  # 保存的文件夹路径
        self.process_mode = "process_all"  # 处理模式：process_all, process_missing_only, overwrite_all
        
        # 创建界面
        self.create_widgets()
        
        # 加载保存的配置
        self.load_saved_config()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 初始化批量处理按钮状态
        self.update_batch_buttons_state()
    
    def load_custom_font(self):
        """加载自定义字体"""
        try:
            # 尝试使用系统字体
            self.custom_font = "Microsoft YaHei"
        except:
            self.custom_font = "Arial"
    
    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
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

        # 修复LabelFrame样式
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
        """加载配置（公共 API 配置 + 双图模式独立配置）"""
        try:
            import config_api
            config = {}
            config.update(config_api.load_api_config())
            config.update(config_api.load_shuang_config())
            return config
        except ImportError:
            return self._load_config_legacy()

    def _load_config_legacy(self):
        """旧版单文件配置加载（兼容）"""
        default = {
            "selected_model": "doubao",
            "doubao_api_key": "", "doubao_model": "doubao-1-5-thinking-vision-pro-250428",
            "siliconflow_api_key": "", "siliconflow_model": "zai-org/GLM-4.5",
            "xai_api_key": "", "xai_model": "grok-2-vision-1212",
            "aliyun_api_key": "", "aliyun_model": "qwen-vl-plus",
            "system_prompt": "请对比这两张图片，详细描述它们的差异和相似之处。",
            "single_mode": {"image_a": "", "image_b": ""},
            "batch_mode": {"folder_a": "", "folder_b": ""},
        }
        try:
            with open("config-shuang.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in default.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception as e:
            print(f"加载配置失败: {e}")
            return default

    def save_config(self):
        """保存配置到 config-api.json 和 config-shuang.json"""
        try:
            import config_api
            config_api.save_api_config(self.config)
            config_api.save_shuang_config(self.config)
        except ImportError:
            with open("config-shuang.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
    
    def load_saved_config(self):
        """加载保存的配置到界面"""
        # 设置选中的模型
        self.model_var.set(self.config.get("selected_model", "doubao"))
        
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(1.0, self.config.get("system_prompt", ""))
        if hasattr(self, 'supplement_vars'):
            for key, var in self.supplement_vars.items():
                var.set(self.config.get(key, key != "prompt_supplement_4"))
        
        # 加载单例模式配置
        if self.config.get("single_mode"):
            image_a_path = self.config["single_mode"].get("image_a", "")
            image_b_path = self.config["single_mode"].get("image_b", "")
            
            if image_a_path:
                self.image_a_entry.delete(0, tk.END)
                self.image_a_entry.insert(0, image_a_path)
                # 如果文件存在，更新预览
                if os.path.exists(image_a_path):
                    self.update_image_preview(image_a_path, self.image_a_preview)
            
            if image_b_path:
                self.image_b_entry.delete(0, tk.END)
                self.image_b_entry.insert(0, image_b_path)
                # 如果文件存在，更新预览
                if os.path.exists(image_b_path):
                    self.update_image_preview(image_b_path, self.image_b_preview)
        
        # 加载批量模式配置
        if self.config.get("batch_mode"):
            self.folder_a_entry.delete(0, tk.END)
            self.folder_a_entry.insert(0, self.config["batch_mode"].get("folder_a", ""))
            self.folder_b_entry.delete(0, tk.END)
            self.folder_b_entry.insert(0, self.config["batch_mode"].get("folder_b", ""))
        
        # 更新模型名称显示和颜色
        self.update_model_names()
        # 确保颜色更新在模型名称更新之后
        self.root.after(100, self.update_model_colors)
        
        # 延迟加载图片和更新UI状态
        self.root.after(200, self.load_saved_images_and_txt)

    def update_model_names(self):
        """更新模型名称显示"""
        try:
            # 获取模型名称用于显示
            doubao_name = self.config.get("doubao_model", "doubao-1-5-thinking-vision-pro-250428")
            siliconflow_name = self.config.get("siliconflow_model", "zai-org/GLM-4.5")
            xai_name = self.config.get("xai_model", "grok-2-vision-1212")
            gptsapi_name = self.config.get("gptsapi_model", "gemini-3.1-pro-preview")
            aliyun_name = self.config.get("aliyun_model", "qwen-vl-plus")
            
            # 更新单选按钮的显示文本
            self.doubao_check.config(text=f"豆包 ({doubao_name})")
            self.siliconflow_check.config(text=f"硅基流动 ({siliconflow_name})")
            self.aliyun_check.config(text=f"阿里云 ({aliyun_name})")
            self.xai_check.config(text=f"XAI ({xai_name})")
            self.gptsapi_check.config(text=f"GPTsAPI ({gptsapi_name})")
            
            # 更新选中状态的文字颜色
            self.update_model_colors()
        except Exception as e:
            print(f"更新模型名称显示失败: {e}")
            import traceback
            traceback.print_exc()

    def update_model_colors(self):
        """更新模型选择按钮的颜色"""
        try:
            selected_model = self.model_var.get()
            print(f"当前选中的模型: {selected_model}")
            
            # 使用样式来设置颜色
            style = ttk.Style()
            
            # 重置所有按钮为默认颜色
            style.configure('Doubao.TRadiobutton', foreground='black')
            style.configure('Siliconflow.TRadiobutton', foreground='black')
            style.configure('Aliyun.TRadiobutton', foreground='black')
            style.configure('XAI.TRadiobutton', foreground='black')
            style.configure('GPTsAPI.TRadiobutton', foreground='black')
            
            # 设置选中按钮为绿色
            if selected_model == "doubao":
                print("设置豆包按钮为绿色")
                style.configure('Doubao.TRadiobutton', foreground='green')
                self.doubao_check.configure(style='Doubao.TRadiobutton')
            elif selected_model == "siliconflow":
                print("设置硅基流动按钮为绿色")
                style.configure('Siliconflow.TRadiobutton', foreground='green')
                self.siliconflow_check.configure(style='Siliconflow.TRadiobutton')
            elif selected_model == "xai":
                print("设置XAI按钮为绿色")
                style.configure('XAI.TRadiobutton', foreground='green')
                self.xai_check.configure(style='XAI.TRadiobutton')
            elif selected_model == "gptsapi":
                print("设置GPTsAPI按钮为绿色")
                style.configure('GPTsAPI.TRadiobutton', foreground='green')
                self.gptsapi_check.configure(style='GPTsAPI.TRadiobutton')
            elif selected_model == "aliyun":
                print("设置阿里云按钮为绿色")
                style.configure('Aliyun.TRadiobutton', foreground='green')
                self.aliyun_check.configure(style='Aliyun.TRadiobutton')
            
            print("颜色更新完成")
        except Exception as e:
            print(f"更新模型颜色失败: {e}")
            import traceback
            traceback.print_exc()
    
    def load_saved_images_and_txt(self):
        """加载保存的图片和TXT内容，更新UI状态"""
        try:
            # 检查单例模式下的图片路径
            image_a_path = self.image_a_entry.get().strip()
            image_b_path = self.image_b_entry.get().strip()
            
            # 如果两个路径都存在且文件存在，更新预览和状态
            if image_a_path and image_b_path and os.path.exists(image_a_path) and os.path.exists(image_b_path):
                print(f"加载保存的图片路径: A={os.path.basename(image_a_path)}, B={os.path.basename(image_b_path)}")
                
                # 更新图片预览
                self.update_image_preview(image_a_path, self.image_a_preview)
                self.update_image_preview(image_b_path, self.image_b_preview)
                
                # 更新切换按钮状态
                self.update_switch_buttons_state()
            else:
                # 如果保存的路径不存在，清空输入框
                if image_a_path and not os.path.exists(image_a_path):
                    print(f"保存的图片A路径不存在: {image_a_path}")
                    self.image_a_entry.delete(0, tk.END)
                    self.image_a_preview.configure(image="", text="点击选择图片A")
                
                if image_b_path and not os.path.exists(image_b_path):
                    print(f"保存的图片B路径不存在: {image_b_path}")
                    self.image_b_entry.delete(0, tk.END)
                    self.image_b_preview.configure(image="", text="点击选择图片B")
                
        except Exception as e:
            print(f"加载保存的图片时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def on_model_change(self):
        """处理模型选择变化"""
        print("模型选择发生变化")
        # 更新颜色显示
        self.update_model_colors()
        # 自动保存配置
        self.auto_save_config()

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
            self.config["selected_model"] = self.model_var.get()
            self.config["system_prompt"] = self.prompt_text.get(1.0, tk.END).strip()
            if hasattr(self, 'supplement_vars'):
                for key, var in self.supplement_vars.items():
                    self.config[key] = var.get()

            # 检查当前选中的TAB来判断模式
            current_tab = self.work_notebook.tab(self.work_notebook.select(), "text")
            if "单例模式" in current_tab:
                # 保存图片路径
                if not self.config.get("single_mode"):
                    self.config["single_mode"] = {}
                self.config["single_mode"]["image_a"] = self.image_a_entry.get()
                self.config["single_mode"]["image_b"] = self.image_b_entry.get()
            elif "批量模式" in current_tab:
                self.config["batch_mode"]["folder_a"] = self.folder_a_entry.get()
                self.config["batch_mode"]["folder_b"] = self.folder_b_entry.get()

            self.save_config()
            # 不显示日志消息，避免频繁提示
        except Exception as e:
            # 如果自动保存失败，记录错误但不中断程序
            print(f"自动保存配置失败: {e}")

    def create_widgets(self):
        """创建现代化GUI界面"""
        # 主滚动框架
        self.create_scrollable_frame()
        
        # 标题区域
        self.create_header()
        
        # 配置区域
        self.create_config_section()
        
        # 模式选择区域
        self.create_mode_section()
        
        # 工作区域
        self.create_work_section()
        
        # 操作按钮区域
        self.create_action_section()
        
        # 底部信息区域
        self.create_info_section()

        # 绑定拖拽事件（延迟执行，确保所有组件都已创建）
        self.root.after(100, self.setup_drag_drop)
    
    def create_scrollable_frame(self):
        """创建主框架（移除滚动功能）"""
        # 创建主容器，直接使用Frame而不是滚动容器
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        # 配置主框架的列权重，让内容可以水平扩展
        self.main_frame.columnconfigure(0, weight=1)
        # 配置主框架的行权重，让配置区域可以垂直扩展
        self.main_frame.rowconfigure(1, weight=1)
    
    def create_header(self):
        """创建标题区域"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        header_frame.columnconfigure(0, weight=1)

        # 主标题
        title_label = ttk.Label(header_frame, text="双图对比分析打标工具", style='Title.TLabel')
        title_label.grid(row=0, column=0)

        # 分隔线
        separator = ttk.Separator(header_frame, orient='horizontal')
        separator.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(8, 0))
    
    def create_config_section(self):
        """创建配置区域"""
        config_frame = ttk.Frame(self.main_frame)
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 12))
        config_frame.columnconfigure(1, weight=1)
        # 修正行权重：第2行（系统提示词）应该有权重，第0、1行（模型选择）固定高度
        config_frame.rowconfigure(2, weight=1)

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
        
        self.siliconflow_check = ttk.Radiobutton(model_frame_1, text="硅基流动", variable=self.model_var, value="siliconflow", command=self.on_model_change)
        self.siliconflow_check.pack(side=tk.LEFT, padx=(0, 15))
        
        self.aliyun_check = ttk.Radiobutton(model_frame_1, text="阿里云", variable=self.model_var, value="aliyun", command=self.on_model_change)
        self.aliyun_check.pack(side=tk.LEFT, padx=(0, 15))
        
        # 第二行：国外模型
        model_frame_2 = ttk.Frame(config_frame)
        model_frame_2.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 8), pady=(0, 0))
        model_frame_2.configure(height=30)  # 固定高度
        
        self.xai_check = ttk.Radiobutton(model_frame_2, text="XAI", variable=self.model_var, value="xai", command=self.on_model_change)
        self.xai_check.pack(side=tk.LEFT, padx=(0, 15))
        
        self.gptsapi_check = ttk.Radiobutton(model_frame_2, text="GPTsAPI", variable=self.model_var, value="gptsapi", command=self.on_model_change)
        self.gptsapi_check.pack(side=tk.LEFT, padx=(0, 15))

        # 系统提示词配置
        ttk.Label(config_frame, text="系统提示词:", font=(self.custom_font, 9)).grid(row=2, column=0, sticky=(tk.W, tk.N), padx=(8, 5), pady=(5, 0))
        
        # 创建可调整大小的提示词输入框
        prompt_frame = ttk.Frame(config_frame)
        prompt_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 8), pady=5)
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
        supplement_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(0, 8), pady=(0, 4))  # 与提示词输入框左对齐
        supplement_frame.columnconfigure(4, weight=1)  # 空白列吸收益出空间
        self.supplement_vars = {}
        for i, (text, key) in enumerate(supplement_texts):
            var = tk.BooleanVar(value=self.config.get(key, key != "prompt_supplement_4"))
            self.supplement_vars[key] = var
            cb = ttk.Checkbutton(supplement_frame, text=text, variable=var, command=self.auto_save_config)
            cb.grid(row=0, column=i, sticky=tk.W, padx=(0, 12))
        self._supplement_items = supplement_texts
    
    def create_mode_section(self):
        """创建模式选择区域 - 现在使用TAB样式"""
        # 创建工作区域的TAB容器
        self.work_notebook = ttk.Notebook(self.main_frame)
        self.work_notebook.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 12))

        # 创建单例模式TAB
        self.single_frame = ttk.Frame(self.work_notebook)
        self.work_notebook.add(self.single_frame, text="🖼️ 单例模式")

        # 创建批量模式TAB
        self.batch_frame = ttk.Frame(self.work_notebook)
        self.work_notebook.add(self.batch_frame, text="📁 批量模式")

        # 创建处理日志TAB
        self.log_frame = ttk.Frame(self.work_notebook)
        self.work_notebook.add(self.log_frame, text="📝 处理日志")

        # 绑定TAB切换事件
        self.work_notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
    
    def create_work_section(self):
        """创建工作区域内容"""
        # 创建单例模式内容
        self.create_single_mode_content()

        # 创建批量模式内容
        self.create_batch_mode_content()

        # 创建处理日志内容
        self.create_log_tab_content()

    def create_single_mode_content(self):
        """创建单例模式TAB内容"""
        # 创建主容器，包含图片区域和按钮区域
        main_container = ttk.Frame(self.single_frame)
        main_container.pack(fill="both", expand=True, padx=12, pady=12)
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)  # 结果预览区域列权重

        # 创建两列布局：左侧图片选择，右侧结果预览
        images_container = ttk.Frame(main_container)
        images_container.grid(row=0, column=0, sticky=(tk.W, tk.E))
        images_container.columnconfigure(0, weight=1)
        images_container.columnconfigure(1, weight=1)
        images_container.columnconfigure(2, weight=0)  # 按钮列

        # 图片A区域
        image_a_frame = ttk.LabelFrame(images_container, text="图片 A", padding="10")
        image_a_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 6))
        image_a_frame.columnconfigure(0, weight=1)

        # 图片A选择
        a_select_frame = ttk.Frame(image_a_frame)
        a_select_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        a_select_frame.columnconfigure(0, weight=1)

        self.image_a_entry = ttk.Entry(a_select_frame, font=(self.custom_font, 8))
        self.image_a_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 6))
        # 绑定失去焦点事件，自动保存配置
        self.image_a_entry.bind("<FocusOut>", lambda e: self.auto_save_config())

        ttk.Button(a_select_frame, text="选择文件", command=self.browse_image_a,
                  style='Custom.TButton').grid(row=0, column=1)

        # 图片A预览
        self.image_a_preview = ttk.Label(image_a_frame, text="点击选择图片A",
                                        background='#f8f9fa', relief='ridge',
                                        anchor='center', padding=12)
        self.image_a_preview.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        self.image_a_preview.configure(width=25)  # 限制预览区域宽度

        # 图片B区域
        image_b_frame = ttk.LabelFrame(images_container, text="图片 B", padding="10")
        image_b_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(6, 12))
        image_b_frame.columnconfigure(0, weight=1)

        # 图片B选择
        b_select_frame = ttk.Frame(image_b_frame)
        b_select_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        b_select_frame.columnconfigure(0, weight=1)

        self.image_b_entry = ttk.Entry(b_select_frame, font=(self.custom_font, 8))
        self.image_b_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 6))
        # 绑定失去焦点事件，自动保存配置
        self.image_b_entry.bind("<FocusOut>", lambda e: self.auto_save_config())

        ttk.Button(b_select_frame, text="选择文件", command=self.browse_image_b,
                  style='Custom.TButton').grid(row=0, column=1)

        # 图片B预览
        self.image_b_preview = ttk.Label(image_b_frame, text="点击选择图片B",
                                        background='#f8f9fa', relief='ridge',
                                        anchor='center', padding=12)
        self.image_b_preview.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 6))
        self.image_b_preview.configure(width=25)  # 限制预览区域宽度

        # 右侧按钮区域
        button_frame = ttk.Frame(images_container)
        button_frame.grid(row=0, column=2, sticky=(tk.N, tk.S), padx=(12, 0))

        # 开始对比分析按钮
        self.generate_button = ttk.Button(button_frame, text="🚀 开始对比分析",
                                         command=self.generate_comparison,
                                         style='Action.TButton')
        self.generate_button.pack(anchor='n', pady=(20, 0))

        # 图片切换按钮区域
        switch_frame = ttk.Frame(button_frame)
        switch_frame.pack(anchor='n', pady=(15, 0))
        
        # 上一张按钮
        self.prev_button = ttk.Button(switch_frame, text="⬅️ 上一张",
                                     command=self.switch_to_previous,
                                     style='Custom.TButton',
                                     state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 下一张按钮
        self.next_button = ttk.Button(switch_frame, text="下一张 ➡️",
                                     command=self.switch_to_next,
                                     style='Custom.TButton',
                                     state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT)

        # 进度状态
        self.progress_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(button_frame, textvariable=self.progress_var,
                                     style='Info.TLabel')
        self.status_label.pack(anchor='n', pady=(10, 0))

        # 右侧结果预览区域
        result_preview_frame = ttk.LabelFrame(main_container, text="📄 分析结果预览")
        result_preview_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(12, 0), pady=0)
        result_preview_frame.columnconfigure(0, weight=1)
        result_preview_frame.rowconfigure(0, weight=1)

        self.single_result_text = scrolledtext.ScrolledText(result_preview_frame, height=15, font=(self.custom_font, 9), wrap=tk.WORD)
        self.single_result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=8, pady=8)
    
    def create_batch_mode_content(self):
        """创建批量模式TAB内容"""
        # 创建主容器
        main_container = ttk.Frame(self.batch_frame)
        main_container.pack(fill="both", expand=True, padx=12, pady=12)
        main_container.columnconfigure(0, weight=1)

        # 目录选择区域
        dirs_container = ttk.Frame(main_container)
        dirs_container.grid(row=0, column=0, sticky=(tk.W, tk.E))
        dirs_container.columnconfigure(0, weight=1)
        dirs_container.columnconfigure(1, weight=0)  # 按钮列

        # 目录选择
        dirs_frame = ttk.Frame(dirs_container)
        dirs_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 12))
        dirs_frame.columnconfigure(1, weight=1)

        # 目录A
        ttk.Label(dirs_frame, text="图片A目录:", font=(self.custom_font, 9, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 8), pady=(0, 8))

        folder_a_frame = ttk.Frame(dirs_frame)
        folder_a_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 8))
        folder_a_frame.columnconfigure(0, weight=1)

        self.folder_a_entry = ttk.Entry(folder_a_frame, font=(self.custom_font, 8))
        self.folder_a_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 6))
        # 绑定失去焦点事件，自动保存配置
        self.folder_a_entry.bind("<FocusOut>", lambda e: self.auto_save_config())

        ttk.Button(folder_a_frame, text="选择目录", command=self.browse_folder_a,
                  style='Custom.TButton').grid(row=0, column=1)

        # 目录B
        ttk.Label(dirs_frame, text="图片B目录:", font=(self.custom_font, 9, 'bold')).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 8))

        folder_b_frame = ttk.Frame(dirs_frame)
        folder_b_frame.grid(row=1, column=1, sticky=(tk.W, tk.E))
        folder_b_frame.columnconfigure(0, weight=1)

        self.folder_b_entry = ttk.Entry(folder_b_frame, font=(self.custom_font, 8))
        self.folder_b_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 6))
        # 绑定失去焦点事件，自动保存配置
        self.folder_b_entry.bind("<FocusOut>", lambda e: self.auto_save_config())

        ttk.Button(folder_b_frame, text="选择目录", command=self.browse_folder_b,
                  style='Custom.TButton').grid(row=0, column=1)

        # 批量处理说明
        batch_info = ttk.Label(dirs_frame,
                              text="💡 批量模式将自动匹配同名文件进行对比，结果保存为txt文件\n选择A文件夹时会自动检测对应的B文件夹",
                              style='Subtitle.TLabel')
        batch_info.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        # 右侧按钮区域
        button_frame = ttk.Frame(dirs_container)
        button_frame.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 开始批量处理按钮
        self.batch_generate_button = ttk.Button(button_frame, text="🚀 开始批量处理",
                                               command=self.handle_batch_button_click,
                                               style='Action.TButton')
        self.batch_generate_button.pack(anchor='n', pady=(20, 0))

        # 删除所有txt按钮
        self.delete_txt_button = ttk.Button(button_frame, text="🗑️ 删除TXT",
                                           command=self.delete_all_txt_files,
                                           style='Custom.TButton')
        self.delete_txt_button.pack(anchor='n', pady=(10, 0))

        # 进度状态（批量模式共享相同的状态变量）
        self.batch_status_label = ttk.Label(button_frame, textvariable=self.progress_var,
                                           style='Info.TLabel')
        self.batch_status_label.pack(anchor='n', pady=(10, 0))

    def create_log_tab_content(self):
        """创建处理日志TAB内容"""
        try:
            # 主容器
            log_container = ttk.Frame(self.log_frame)
            log_container.pack(fill="both", expand=True, padx=12, pady=12)
            log_container.columnconfigure(0, weight=1)
            log_container.rowconfigure(0, weight=1)

            # 日志文本区
            self.log_text = scrolledtext.ScrolledText(log_container, height=20, font=(self.custom_font, 9), wrap=tk.WORD)
            self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            # 操作按钮行
            btn_frame = ttk.Frame(log_container)
            btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(8, 0))

            clear_btn = ttk.Button(btn_frame, text="清空日志", command=self.clear_log, style='Custom.TButton')
            clear_btn.pack(side=tk.LEFT)

            copy_btn = ttk.Button(btn_frame, text="复制全部", command=self.copy_log, style='Custom.TButton')
            copy_btn.pack(side=tk.LEFT, padx=(8, 0))

            # 初始提示
            self.append_log("日志系统已就绪")
        except Exception as e:
            print(f"创建日志TAB失败: {str(e)}")

    def _sanitize_log_text(self, text):
        """移除不需要展示的响应元数据字段"""
        try:
            if not isinstance(text, str):
                text = str(text)
            # 优先按JSON移除字段
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

            # 文本模式，正则移除相关字段/块
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

            # 控制台输出
            print(full_text)

            # GUI线程安全更新
            def _do_append():
                try:
                    if hasattr(self, 'log_text') and self.log_text:
                        self.log_text.insert(tk.END, full_text + "\n")
                        self.log_text.see(tk.END)
                except Exception as _:
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
    
    def create_action_section(self):
        """创建操作按钮区域 - 现在按钮已移到TAB中"""
        pass  # 按钮现在在各个TAB中
    
    def create_info_section(self):
        """创建底部信息区域（简化版）"""
        info_frame = ttk.Frame(self.main_frame)
        info_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 12))

        # 进度显示
        self.progress_var = tk.StringVar(value="就绪 - 请选择图片进行对比")
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

            # 为图片A输入框设置拖拽
            if hasattr(self.image_a_entry, 'drop_target_register'):
                self.image_a_entry.drop_target_register(DND_FILES)
                self.image_a_entry.dnd_bind('<<Drop>>', self.on_image_a_drop)

            # 为图片B输入框设置拖拽
            if hasattr(self.image_b_entry, 'drop_target_register'):
                self.image_b_entry.drop_target_register(DND_FILES)
                self.image_b_entry.dnd_bind('<<Drop>>', self.on_image_b_drop)

            # 为图片A预览区域设置拖拽
            if hasattr(self.image_a_preview, 'drop_target_register'):
                self.image_a_preview.drop_target_register(DND_FILES)
                self.image_a_preview.dnd_bind('<<Drop>>', self.on_image_a_drop)

            # 为图片B预览区域设置拖拽
            if hasattr(self.image_b_preview, 'drop_target_register'):
                self.image_b_preview.drop_target_register(DND_FILES)
                self.image_b_preview.dnd_bind('<<Drop>>', self.on_image_b_drop)

            # 为整个窗口设置拖拽作为备用
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_window_drop)

            print("拖拽功能已启用")
        except Exception as e:
            print(f"拖拽功能设置失败: {str(e)}")

        # 为预览区域添加点击事件，方便用户选择图片
        self.image_a_preview.bind("<Button-1>", lambda e: self.browse_image_a())
        self.image_b_preview.bind("<Button-1>", lambda e: self.browse_image_b())
        
        # 添加提示文本
        self.image_a_preview.configure(text="点击此处选择图片A\n(会自动检测B文件夹)\n或直接拖拽图片到此处")
        self.image_b_preview.configure(text="点击此处选择图片B\n或直接拖拽图片到此处")
    
    def on_image_a_drop(self, event):
        """处理图片A拖拽事件"""
        try:
            # 获取拖拽的文件路径
            files = self.parse_drop_files(event.data)
            if not files:
                return

            # 取第一个文件
            file_path = files[0]

            # 检查是否为图片文件
            if self.is_image_file(file_path):
                self.image_a_entry.delete(0, tk.END)
                self.image_a_entry.insert(0, file_path)
                self.update_image_preview(file_path, self.image_a_preview)
                print(f"已拖入图片A: {os.path.basename(file_path)}")
                
                # 尝试自动检测和加载对应的图片B
                self.auto_detect_image_b(file_path)
                
                # 更新切换按钮状态
                self.update_switch_buttons_state()
            else:
                print("拖入的文件不是支持的图片格式")

        except Exception as e:
            print(f"处理拖拽文件时出错: {str(e)}")

    def on_image_b_drop(self, event):
        """处理图片B拖拽事件"""
        try:
            # 获取拖拽的文件路径
            files = self.parse_drop_files(event.data)
            if not files:
                return

            # 取第一个文件
            file_path = files[0]

            # 检查是否为图片文件
            if self.is_image_file(file_path):
                self.image_b_entry.delete(0, tk.END)
                self.image_b_entry.insert(0, file_path)
                self.update_image_preview(file_path, self.image_b_preview)
                print(f"已拖入图片B: {os.path.basename(file_path)}")
                
                # 更新切换按钮状态
                self.update_switch_buttons_state()
            else:
                print("拖入的文件不是支持的图片格式")

        except Exception as e:
            print(f"处理拖拽文件时出错: {str(e)}")

    def on_window_drop(self, event):
        """处理窗口拖拽事件"""
        try:
            # 获取当前选中的标签页
            current_tab = self.work_notebook.tab(self.work_notebook.select(), "text")

            if "单例模式" in current_tab:
                # 单例模式，处理为图片A拖拽
                self.on_image_a_drop(event)
            else:
                # 批量模式，处理为文件夹拖拽
                self.on_folder_drop(event)

        except Exception as e:
            print(f"处理窗口拖拽时出错: {str(e)}")

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
                self.folder_a_entry.delete(0, tk.END)
                self.folder_a_entry.insert(0, path)
                # 保存配置
                self.config["batch_mode"]["folder_a"] = path
                self.save_config()
                print(f"已拖入文件夹A: {os.path.basename(path)}")
                
                # 尝试自动检测对应的B文件夹
                self.auto_detect_folder_b(path)
            elif self.is_image_file(path):
                # 如果拖入的是图片文件，则使用其所在目录
                folder_path = os.path.dirname(path)
                self.folder_a_entry.delete(0, tk.END)
                self.folder_a_entry.insert(0, folder_path)
                self.config["batch_mode"]["folder_a"] = folder_path
                self.save_config()
                print(f"已拖入图片文件，使用其所在目录: {os.path.basename(folder_path)}")
                
                # 尝试自动检测对应的B文件夹
                self.auto_detect_folder_b(folder_path)
            else:
                print("请拖入文件夹或图片文件")

        except Exception as e:
            print(f"处理拖拽文件夹时出错: {str(e)}")

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
    
    def update_image_preview(self, image_path, preview_label):
        """更新图片预览"""
        try:
            image = Image.open(image_path)
            # 调整图片大小用于预览，限制最大尺寸
            image.thumbnail((100, 100), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # 设置图片并调整标签大小
            preview_label.configure(image=photo, text="", compound='center')
            preview_label.image = photo  # 保持引用
            
            # 显示图片信息
            file_name = os.path.basename(image_path)
            file_size = os.path.getsize(image_path) // 1024  # KB
            info_text = f"{file_name}\n({file_size} KB)"
            
            # 在图片下方显示文件信息
            if hasattr(preview_label, 'info_label'):
                preview_label.info_label.configure(text=info_text)
            else:
                # 创建信息标签
                parent = preview_label.master
                preview_label.info_label = ttk.Label(parent, text=info_text, 
                                                   font=(self.custom_font, 8),
                                                   foreground='#666666', anchor='center')
                
                # 获取预览标签的网格信息并在其下方放置信息标签
                grid_info = preview_label.grid_info()
                row = grid_info.get('row', 0)
                preview_label.info_label.grid(row=row+1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
                
        except Exception as e:
            preview_label.configure(image="", text=f"预览失败\n{str(e)}")
            # 清除信息标签
            if hasattr(preview_label, 'info_label'):
                preview_label.info_label.configure(text="")
    
    def on_tab_change(self, event):
        """TAB切换处理"""
        selected_tab = event.widget.tab('current')['text']
        if "单例模式" in selected_tab:
            self.progress_var.set("就绪 - 请选择两张图片进行对比")
        else:
            self.progress_var.set("就绪 - 请选择两个包含图片的目录")
        
        # TAB切换后自动保存配置
        self.auto_save_config()

    def on_mode_change(self):
        """保留此方法以兼容性，但现在使用TAB切换"""
        pass
    
    def browse_image_a(self):
        """浏览选择图片A"""
        file_path = filedialog.askopenfilename(
            title="选择图片A",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.bmp *.gif")]
        )
        if file_path:
            self.image_a_entry.delete(0, tk.END)
            self.image_a_entry.insert(0, file_path)
            self.update_image_preview(file_path, self.image_a_preview)
            
            # 尝试自动检测和加载对应的图片B
            self.auto_detect_image_b(file_path)
            
            # 更新切换按钮状态
            self.update_switch_buttons_state()
    
    def auto_detect_image_b(self, image_a_path):
        """自动检测并加载对应的图片B"""
        try:
            # 获取图片A的文件信息
            a_dir = os.path.dirname(image_a_path)
            a_filename = os.path.basename(image_a_path)
            a_name, a_ext = os.path.splitext(a_filename)
            
            # 获取A文件夹名称
            a_folder_name = os.path.basename(a_dir)
            
            # 尝试多种B文件夹路径
            parent_dir = os.path.dirname(a_dir)
            possible_b_dirs = self.get_possible_b_folders(parent_dir, a_folder_name)
            
            # 遍历所有可能的B文件夹
            for b_dir in possible_b_dirs:
                if os.path.exists(b_dir) and os.path.isdir(b_dir):
                    # 检查B文件夹中是否存在相同编号的文件
                    b_file_path = os.path.join(b_dir, a_filename)
                    
                    # 如果文件名完全匹配
                    if os.path.exists(b_file_path):
                        print(f"自动检测到B文件夹({os.path.basename(b_dir)})中的对应文件: {a_filename}")
                        self.image_b_entry.delete(0, tk.END)
                        self.image_b_entry.insert(0, b_file_path)
                        self.update_image_preview(b_file_path, self.image_b_preview)
                        
                        # 更新切换按钮状态
                        self.update_switch_buttons_state()
                        return
                    
                    # 如果文件名不完全匹配，尝试查找相同编号的文件（忽略扩展名）
                    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
                    for ext in image_extensions:
                        b_file_path = os.path.join(b_dir, a_name + ext)
                        if os.path.exists(b_file_path):
                            print(f"自动检测到B文件夹({os.path.basename(b_dir)})中的对应文件: {os.path.basename(b_file_path)}")
                            self.image_b_entry.delete(0, tk.END)
                            self.image_b_entry.insert(0, b_file_path)
                            self.update_image_preview(b_file_path, self.image_b_preview)
                            
                            # 更新切换按钮状态
                            self.update_switch_buttons_state()
                            return
                    
                    # 尝试智能匹配：提取数字编号进行匹配
                    import re
                    # 提取文件名中的数字编号
                    number_match = re.search(r'(\d+)', a_name)
                    if number_match:
                        number = number_match.group(1)
                        # 在B文件夹中查找包含相同编号的文件
                        for file in os.listdir(b_dir):
                            if number in file and any(file.lower().endswith(ext) for ext in image_extensions):
                                b_file_path = os.path.join(b_dir, file)
                                print(f"智能匹配到B文件夹({os.path.basename(b_dir)})中的对应文件: {file}")
                                self.image_b_entry.delete(0, tk.END)
                                self.image_b_entry.insert(0, b_file_path)
                                self.update_image_preview(b_file_path, self.image_b_preview)
                                
                                # 更新切换按钮状态
                                self.update_switch_buttons_state()
                                return
            
            # 如果没找到对应文件，记录日志
            print(f"未找到对应的B文件夹或文件: {a_filename}")
            print("请手动选择图片B或检查B文件夹中的文件命名")
                
        except Exception as e:
            print(f"自动检测图片B时出错: {str(e)}")
    
    def get_possible_b_folders(self, parent_dir, a_folder_name):
        """获取可能的B文件夹路径列表"""
        possible_b_dirs = []
        
        # 定义文件夹名称映射规则
        folder_mapping = {
            'yuan': 'mubiao',
            'start': 'end',
            'source': 'target',
            'original': 'modified',
            'before': 'after',
            'input': 'output',
            'src': 'dst',
            'A': 'B',
            'a': 'b'
        }
        
        # 添加标准B文件夹
        possible_b_dirs.append(os.path.join(parent_dir, "B"))
        possible_b_dirs.append(os.path.join(parent_dir, "b"))
        
        # 根据映射规则添加对应的B文件夹
        if a_folder_name in folder_mapping:
            b_folder_name = folder_mapping[a_folder_name]
            possible_b_dirs.append(os.path.join(parent_dir, b_folder_name))
        
        # 处理带前缀或后缀的文件夹名称
        for prefix in ['**', '*', '_', '-']:
            for suffix in ['**', '*', '_', '-']:
                # 检查A文件夹是否带前缀或后缀
                if a_folder_name.startswith(prefix):
                    clean_name = a_folder_name[len(prefix):]
                    if clean_name in folder_mapping:
                        b_folder_name = folder_mapping[clean_name]
                        possible_b_dirs.append(os.path.join(parent_dir, prefix + b_folder_name))
                        possible_b_dirs.append(os.path.join(parent_dir, b_folder_name + suffix))
                
                if a_folder_name.endswith(suffix):
                    clean_name = a_folder_name[:-len(suffix)]
                    if clean_name in folder_mapping:
                        b_folder_name = folder_mapping[clean_name]
                        possible_b_dirs.append(os.path.join(parent_dir, prefix + b_folder_name))
                        possible_b_dirs.append(os.path.join(parent_dir, b_folder_name + suffix))
        
        # 去重并返回
        return list(set(possible_b_dirs))
    
    def browse_image_b(self):
        """浏览选择图片B"""
        file_path = filedialog.askopenfilename(
            title="选择图片B",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            self.image_b_entry.delete(0, tk.END)
            self.image_b_entry.insert(0, file_path)
            self.update_image_preview(file_path, self.image_b_preview)
            
            # 更新切换按钮状态
            self.update_switch_buttons_state()
    
    def browse_folder_a(self):
        """浏览选择目录A"""
        folder_path = filedialog.askdirectory(title="选择图片A目录")
        if folder_path:
            self.folder_a_entry.delete(0, tk.END)
            self.folder_a_entry.insert(0, folder_path)
            # 保存配置
            self.config["batch_mode"]["folder_a"] = folder_path
            self.save_config()
            
            # 尝试自动检测对应的B文件夹
            self.auto_detect_folder_b(folder_path)
    
    def auto_detect_folder_b(self, folder_a_path):
        """自动检测并设置对应的B文件夹"""
        try:
            # 获取A文件夹名称
            a_folder_name = os.path.basename(folder_a_path)
            parent_dir = os.path.dirname(folder_a_path)
            
            # 获取可能的B文件夹路径
            possible_b_dirs = self.get_possible_b_folders(parent_dir, a_folder_name)
            
            # 检查哪个B文件夹存在且包含图片文件
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            
            for b_dir in possible_b_dirs:
                if os.path.exists(b_dir) and os.path.isdir(b_dir):
                    # 检查B文件夹中是否有图片文件
                    try:
                        files = os.listdir(b_dir)
                        image_files = [f for f in files if f.lower().endswith(image_extensions)]
                        
                        if image_files:
                            # 找到包含图片的B文件夹，自动设置
                            self.folder_b_entry.delete(0, tk.END)
                            self.folder_b_entry.insert(0, b_dir)
                            self.config["batch_mode"]["folder_b"] = b_dir
                            self.save_config()
                            
                            print(f"自动检测到B文件夹: {os.path.basename(b_dir)}")
                            print(f"B文件夹包含 {len(image_files)} 个图片文件")
                            return
                    except Exception as e:
                        continue
            
            # 如果没有找到合适的B文件夹，记录日志
            print(f"未找到对应的B文件夹，请手动选择")
            print(f"已尝试的B文件夹: {[os.path.basename(d) for d in possible_b_dirs]}")
            
        except Exception as e:
            print(f"自动检测B文件夹时出错: {str(e)}")
    
    def browse_folder_b(self):
        """浏览选择目录B"""
        folder_path = filedialog.askdirectory(title="选择图片B目录")
        if folder_path:
            self.folder_b_entry.delete(0, tk.END)
            self.folder_b_entry.insert(0, folder_path)
            # 保存配置
            self.config["batch_mode"]["folder_b"] = folder_path
            self.save_config()
    

    
    def save_config_from_ui(self):
        """从界面保存配置"""
        self.config["selected_model"] = self.model_var.get()
        self.config["system_prompt"] = self.prompt_text.get(1.0, tk.END).strip()
        if hasattr(self, 'supplement_vars'):
            for key, var in self.supplement_vars.items():
                self.config[key] = var.get()
        
        # 检查当前选中的TAB来判断模式
        current_tab = self.work_notebook.tab(self.work_notebook.select(), "text")
        if "单例模式" in current_tab:
            # 保存图片路径
            if not self.config.get("single_mode"):
                self.config["single_mode"] = {}
            self.config["single_mode"]["image_a"] = self.image_a_entry.get()
            self.config["single_mode"]["image_b"] = self.image_b_entry.get()
        elif "批量模式" in current_tab:
            self.config["batch_mode"]["folder_a"] = self.folder_a_entry.get()
            self.config["batch_mode"]["folder_b"] = self.folder_b_entry.get()
        
        self.save_config()

    def call_api(self, image_a_path, image_b_path, prompt):
        """根据选择的模型调用相应的API"""
        selected_model = self.config.get("selected_model", "doubao")
        self.append_log(f"开始调用模型: {selected_model}")
        
        if selected_model == "doubao":
            return self.call_doubao_api(image_a_path, image_b_path, prompt)
        elif selected_model == "siliconflow":
            return self.call_siliconflow_api(image_a_path, image_b_path, prompt)
        elif selected_model == "xai":
            return self.call_xai_api(image_a_path, image_b_path, prompt)
        elif selected_model == "gptsapi":
            return self.call_gptsapi_api(image_a_path, image_b_path, prompt)
        elif selected_model == "aliyun":
            return self.call_aliyun_api(image_a_path, image_b_path, prompt)
        else:
            return "错误: 未知的模型类型"

    def call_doubao_api(self, image_a_path, image_b_path, prompt):
        """调用豆包API"""
        try:
            import base64
            
            # 读取图片文件并编码为base64
            with open(image_a_path, 'rb') as f:
                image_a_data = base64.b64encode(f.read()).decode('utf-8')
            
            with open(image_b_path, 'rb') as f:
                image_b_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 获取图片MIME类型
            def get_mime_type(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.bmp': 'image/bmp',
                    '.gif': 'image/gif'
                }
                return mime_types.get(ext, 'image/png')
            
            mime_a = get_mime_type(image_a_path)
            mime_b = get_mime_type(image_b_path)
            
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
                        "url": f"data:{mime_a};base64,{image_a_data}"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_b};base64,{image_b_data}"
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

            # 发送请求
            print("正在发送请求到豆包API...")
            print(f"图片A大小: {len(image_a_data)} 字符")
            print(f"图片B大小: {len(image_b_data)} 字符")

            response = requests.post("https://ark.cn-beijing.volces.com/api/v3/chat/completions", 
                                   headers=headers, json=data, timeout=120)
            
            print(f"API响应状态码: {response.status_code}")
            try:
                self.append_log("豆包API原始响应(text)", response.text)
            except Exception:
                pass
            
            if response.status_code == 200:
                result = response.json()
                print(f"豆包API响应完整内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                try:
                    self.append_log("豆包API响应(JSON)", json.dumps(result, ensure_ascii=False, indent=2))
                except Exception:
                    pass
                
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

    def call_gptsapi_api(self, image_a_path, image_b_path, prompt):
        """调用 GPTsAPI (Gemini) API - 双图对比"""
        try:
            import base64
            with open(image_a_path, 'rb') as f:
                image_a_data = base64.b64encode(f.read()).decode('utf-8')
            with open(image_b_path, 'rb') as f:
                image_b_data = base64.b64encode(f.read()).decode('utf-8')

            def get_mime_type(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                    '.bmp': 'image/bmp', '.gif': 'image/gif', '.webp': 'image/webp'
                }
                return mime_types.get(ext, 'image/png')

            mime_a = get_mime_type(image_a_path)
            mime_b = get_mime_type(image_b_path)
            api_key = self.config.get("gptsapi_api_key", "")
            if not api_key:
                return "错误: 未配置GPTsAPI Key，请在配置文件中设置"

            model = self.config.get("gptsapi_model", "gemini-3.1-pro-preview")
            url = f"https://api.gptsapi.net/v1beta/models/{model}:generateContent"
            headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
            data = {
                "contents": [{
                    "role": "user",
                    "parts": [
                        {"inline_data": {"mime_type": mime_a, "data": image_a_data}},
                        {"inline_data": {"mime_type": mime_b, "data": image_b_data}},
                        {"text": f"请对比分析这两张图片：\n\n{prompt}"}
                    ]
                }]
            }

            print("正在发送请求到 GPTsAPI...")
            response = requests.post(url, headers=headers, json=data, timeout=120)
            print(f"API响应状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        content = parts[0]["text"]
                        print(f"API调用成功，返回内容长度: {len(content)} 字符")
                        return content
                return f"API响应格式异常: {result}"
            else:
                return f"API调用失败: {response.status_code} - {response.text}"
        except Exception as e:
            print(f"API调用异常: {str(e)}")
            return f"API调用异常: {str(e)}"

    def call_xai_api(self, image_a_path, image_b_path, prompt):
        """调用XAI API"""
        try:
            import base64
            
            # 读取图片文件并编码为base64
            with open(image_a_path, 'rb') as f:
                image_a_data = base64.b64encode(f.read()).decode('utf-8')
            
            with open(image_b_path, 'rb') as f:
                image_b_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 获取图片MIME类型
            def get_mime_type(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.bmp': 'image/bmp',
                    '.gif': 'image/gif'
                }
                return mime_types.get(ext, 'image/png')
            
            mime_a = get_mime_type(image_a_path)
            mime_b = get_mime_type(image_b_path)
            
            # 准备请求数据
            api_key = self.config.get("xai_api_key", "")
            if not api_key:
                return "错误: 未配置XAI API Key，请在配置文件中设置"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建XAI API请求数据
            data = {
                "model": self.config.get("xai_model", "grok-2-vision-1212"),
                "messages": [
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请对比分析这两张图片："
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_a};base64,{image_a_data}"
                                }
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_b};base64,{image_b_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 4096  # 增加token限制，避免内容被截断
            }
            
            # 发送请求
            print("正在发送请求到XAI API...")
            print(f"图片A大小: {len(image_a_data)} 字符")
            print(f"图片B大小: {len(image_b_data)} 字符")

            response = requests.post("https://api.x.ai/v1/chat/completions", 
                                   headers=headers, json=data, timeout=120)
            
            print(f"API响应状态码: {response.status_code}")
            try:
                self.append_log("XAI API原始响应(text)", response.text)
            except Exception:
                pass
            
            if response.status_code == 200:
                result = response.json()
                print(f"XAI API响应完整内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                try:
                    self.append_log("XAI API响应(JSON)", json.dumps(result, ensure_ascii=False, indent=2))
                except Exception:
                    pass
                
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

    def call_siliconflow_api(self, image_a_path, image_b_path, prompt):
        """调用硅基流动API（双图）"""
        try:
            import base64
            
            with open(image_a_path, 'rb') as f:
                image_a_data = base64.b64encode(f.read()).decode('utf-8')
            with open(image_b_path, 'rb') as f:
                image_b_data = base64.b64encode(f.read()).decode('utf-8')
            
            def get_mime_type(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                    '.bmp': 'image/bmp', '.gif': 'image/gif', '.webp': 'image/webp'
                }
                return mime_types.get(ext, 'image/png')
            
            mime_a = get_mime_type(image_a_path)
            mime_b = get_mime_type(image_b_path)
            
            api_key = self.config.get("siliconflow_api_key", "")
            if not api_key:
                return "错误: 未配置硅基流动API Key，请在配置文件中设置"
            
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {
                "model": self.config.get("siliconflow_model", "zai-org/GLM-4.5"),
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{mime_a};base64,{image_a_data}"}},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_b};base64,{image_b_data}"}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
            }
            
            print("正在发送请求到硅基流动API...")
            response = requests.post("https://api.siliconflow.cn/v1/chat/completions", headers=headers, json=data, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    msg = result["choices"][0].get("message", {})
                    content = msg.get("content") or msg.get("reasoning_content", "")
                    content = content if content else "API返回内容为空"
                    # 过滤硅基流动输出的 <|begin_of_box|> 和 <|end_of_box|>
                    return _filter_siliconflow_box(content)
            return f"API调用失败: {response.status_code} - {response.text}"
        except Exception as e:
            return f"API调用异常: {str(e)}"

    def call_aliyun_api(self, image_a_path, image_b_path, prompt):
        """调用阿里云API"""
        try:
            import base64
            
            # 读取图片文件并编码为base64
            with open(image_a_path, 'rb') as f:
                image_a_data = base64.b64encode(f.read()).decode('utf-8')
            
            with open(image_b_path, 'rb') as f:
                image_b_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 获取图片MIME类型
            def get_mime_type(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.bmp': 'image/bmp',
                    '.gif': 'image/gif'
                }
                return mime_types.get(ext, 'image/png')
            
            mime_a = get_mime_type(image_a_path)
            mime_b = get_mime_type(image_b_path)
            
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
                                    "url": f"data:{mime_a};base64,{image_a_data}"
                                }
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_b};base64,{image_b_data}"
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
            print(f"使用模型: {data['model']}")
            print(f"图片A大小: {len(image_a_data)} 字符")
            print(f"图片B大小: {len(image_b_data)} 字符")
            
            response = requests.post("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", headers=headers, json=data, timeout=120)
            
            print(f"API响应状态码: {response.status_code}")
            try:
                self.append_log("阿里云API原始响应(text)", response.text)
            except Exception:
                pass
            
            if response.status_code == 200:
                result = response.json()
                print(f"阿里云API响应完整内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                try:
                    self.append_log("阿里云API响应(JSON)", json.dumps(result, ensure_ascii=False, indent=2))
                except Exception:
                    pass
                
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
    
    def generate_comparison(self):
        """生成对比结果"""
        # 保存配置
        self.save_config_from_ui()
        self.append_log("单例模式-开始处理")
        
        # 检查API密钥
        selected_model = self.config.get("selected_model", "doubao")
        if selected_model == "doubao" and not self.config.get("doubao_api_key"):
            messagebox.showerror("错误", "请先在配置文件中配置豆包API Key")
            self.progress_var.set("错误 - 请先配置豆包API Key")
            return
        elif selected_model == "siliconflow" and not self.config.get("siliconflow_api_key"):
            messagebox.showerror("错误", "请先在配置文件中配置硅基流动API Key")
            self.progress_var.set("错误 - 请先配置硅基流动API Key")
            return
        elif selected_model == "xai" and not self.config.get("xai_api_key"):
            messagebox.showerror("错误", "请先在配置文件中配置XAI API Key")
            self.progress_var.set("错误 - 请先配置XAI API Key")
            return
        elif selected_model == "aliyun" and not self.config.get("aliyun_api_key"):
            messagebox.showerror("错误", "请先在配置文件中配置阿里云API Key")
            self.progress_var.set("错误 - 请先配置阿里云API Key")
            return
        elif selected_model == "gptsapi" and not self.config.get("gptsapi_api_key"):
            messagebox.showerror("错误", "请先在配置文件中配置GPTsAPI Key")
            self.progress_var.set("错误 - 请先配置GPTsAPI Key")
            return
        
        # 检查提示词
        if not self._get_effective_prompt():
            messagebox.showerror("错误", "请输入系统提示词")
            self.progress_var.set("错误 - 请输入系统提示词")
            return
        
        # 更新按钮和状态
        current_tab = self.work_notebook.tab(self.work_notebook.select(), "text")
        if "单例模式" in current_tab:
            self.generate_button.config(state="disabled", text="🔄 处理中...")
        else:
            # 批量模式现在由start_batch_processing方法处理
            return
        
        self.progress_var.set("正在准备...")
        
        # 清空结果预览
        self.single_result_text.delete(1.0, tk.END)

        # 检测当前选中的TAB
        current_tab = self.work_notebook.tab(self.work_notebook.select(), "text")
        if "单例模式" in current_tab:
            # 单例模式（在主线程获取 prompt 后传入工作线程）
            prompt = self._get_effective_prompt()
            self.progress_var.set("正在处理单例模式...")
            threading.Thread(target=self.single_mode_process, args=(prompt,), daemon=True).start()
        else:
            # 批量模式 - 不应该到达这里
            print("批量模式应该由start_batch_processing方法处理")
            return
    
    def single_mode_process(self, prompt):
        """单例模式处理"""
        try:
            image_a_path = self.image_a_entry.get().strip()
            image_b_path = self.image_b_entry.get().strip()
            
            if not image_a_path or not image_b_path:
                print("请选择两张图片")
                self.progress_var.set("错误 - 请选择两张图片")
                return
            
            if not os.path.exists(image_a_path):
                print(f"图片A不存在: {image_a_path}")
                self.progress_var.set("错误 - 图片A不存在")
                return
            
            if not os.path.exists(image_b_path):
                print(f"图片B不存在: {image_b_path}")
                self.progress_var.set("错误 - 图片B不存在")
                return
            
            print("开始处理单例模式")
            print(f"图片A: {os.path.basename(image_a_path)}")
            print(f"图片B: {os.path.basename(image_b_path)}")
            self.append_log("单例-开始调用API", {"A": os.path.basename(image_a_path), "B": os.path.basename(image_b_path)})
            self.progress_var.set("正在调用API...")
            
            # 调用API
            result = self.call_api(image_a_path, image_b_path, prompt)
            
            if result.startswith("API调用失败") or result.startswith("API调用异常"):
                print("API调用失败")
                self.progress_var.set("处理失败")
                self.append_log("单例-失败", result[:2000])
            else:
                print("单例模式处理完成")
                self.single_result_text.insert(tk.END, result)
                self.progress_var.set("处理完成")
                self.append_log("单例-完成，返回文本长度", len(result))
            
        except Exception as e:
            print(f"处理异常: {str(e)}")
            self.append_log("单例-处理异常", str(e))
            self.progress_var.set("处理异常")
        finally:
            self.generate_button.config(state="normal", text="🚀 开始对比分析")
    
    def batch_mode_process(self, prompt):
        """批量模式处理"""
        try:
            folder_a = self.folder_a_entry.get().strip()
            folder_b = self.folder_b_entry.get().strip()

            if not folder_a or not folder_b:
                print("错误: 请选择两个目录")
                self.progress_var.set("错误 - 请选择两个目录")
                return

            if not os.path.exists(folder_a):
                print(f"错误: 目录A不存在 - {folder_a}")
                self.progress_var.set("错误 - 目录A不存在")
                return

            if not os.path.exists(folder_b):
                print(f"错误: 目录B不存在 - {folder_b}")
                self.progress_var.set("错误 - 目录B不存在")
                return
            
            print("开始处理批量模式...")
            print(f"目录A: {folder_a}")
            print(f"目录B: {folder_b}")
            print(f"处理模式: {self.process_mode}")
            self.append_log("批量-开始", {"A": folder_a, "B": folder_b, "mode": self.process_mode})
            
            # 获取目录中的图片文件
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            files_a = [f for f in os.listdir(folder_a) if f.lower().endswith(image_extensions)]
            files_b = [f for f in os.listdir(folder_b) if f.lower().endswith(image_extensions)]
            
            if not files_a:
                print("错误: 目录A中没有找到图片文件")
                return
            
            if not files_b:
                print("错误: 目录B中没有找到图片文件")
                return
            
            # 按文件名排序
            files_a.sort()
            files_b.sort()
            
            print(f"目录A中找到 {len(files_a)} 个图片文件")
            print(f"目录B中找到 {len(files_b)} 个图片文件")
            self.append_log("批量-文件统计", {"A_images": len(files_a), "B_images": len(files_b)})

            # 根据处理模式决定要处理的文件
            files_to_process = []
            
            if self.process_mode == "process_missing_only":
                # 仅处理无txt的图片（txt 与 B 图片同名）
                for file_a in files_a:
                    name_a = os.path.splitext(file_a)[0]
                    file_b = next((b for b in files_b if os.path.splitext(b)[0] == name_a), None)
                    if not file_b:
                        continue  # 无对应 B，主循环会跳过
                    name_b = os.path.splitext(file_b)[0]
                    txt_file = os.path.join(folder_b, f"{name_b}.txt")
                    if not os.path.exists(txt_file):
                        files_to_process.append(file_a)
                
                print(f"将处理 {len(files_to_process)} 个无txt的图片文件")
                self.append_log("批量-仅处理无txt", {"count": len(files_to_process)})
            else:
                # 处理所有图片（覆盖模式或全新处理）
                files_to_process = files_a
                print(f"将处理所有 {len(files_to_process)} 个图片文件")
                self.append_log("批量-处理所有", {"count": len(files_to_process)})

            if not files_to_process:
                print("没有需要处理的文件")
                self.progress_var.set("没有需要处理的文件")
                return

            # 处理文件
            processed_count = 0
            failed_count = 0
            skipped_count = 0
            for i, file_a in enumerate(files_to_process):
                # 检查是否需要停止处理
                if self.stop_batch_processing:
                    print("批量处理已被用户中断")
                    break

                # 查找对应的B图片
                name_a = os.path.splitext(file_a)[0]
                file_b = None
                
                # 在B文件夹中查找同名文件（忽略扩展名）
                for b_file in files_b:
                    b_name = os.path.splitext(b_file)[0]
                    if b_name == name_a:
                        file_b = b_file
                        break

                if not file_b:
                    print(f"跳过: 在B文件夹中未找到对应的图片 {file_a}")
                    skipped_count += 1
                    continue

                name_b = os.path.splitext(file_b)[0]
                image_a_path = os.path.join(folder_a, file_a)
                image_b_path = os.path.join(folder_b, file_b)

                print(f"处理第 {i+1}/{len(files_to_process)} 组: {file_a} vs {file_b}")
                self.progress_var.set(f"正在处理第 {i+1}/{len(files_to_process)} 组图片...")
                self.append_log("批量-开始处理一组", {"index": i+1, "total": len(files_to_process), "A": file_a, "B": file_b})

                # 再次检查是否需要停止处理
                if self.stop_batch_processing:
                    print("批量处理已被用户中断")
                    break

                # 调用API
                result = self.call_api(image_a_path, image_b_path, prompt)

                if result.startswith("API调用失败") or result.startswith("API调用异常"):
                    print(f"失败: {result}")
                    failed_count += 1
                    self.append_log("批量-失败", result[:2000])
                    # 继续处理后续文件
                    continue
                else:
                    # 保存结果到文件（与B图片同名）
                    output_file = os.path.join(folder_b, f"{name_b}.txt")
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(result)
                        print(f"成功: 结果已保存到 {output_file}")
                        processed_count += 1
                        self.append_log("批量-成功", {"saved_to": output_file})
                    except Exception as e:
                        print(f"保存文件失败: {str(e)}")
                        failed_count += 1
                        self.append_log("批量-保存失败", str(e))
                        # 继续处理后续文件
                        continue
            
            if self.stop_batch_processing:
                print(f"批量处理已中断 - 成功 {processed_count}，失败 {failed_count}，跳过 {skipped_count}，总计 {len(files_to_process)}")
                self.progress_var.set(f"批量处理中断 - 成功 {processed_count}，失败 {failed_count}，跳过 {skipped_count}")
                self.append_log("批量-中断", {"success": processed_count, "failed": failed_count, "skipped": skipped_count, "total": len(files_to_process)})
            else:
                if failed_count > 0 or skipped_count > 0:
                    print(f"批量处理完成（部分失败）- 成功 {processed_count}，失败 {failed_count}，跳过 {skipped_count}，总计 {len(files_to_process)}")
                    self.progress_var.set(f"批量完成（部分失败）- 成功 {processed_count}，失败 {failed_count}，跳过 {skipped_count}")
                    self.append_log("批量-完成(部分失败)", {"success": processed_count, "failed": failed_count, "skipped": skipped_count, "total": len(files_to_process)})
                else:
                    print(f"批量处理完成 - 成功 {processed_count}/{len(files_to_process)}")
                    self.progress_var.set(f"批量处理完成 - 成功 {processed_count}/{len(files_to_process)}")
                    self.append_log("批量-完成(全部成功)", {"success": processed_count, "total": len(files_to_process)})

        except Exception as e:
            print(f"批量处理异常: {str(e)}")
            self.progress_var.set("批量处理异常")
        finally:
            # 重置批量处理状态
            self.batch_processing = False
            self.stop_batch_processing = False
            self.batch_generate_button.config(state="normal", text="🚀 开始批量处理")
    
    def handle_batch_button_click(self):
        """处理批量处理按钮点击事件"""
        if not self.batch_processing:
            # 开始批量处理
            self.append_log("用户点击开始批量处理")
            self.start_batch_processing()
        else:
            # 停止批量处理
            self.stop_batch_processing = True
            self.batch_generate_button.config(state="disabled", text="🔄 正在停止...")
            self.progress_var.set("正在停止批量处理...")
            print("用户请求停止批量处理")
            self.append_log("收到停止批量处理请求")

    def start_batch_processing(self):
        """开始批量处理"""
        try:
            selected_model = self.config.get("selected_model", "doubao")
            if selected_model == "doubao" and not self.config.get("doubao_api_key"):
                messagebox.showerror("错误", "请先在配置文件中配置豆包API Key")
                return
            elif selected_model == "siliconflow" and not self.config.get("siliconflow_api_key"):
                messagebox.showerror("错误", "请先在配置文件中配置硅基流动API Key")
                return
            elif selected_model == "xai" and not self.config.get("xai_api_key"):
                messagebox.showerror("错误", "请先在配置文件中配置XAI API Key")
                return
            elif selected_model == "gptsapi" and not self.config.get("gptsapi_api_key"):
                messagebox.showerror("错误", "请先在配置文件中配置GPTsAPI Key")
                return
            elif selected_model == "aliyun" and not self.config.get("aliyun_api_key"):
                messagebox.showerror("错误", "请先在配置文件中配置阿里云API Key")
                return

            folder_a = self.folder_a_entry.get().strip()
            folder_b = self.folder_b_entry.get().strip()

            if not folder_a or not folder_b:
                messagebox.showerror("错误", "请选择两个目录")
                return

            if not os.path.exists(folder_a):
                messagebox.showerror("错误", f"目录A不存在: {folder_a}")
                return

            if not os.path.exists(folder_b):
                messagebox.showerror("错误", f"目录B不存在: {folder_b}")
                return

            # 获取目录中的图片文件和txt文件
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            files_a = [f for f in os.listdir(folder_a) if f.lower().endswith(image_extensions)]
            files_b = [f for f in os.listdir(folder_b) if f.lower().endswith(image_extensions)]
            
            # 获取txt文件
            txt_files_b = [f for f in os.listdir(folder_b) if f.lower().endswith('.txt')]
            
            # 按文件名排序
            files_a.sort()
            files_b.sort()
            txt_files_b.sort()

            if not files_a:
                messagebox.showerror("错误", "目录A中没有找到图片文件")
                return

            if not files_b:
                messagebox.showerror("错误", "目录B中没有找到图片文件")
                return

            print(f"目录A中找到 {len(files_a)} 个图片文件")
            print(f"目录B中找到 {len(files_b)} 个图片文件")
            print(f"目录B中找到 {len(txt_files_b)} 个txt文件")

            # 检查图片数量和txt数量是否相同
            if len(files_a) == len(txt_files_b):
                # 图片数量和txt数量相同，询问是否覆盖
                result = messagebox.askyesno("文件覆盖确认", 
                                           f"检测到图片数量({len(files_a)})和txt数量({len(txt_files_b)})相同。\n\n是否覆盖现有的txt文件？\n\n选择'是'覆盖所有文件，选择'否'取消操作。",
                                           icon='warning', default='no')
                if not result:
                    print("用户取消了批量处理")
                    return
                else:
                    print("用户确认覆盖现有文件，开始处理")
                    self.process_mode = "overwrite_all"
            elif len(txt_files_b) > 0:
                # 存在txt文件但数量不同，询问处理方式
                result = messagebox.askyesno("处理方式选择", 
                                           f"检测到图片数量({len(files_a)})和txt数量({len(txt_files_b)})不同。\n\n是否仅处理无txt的图片？\n\n选择'是'仅处理无txt的图片，选择'否'全部重新覆盖处理。",
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

            # 开始批量处理
            self.batch_processing = True
            self.stop_batch_processing = False
            self.batch_generate_button.config(state="normal", text="⏹️ 停止处理")
            self.progress_var.set("正在准备批量处理...")
            try:
                # 自动切换到日志TAB，便于观察过程
                self.work_notebook.select(self.log_frame)
            except Exception:
                pass
            
            # 在主线程获取 prompt 后传入工作线程
            prompt = self._get_effective_prompt()
            # 启动处理线程
            threading.Thread(target=self.batch_mode_process, args=(prompt,), daemon=True).start()

        except Exception as e:
            print(f"开始批量处理失败: {str(e)}")
            messagebox.showerror("错误", f"开始批量处理失败: {str(e)}")

    def on_closing(self):
        """窗口关闭事件处理"""
        # 如果正在批量处理，先停止
        if self.batch_processing:
            self.stop_batch_processing = True
        self.root.destroy()

    def get_current_image_sequence(self):
        """获取当前图片序列信息"""
        try:
            image_a_path = self.image_a_entry.get().strip()
            image_b_path = self.image_b_entry.get().strip()
            
            if not image_a_path or not image_b_path:
                return None, None, None, None
            
            # 获取图片A和B的目录和文件名
            a_dir = os.path.dirname(image_a_path)
            b_dir = os.path.dirname(image_b_path)
            a_filename = os.path.basename(image_a_path)
            b_filename = os.path.basename(image_b_path)
            a_name, a_ext = os.path.splitext(a_filename)
            b_name, b_ext = os.path.splitext(b_filename)
            
            # 检查是否在同一父目录下
            parent_dir = os.path.dirname(a_dir)
            if parent_dir != os.path.dirname(b_dir):
                return None, None, None, None
            
            # 获取A和B文件夹名称
            a_folder = os.path.basename(a_dir)
            b_folder = os.path.basename(b_dir)
            
            # 获取所有图片文件
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            
            # 获取A文件夹中的图片文件
            if os.path.exists(a_dir) and os.path.isdir(a_dir):
                a_files = [f for f in os.listdir(a_dir) if f.lower().endswith(image_extensions)]
                a_files.sort()
            else:
                return None, None, None, None
            
            # 获取B文件夹中的图片文件
            if os.path.exists(b_dir) and os.path.isdir(b_dir):
                b_files = [f for f in os.listdir(b_dir) if f.lower().endswith(image_extensions)]
                b_files.sort()
            else:
                return None, None, None, None
            
            # 查找当前图片在序列中的位置（基于编号匹配，不要求文件名完全一致）
            current_index = -1
            for i, a_file in enumerate(a_files):
                a_name_check, _ = os.path.splitext(a_file)
                # 提取A文件名中的编号
                a_number = self.extract_number_from_filename(a_name_check)
                if a_number is None:
                    continue
                
                # 在B文件夹中查找包含相同编号的文件
                for b_file in b_files:
                    b_name_check, _ = os.path.splitext(b_file)
                    b_number = self.extract_number_from_filename(b_file)
                    if b_number == a_number:
                        # 找到匹配的编号，检查是否是当前选中的图片
                        if a_name_check == a_name and b_name_check == b_name:
                            current_index = i
                            break
                if current_index != -1:
                    break
            
            if current_index == -1:
                return None, None, None, None
            
            return a_dir, b_dir, a_files, current_index
            
        except Exception as e:
            print(f"获取图片序列信息失败: {str(e)}")
            return None, None, None, None

    def extract_number_from_filename(self, filename):
        """从文件名中提取编号"""
        try:
            import re
            # 查找文件名中的数字编号
            number_match = re.search(r'(\d+)', filename)
            if number_match:
                return number_match.group(1)
            return None
        except Exception as e:
            print(f"提取文件名编号失败: {str(e)}")
            return None

    def switch_to_previous(self):
        """切换到上一张图片"""
        try:
            a_dir, b_dir, a_files, current_index = self.get_current_image_sequence()
            if a_dir is None or current_index <= 0:
                return
            
            # 切换到上一张
            prev_index = current_index - 1
            prev_a_file = a_files[prev_index]
            
            # 基于编号匹配查找对应的B图片
            prev_a_name, _ = os.path.splitext(prev_a_file)
            prev_a_number = self.extract_number_from_filename(prev_a_name)
            if prev_a_number is None:
                print(f"无法从文件名提取编号: {prev_a_file}")
                return
            
            # 在B文件夹中查找包含相同编号的文件
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            b_files = [f for f in os.listdir(b_dir) if f.lower().endswith(image_extensions)]
            prev_b_file = None
            
            for b_file in b_files:
                b_name, _ = os.path.splitext(b_file)
                b_number = self.extract_number_from_filename(b_name)
                if b_number == prev_a_number:
                    prev_b_file = b_file
                    break
            
            if prev_b_file is None:
                print(f"在B文件夹中未找到编号为 {prev_a_number} 的图片")
                return
            
            # 构建完整路径
            prev_a_path = os.path.join(a_dir, prev_a_file)
            prev_b_path = os.path.join(b_dir, prev_b_file)
            
            # 检查文件是否存在
            if not os.path.exists(prev_a_path) or not os.path.exists(prev_b_path):
                print(f"上一张图片不存在: {prev_a_path} 或 {prev_b_path}")
                return
            
            # 更新界面
            self.image_a_entry.delete(0, tk.END)
            self.image_a_entry.insert(0, prev_a_path)
            self.update_image_preview(prev_a_path, self.image_a_preview)
            
            self.image_b_entry.delete(0, tk.END)
            self.image_b_entry.insert(0, prev_b_path)
            self.update_image_preview(prev_b_path, self.image_b_preview)
            
            # 更新按钮状态
            self.update_switch_buttons_state()
            
            print(f"已切换到上一张图片: {os.path.basename(prev_a_file)} -> {os.path.basename(prev_b_file)}")
            
        except Exception as e:
            print(f"切换到上一张图片失败: {str(e)}")

    def switch_to_next(self):
        """切换到下一张图片"""
        try:
            a_dir, b_dir, a_files, current_index = self.get_current_image_sequence()
            if a_dir is None or current_index >= len(a_files) - 1:
                return
            
            # 切换到下一张
            next_index = current_index + 1
            next_a_file = a_files[next_index]
            
            # 基于编号匹配查找对应的B图片
            next_a_name, _ = os.path.splitext(next_a_file)
            next_a_number = self.extract_number_from_filename(next_a_name)
            if next_a_number is None:
                print(f"无法从文件名提取编号: {next_a_file}")
                return
            
            # 在B文件夹中查找包含相同编号的文件
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            b_files = [f for f in os.listdir(b_dir) if f.lower().endswith(image_extensions)]
            next_b_file = None
            
            for b_file in b_files:
                b_name, _ = os.path.splitext(b_file)
                b_number = self.extract_number_from_filename(b_name)
                if b_number == next_a_number:
                    next_b_file = b_file
                    break
            
            if next_b_file is None:
                print(f"在B文件夹中未找到编号为 {next_a_number} 的图片")
                return
            
            # 构建完整路径
            next_a_path = os.path.join(a_dir, next_a_file)
            next_b_path = os.path.join(b_dir, next_b_file)
            
            # 检查文件是否存在
            if not os.path.exists(next_a_path) or not os.path.exists(next_b_path):
                print(f"下一张图片不存在: {next_a_path} 或 {next_b_path}")
                return
            
            # 更新界面
            self.image_a_entry.delete(0, tk.END)
            self.image_a_entry.insert(0, next_a_path)
            self.update_image_preview(next_a_path, self.image_a_preview)
            
            self.image_b_entry.delete(0, tk.END)
            self.image_b_entry.insert(0, next_b_path)
            self.update_image_preview(next_b_path, self.image_b_preview)
            
            # 更新按钮状态
            self.update_switch_buttons_state()
            
            print(f"已切换到下一张图片: {os.path.basename(next_a_file)} -> {os.path.basename(next_b_file)}")
            
        except Exception as e:
            print(f"切换到下一张图片失败: {str(e)}")

    def update_switch_buttons_state(self):
        """更新切换按钮的状态（启用/禁用）"""
        try:
            a_dir, b_dir, a_files, current_index = self.get_current_image_sequence()
            
            if a_dir is None:
                # 没有有效的图片序列，禁用两个按钮
                self.prev_button.config(state=tk.DISABLED)
                self.next_button.config(state=tk.DISABLED)
                return
            
            # 检查上一张按钮状态
            if current_index <= 0:
                self.prev_button.config(state=tk.DISABLED)
            else:
                self.prev_button.config(state=tk.NORMAL)
            
            # 检查下一张按钮状态
            if current_index >= len(a_files) - 1:
                self.next_button.config(state=tk.DISABLED)
            else:
                self.next_button.config(state=tk.NORMAL)
                
        except Exception as e:
            print(f"更新切换按钮状态失败: {str(e)}")
            # 出错时禁用两个按钮
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)

    def update_batch_buttons_state(self):
        """更新批量处理按钮的状态"""
        try:
            if self.batch_processing:
                # 正在处理中
                self.batch_generate_button.config(state="normal", text="⏹️ 停止处理")
                self.delete_txt_button.config(state=tk.DISABLED)
            else:
                # 未在处理中
                self.batch_generate_button.config(state="normal", text="🚀 开始批量处理")
                self.delete_txt_button.config(state=tk.NORMAL)
        except Exception as e:
            print(f"更新批量处理按钮状态失败: {str(e)}")



    def delete_all_txt_files(self):
        """删除所有txt文件"""
        try:
            folder_a = self.folder_a_entry.get().strip()
            folder_b = self.folder_b_entry.get().strip()

            if not folder_a or not folder_b:
                messagebox.showerror("错误", "请先选择两个目录")
                return

            if not os.path.exists(folder_a):
                messagebox.showerror("错误", f"目录A不存在: {folder_a}")
                return

            if not os.path.exists(folder_b):
                messagebox.showerror("错误", f"目录B不存在: {folder_b}")
                return

            # 获取目录中的所有txt文件
            txt_files_a = [f for f in os.listdir(folder_a) if f.lower().endswith('.txt')]
            txt_files_b = [f for f in os.listdir(folder_b) if f.lower().endswith('.txt')]

            total_txt_files = len(txt_files_a) + len(txt_files_b)
            
            if total_txt_files == 0:
                messagebox.showinfo("提示", "目录中没有txt文件")
                return

            # 显示确认对话框
            confirm_message = f"将删除以下txt文件：\n\n"
            
            if txt_files_a:
                confirm_message += f"目录A中的txt文件 ({len(txt_files_a)}个):\n"
                if len(txt_files_a) <= 5:
                    confirm_message += "\n".join(txt_files_a)
                else:
                    confirm_message += "\n".join(txt_files_a[:5])
                    confirm_message += f"\n... 还有 {len(txt_files_a) - 5} 个文件"
                confirm_message += "\n\n"
            
            if txt_files_b:
                confirm_message += f"目录B中的txt文件 ({len(txt_files_b)}个):\n"
                if len(txt_files_b) <= 5:
                    confirm_message += "\n".join(txt_files_b)
                else:
                    confirm_message += "\n".join(txt_files_b[:5])
                    confirm_message += f"\n... 还有 {len(txt_files_b) - 5} 个文件"
                confirm_message += "\n\n"

            confirm_message += f"总共 {total_txt_files} 个txt文件将被删除。\n\n⚠️ 此操作不可恢复！\n是否继续删除？"

            result = messagebox.askyesno("文件删除确认", confirm_message,
                                       icon='warning', default='no')

            if not result:
                print("用户取消了删除操作")
                return

            # 删除txt文件
            deleted_count = 0
            
            for txt_file in txt_files_a:
                try:
                    os.remove(os.path.join(folder_a, txt_file))
                    print(f"已删除文件: {txt_file}")
                    deleted_count += 1
                except Exception as e:
                    print(f"删除文件失败 {txt_file}: {str(e)}")

            for txt_file in txt_files_b:
                try:
                    os.remove(os.path.join(folder_b, txt_file))
                    print(f"已删除文件: {txt_file}")
                    deleted_count += 1
                except Exception as e:
                    print(f"删除文件失败 {txt_file}: {str(e)}")

            print(f"删除完成，共删除 {deleted_count} 个txt文件")
            messagebox.showinfo("删除完成", f"删除完成，共删除 {deleted_count} 个txt文件")

        except Exception as e:
            print(f"删除txt文件时出错: {str(e)}")
            messagebox.showerror("错误", f"删除txt文件时出错: {str(e)}")

def main():
    """主函数"""
    # 如果支持拖拽功能，使用TkinterDnD
    if DND_AVAILABLE and TkinterDnD:
        try:
            root = TkinterDnD.Tk()
            print("拖拽功能已启用")
        except Exception as e:
            root = tk.Tk()
            print(f"警告: 无法初始化拖拽功能，使用标准Tkinter: {e}")
    else:
        root = tk.Tk()
        if not DND_AVAILABLE:
            print("tkinterdnd2 未安装，拖拽功能不可用")

    app = ImageComparisonTool(root)
    root.mainloop()

if __name__ == "__main__":
    main() 