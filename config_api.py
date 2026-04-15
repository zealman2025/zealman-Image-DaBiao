# -*- coding: utf-8 -*-
"""公共配置模块：API 配置与模式配置的加载/保存"""

import json
import os
import sys

# 配置目录：打包为 exe 时使用 exe 所在目录，否则使用脚本所在目录
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 提示词补充选项的默认文字（可于 config-api.json 中自定义）
PROMPT_SUPPLEMENT_TEXT_KEYS = ["prompt_supplement_text_1", "prompt_supplement_text_2", "prompt_supplement_text_3", "prompt_supplement_text_4", "prompt_supplement_text_5"]
DEFAULT_PROMPT_SUPPLEMENT_TEXTS = [
    "1纯文本输出,不要评论,不要发表序言",
    "2不要使用任何 Markdown 格式",
    "3输出纯英文版本",
    "4输出纯中文json版本",
    "5输出纯英文json版本",
]

# 各模型在 config-api.json 中对应的 API Key 与模型名称键名（用于界面绑定）
MODEL_CREDENTIAL_KEYS = {
    "doubao": ("doubao_api_key", "doubao_model"),
    "autodl": ("autodl_api_key", "autodl_model"),
    "aliyun": ("aliyun_api_key", "aliyun_model"),
}

MODEL_DISPLAY_NAMES = {
    "doubao": "豆包",
    "autodl": "AutoDL",
    "aliyun": "阿里云",
}

# API 相关配置键（公共）
API_KEYS = [
    "selected_model",
    "doubao_api_key", "doubao_model",
    "autodl_api_key", "autodl_model",
    "aliyun_api_key", "aliyun_model",
] + PROMPT_SUPPLEMENT_TEXT_KEYS

# 单图模式独立配置键
DAN_KEYS = [
    "system_prompt", "concurrent_workers",
    "prompt_supplement_1", "prompt_supplement_2", "prompt_supplement_3", "prompt_supplement_4", "prompt_supplement_5",
    "single_mode", "batch_mode",
]

# 双图模式独立配置键
SHUANG_KEYS = [
    "system_prompt",
    "prompt_supplement_1", "prompt_supplement_2", "prompt_supplement_3", "prompt_supplement_4", "prompt_supplement_5",
    "single_mode", "batch_mode",
]


def _ensure_dir():
    os.chdir(SCRIPT_DIR)


def load_api_config():
    """加载公共 API 配置"""
    _ensure_dir()
    default_api = {
        "selected_model": "doubao",
        "doubao_api_key": "",
        "doubao_model": "doubao-1-5-thinking-vision-pro-250428",
        "autodl_api_key": "",
        "autodl_model": "Qwen3.5-397B-A17B",
        "aliyun_api_key": "",
        "aliyun_model": "qwen-vl-plus",
        **dict(zip(PROMPT_SUPPLEMENT_TEXT_KEYS, DEFAULT_PROMPT_SUPPLEMENT_TEXTS)),
    }
    try:
        with open("config-api.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in default_api.items():
                if k not in data:
                    data[k] = v
            sm = data.get("selected_model")
            if sm == "siliconflow":
                data["selected_model"] = "autodl"
            elif sm in ("xai", "gptsapi"):
                data["selected_model"] = "doubao"
            return data
    except FileNotFoundError:
        return default_api
    except (json.JSONDecodeError, Exception) as e:
        print(f"加载 config-api.json 失败: {e}")
        return default_api


def save_api_config(config):
    """保存公共 API 配置"""
    _ensure_dir()
    api_config = {k: config.get(k) for k in API_KEYS if k in config}
    with open("config-api.json", "w", encoding="utf-8") as f:
        json.dump(api_config, f, ensure_ascii=False, indent=4)


def load_dan_config():
    """加载单图模式配置"""
    _ensure_dir()
    default_dan = {
        "system_prompt": "请详细分析这张图片，描述图片的内容、风格、色彩、构图等特征。",
        "concurrent_workers": 2,
        "prompt_supplement_1": True, "prompt_supplement_2": True,
        "prompt_supplement_3": True, "prompt_supplement_4": False, "prompt_supplement_5": False,
        "single_mode": {"image": ""},
        "batch_mode": {"folder": ""},
    }
    try:
        with open("config-dan.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in default_dan.items():
                if k not in data:
                    data[k] = v
            return data
    except FileNotFoundError:
        return default_dan
    except (json.JSONDecodeError, Exception) as e:
        print(f"加载 config-dan.json 失败: {e}")
        return default_dan


def save_dan_config(config):
    """保存单图模式配置"""
    _ensure_dir()
    dan_config = {k: config.get(k) for k in DAN_KEYS if k in config}
    with open("config-dan.json", "w", encoding="utf-8") as f:
        json.dump(dan_config, f, ensure_ascii=False, indent=4)


def load_shuang_config():
    """加载双图模式配置"""
    _ensure_dir()
    default_shuang = {
        "system_prompt": "请对比这两张图片，详细描述它们的差异和相似之处。",
        "prompt_supplement_1": True, "prompt_supplement_2": True,
        "prompt_supplement_3": True, "prompt_supplement_4": False, "prompt_supplement_5": False,
        "single_mode": {"image_a": "", "image_b": ""},
        "batch_mode": {"folder_a": "", "folder_b": ""},
    }
    try:
        with open("config-shuang.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in default_shuang.items():
                if k not in data:
                    data[k] = v
            return data
    except FileNotFoundError:
        return default_shuang
    except (json.JSONDecodeError, Exception) as e:
        print(f"加载 config-shuang.json 失败: {e}")
        return default_shuang


def save_shuang_config(config):
    """保存双图模式配置"""
    _ensure_dir()
    shuang_config = {k: config.get(k) for k in SHUANG_KEYS if k in config}
    with open("config-shuang.json", "w", encoding="utf-8") as f:
        json.dump(shuang_config, f, ensure_ascii=False, indent=4)
