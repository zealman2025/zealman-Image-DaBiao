# 图片分析打标工具 / 双图对比分析工具

基于多模型视觉 API 的图片分析与打标工具，支持单图分析、批量打标、双图对比。

**作者**: zealman
**QQ群**: 1046279436
---

## 功能概览

### 单图模式（支持批量和并发，适用Z-IMAGE,QWEN-IMAGE等模型训练打标）

- **单图分析**：选择一张图片，使用 AI 模型生成描述/打标，**结果仅在界面显示，不生成 txt 文件**
- **批量分析**：对文件夹内图片批量分析，结果保存为 txt 文件（见下方说明）
- 支持并发处理，可配置并发数

### 双图模式（支持批量，适用QWEN-IMAGE-EDIT-2511,FLUX2-KLEIN-9B,KONTEXT等编辑模型训练打标）

- **单例对比**：选择两张图片，对比分析差异，需要自己写系统提示词**结果仅在界面显示，不生成 txt 文件**
- **批量对比**：按 A/B 两个目录配对图片，批量对比并保存结果（见下方说明）

### 批量模式 txt 输出说明

| 模式       | txt 保存位置                     |
|------------|----------------------------------|
| 单图批量   | 图片所在目录，与图片同名的 `.txt` |
| 双图批量   | **B 文件夹**，与 B 图片同名的 `.txt` |

### 支持的模型与 API 注册地址（部分模型需要魔法不会的请用国产模型）

| 类别     | 模型       | 注册 / 获取 API Key |
|----------|------------|----------------------|
| 国内     | 豆包       | [火山方舟（火山引擎）](https://www.volcengine.com/product/doubao) |
| 国内     | 硅基流动   | [SiliconFlow 控制台](https://cloud.siliconflow.cn/account/ak) |
| 国内     | 阿里云     | [阿里云百炼 / DashScope](https://dashscope.console.aliyun.com/) |
| 国外     | XAI        | [xAI 控制台](https://console.x.ai/) |
| 国外     | GPTsAPI    | [GPTsAPI](https://gptsapi.net)（聚合 Gemini 等模型） |

---

## 快速开始

### 1. 配置 API Key

编辑 `config-api.json`，填入各模型的 API Key 和也可以自己改模型名称：

```json
{
  "selected_model": "doubao",
  "doubao_api_key": "你的豆包API Key",
  "doubao_model": "doubao-seed-2-0-pro-260215",
  "xai_api_key": "",
  "aliyun_api_key": "",
  ...
}
```

### 2. 启动程序

- **单图模式**：双击 `启动单图.bat`
- **双图模式**：双击 `启动双图.bat`

---

## 配置文件说明

| 文件             | 用途                         |
|------------------|------------------------------|
| `config-api.json` | 公共配置：模型选择、API Key、提示词补充文案 |
| `config-dan.json` | 单图模式：系统提示词、并发数、路径等     |
| `config-shuang.json` | 双图模式：系统提示词、路径等           |

配置会自动保存，重启后会加载上次设置。

### 提示词补充选项

在系统提示词下方有可勾选的补充项，勾选后会将对应内容追加到提示词一并发送给 API。文案可在 `config-api.json` 中自定义：

- `prompt_supplement_text_1` ~ `prompt_supplement_text_5`

默认包括：纯文本输出、不要 Markdown、输出英文、输出中文 JSON、输出英文 JSON 等。

---

## 项目结构

```text
dabiao/
├── MYAPI单图模式.py      # 单图分析与批量打标
├── MYAPI双图模式.py      # 双图对比
├── config_api.py         # 配置读写模块
├── config-api.json       # 公共 API 配置
├── config-dan.json       # 单图模式配置
├── config-shuang.json    # 双图模式配置
├── requirements.txt      # 依赖列表
├── 启动单图.bat          # 单图模式入口
├── 启动双图.bat          # 双图模式入口
├── 提示词/               # 提示词模板等
└── README.md
```

运行 `创建便携版.bat` 后会生成「便携版」文件夹，内含 `python/`（Python 运行环境）、`启动单图.bat`、`启动双图.bat` 及程序文件。

---

## 常见问题

### 单例/单图分析为什么不生成 txt？

单例对比与单图分析为**即时预览**模式，结果仅在界面显示，便于快速测试API效果调试提示词。需要保存到文件时，请使用**批量模式**。

---

## 许可证

本项目仅供学习与个人使用。使用各模型 API 时请遵守其服务条款与计费规则。
