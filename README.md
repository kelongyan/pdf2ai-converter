<div align="center">

# 📄✨ PDF2AI Converter

*使用 AI 视觉大模型智能转换 PDF 为 Markdown 或 Word，自动去除页眉页脚，尽可能保留公式、表格与排版*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/kelongyan/pdf2ai-converter/pulls)

[✨ 特性](#-特性) • [🚀 快速开始](#-快速开始) • [🎮 使用方法](#-使用方法) • [⚙️ 配置](#️-配置)

</div>

---

## 🎯 这是什么？

这个工具使用 **AI 视觉大模型** 智能识别 PDF 页面，支持输出 Markdown 和 Word，并尽可能保留文档结构与排版信息。提供三种使用方式：**Web UI**、**交互式 CLI 启动器**、**命令行直接调用**。

### 📝 转换为 Markdown
- 🧹 自动去除页眉页脚、页码、水印
- 📐 LaTeX 公式、Markdown 表格完美转换
- 🎨 标题层级、列表缩进自动处理
- 📊 内置质量评分（0-100）

### 📄 转换为 Word
- 🎨 精确模式：尽可能还原字体、颜色、对齐方式
- ⚡ 快速模式：仅提取内容结构，速度快成本低
- 📊 表格样式保留

### 🌐 Web UI
- 浏览器端可视化操作，拖拽上传
- 逐页实时进度条 + 预计剩余时间
- Markdown 在线预览（公式渲染 + 代码高亮）
- 暗色/亮色主题切换
- API 连接测试

> 💡 **支持任何 OpenAI 兼容的视觉模型**：GPT-4o、Claude、通义千问、智谱 GLM、DeepSeek 等。

---

## ✨ 特性

| 特性 | 说明 |
|------|------|
| 智能识别 | 标题、段落、列表、公式、表格、代码块 |
| 页级缓存 | 成功页自动缓存，重跑只处理失败页 |
| 恢复模式 | `--resume` 仅补处理失败/未完成页 |
| 并发处理 | 多线程并行调用模型，大幅缩短耗时 |
| 分段处理 | 超长文档自动分段，避免上下文过长 |
| 批量转换 | 一次处理整个文件夹 |
| 质量检查 | 公式配对、表格格式、编码检测 |
| Web UI | 浏览器操作 + WebSocket 实时进度 |

---

## 🚀 快速开始

### 📦 安装

```powershell
# 克隆项目
git clone https://github.com/kelongyan/pdf2ai-converter.git
cd pdf2ai-converter

# 创建虚拟环境
python -m venv venv
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### ⚙️ 配置

复制配置模板并填入 API 信息：

```powershell
cp config.yaml.example config.yaml
```

或直接运行启动器，交互式配置：

```powershell
.\start.ps1
```

---

## 🎮 使用方法

### 方式 1：Web UI（推荐）

```powershell
.\start_web.ps1
```

自动打开浏览器访问 `http://localhost:8000`，拖拽 PDF 即可开始转换。

**开发模式**（前后端分离热重载）：

```powershell
# 终端 1：后端
python server.py --dev

# 终端 2：前端
cd web
npm install
npm run dev
```

### 方式 2：交互式启动器

```powershell
.\start.ps1
```

跟着菜单走：选择配置 → 选择文件 → 选择格式 → 等待转换 → 查看质量报告。

### 方式 3：命令行

**转换为 Markdown：**
```powershell
python main.py paper.pdf
python main.py paper.pdf output.md
python main.py paper.pdf --resume        # 仅补处理失败页
```

**转换为 Word：**
```powershell
python main_word.py paper.pdf                        # 精确模式（默认）
python main_word.py paper.pdf output.docx fast       # 快速模式
python main_word.py paper.pdf output.docx precise --resume  # 恢复模式
```

---

## ⚙️ 配置

### 基础配置（config.yaml）

```yaml
model:
  type: openai_compatible
  name: gpt-4o                # 模型名称
  api_key: your-key-here      # API 密钥
  base_url: https://api.openai.com/v1

pdf:
  dpi: 150                    # 分辨率（150=标准，300=高清）

processing:
  concurrency: 3              # 并发数（多线程处理未缓存页）

cache:
  enabled: true               # 页级缓存开关
  prompt_version: "1"         # 修改 prompt 后递增此值以清除缓存

chunk_size: 10                # 分段大小（每次处理页数）
quality_check: true           # 质量检查开关
```

### 配置管理

- **CLI 启动器**：交互式创建/切换 API 配置
- **Web UI 设置页**：可视化管理配置 + 连接测试

配置存储在 `.config.json`（API profiles）和 `config.yaml`（运行时参数）。

---

## 📊 效果展示

### 输入：学术论文 PDF
```
📄 6 页学术论文 - 复杂公式、多个表格、参考文献
```

### 输出：完美 Markdown
```markdown
# Semantically-Supervised Identity-Attribute Decoupling

## Abstract
Text-to-Image Person Re-Identification faces...

$$
f_{\text{id}}^i = g \odot \hat{f}_{\text{id}}
$$

| Method | mAP(%) | R-1(%) |
|--------|--------|--------|
| Ours   | 72.61  | 79.93  |
```

### 质量报告
```
📊 质量检查报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 统计信息：总行数 286 · 标题 17 · 公式 113 ✅ · 表格 40 ✅
🎯 质量得分：100/100 ✅ 通过
```

---

## 📁 项目结构

```
pdf2ai-converter/
├── start.ps1                    # CLI 启动脚本
├── start_web.ps1                # Web UI 启动脚本
├── server.py                    # FastAPI 入口
├── launcher.py                  # 交互式 CLI 启动器
├── main.py                      # Markdown 转换管道
├── main_word.py                 # Word 转换管道
├── pipeline_utils.py            # 共享管道逻辑（缓存、并发、进度）
├── pdf_processor.py             # PDF → 图片
├── cache_manager.py             # 页级缓存
├── quality_checker.py           # Markdown 质量检查
├── config_manager.py            # 配置 profile 管理
├── config_validator.py          # 配置校验
├── config_defaults.py           # 默认配置值
├── models/                      # 模型适配器
│   ├── base.py                 # VisionModel 抽象基类
│   ├── openai_compatible.py    # OpenAI 兼容接口（含重试）
│   └── word_generator.py       # Word 两阶段生成器
├── api/                         # Web 后端（FastAPI）
│   ├── app.py                  # App 工厂 + 路由挂载
│   ├── routes/                 # REST + WebSocket 端点
│   ├── schemas/                # Pydantic 数据模型
│   └── services/               # 任务管理 + 进度广播
├── web/                         # React 前端
│   ├── src/                    # TypeScript 源码
│   └── dist/                   # 生产构建产物（gitignore）
├── tests/                       # pytest 测试套件
├── config.yaml.example          # 配置模板
└── requirements.txt             # Python 依赖
```

---

## 🎨 高级功能

### 🔁 恢复模式

转换中断或部分页面失败时，使用 `--resume` 仅重试失败页，已成功的页面自动跳过：

```powershell
python main.py paper.pdf --resume
python main_word.py paper.pdf output.docx precise --resume
```

Web UI 中勾选"恢复模式"复选框即可。

### ⚡ 并发处理

配置 `processing.concurrency` 开启多线程并行处理未缓存页面：

```yaml
processing:
  concurrency: 5  # 5 个线程并行
```

### 📦 分段处理

超长文档自动分段，避免上下文过长：

```yaml
chunk_size: 5  # 每 5 页一段
```

### 📄 Word 转换模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `fast` | 仅提取内容结构 | 快速提取，不在意样式 |
| `precise` | 保留字体、颜色、对齐 | 正式文档，需要原样排版 |

### 🔍 质量检查（Markdown）

自动检查内容长度、公式配对、表格格式、编码问题，输出 0-100 质量评分。

---

## 🤔 常见问题

<details>
<summary><b>Q: 支持哪些语言的 PDF？</b></summary>

A: 支持所有语言，取决于你选择的视觉大模型能力。
</details>

<details>
<summary><b>Q: Word 转换能完美还原样式吗？</b></summary>

A: 精确模式会尽力还原，但特殊字体、复杂布局可能有偏差，建议转换后人工微调。
</details>

<details>
<summary><b>Q: 可以离线使用吗？</b></summary>

A: 需要调用在线 API。如果要离线，可以部署本地大模型（如 Ollama + LLaVA）并修改 `base_url` 指向本地。
</details>

<details>
<summary><b>Q: Web UI 需要安装 Node.js 吗？</b></summary>

A: 生产模式不需要——前端已预构建到 `web/dist/`，FastAPI 直接 serve 静态文件。只有开发模式（热重载）才需要 Node.js。
</details>

---

## 🛠️ 开发

```powershell
# 运行测试
python -m pytest tests -v

# 语法检查
python -m compileall main.py main_word.py pipeline_utils.py api server.py models tests

# 前端构建
cd web && npm run build
```

欢迎 PR！请确保测试通过、代码风格一致。

---

## 📜 开源协议

MIT License

---

## 🙏 致谢

- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF 处理
- [python-docx](https://github.com/python-openxml/python-docx) - Word 文档生成
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [React](https://react.dev/) + [Tailwind CSS](https://tailwindcss.com/) - 前端
- [Framer Motion](https://www.framer.com/motion/) - 动画
- [Rich](https://github.com/Textualize/rich) - 终端美化

---

<div align="center">

**觉得有用？给个 ⭐ 吧！**

Made with ❤️ by [扎西德勒](https://github.com/kelongyan)

[🐛 报告 Bug](https://github.com/kelongyan/pdf2ai-converter/issues) • [💡 提建议](https://github.com/kelongyan/pdf2ai-converter/issues)

</div>
