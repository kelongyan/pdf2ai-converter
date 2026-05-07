<div align="center">

# 📄✨ PDF 转 Markdown 魔法工具

*让 AI 帮你读 PDF，一键变身 Markdown！*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/yourusername/pdf2md/pulls)

[✨ 特性](#-特性) • [🚀 快速开始](#-快速开始) • [🎮 使用方法](#-使用方法) • [⚙️ 配置](#️-配置)

</div>

---

## 🎯 这是什么？

厌倦了手动复制 PDF 内容？被页眉页脚搞得头大？

这个工具用 **AI 大模型** 智能识别 PDF，自动：
- 🧹 **去除页眉页脚** - 再也不用手动删除页码和水印
- 📐 **保留公式表格** - LaTeX 公式、Markdown 表格完美转换
- 🎨 **格式规范** - 标题层级、列表缩进自动处理
- ⚡ **批量处理** - 一次转换整个文件夹

> 💡 **支持任何 OpenAI 兼容的视觉模型**：GPT-4V、Claude、通义千问、智谱 GLM...

---

## ✨ 特性

### 🤖 智能识别
- 自动识别标题、段落、列表
- 完美保留 LaTeX 公式（`$...$` 和 `$$...$$`）
- 表格转 Markdown 语法
- 代码块自动标记

### 🎨 交互式界面
```
╔══════════════════════════════════════════════════════════╗
║          🚀 PDF 转 Markdown 工具 v2.0                   ║
╚══════════════════════════════════════════════════════════╝

  [1] 🎯 快速转换（单个文件）
  [2] 📁 批量处理（文件夹）
  [3] ⚙️  配置管理
```

### 📊 质量保证
- ✅ 实时进度条
- 📈 质量评分（0-100）
- 🔍 自动检查公式、表格、编码
- 📝 详细统计报告

### 🚀 性能优化
- 📦 **分段处理** - 超长文档自动分段，避免上下文过长
- ⚡ **进度可视化** - 实时显示处理速度和剩余时间
- 💾 **配置保存** - 一次配置，永久使用

---

## 🚀 快速开始

### 📦 安装

```powershell
# 1. 克隆项目
git clone https://github.com/yourusername/pdf2md.git
cd pdf2md

# 2. 创建虚拟环境
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. 安装依赖
pip install -r requirements.txt
```

### ⚙️ 配置

复制配置模板并填入你的 API 信息：

```powershell
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入 API Key
```

或者直接运行启动器，交互式配置：

```powershell
.\start.ps1
```

---

## 🎮 使用方法

### 方式 1️⃣：交互式启动器（推荐）

```powershell
.\start.ps1
```

然后跟着菜单走：
1. 首次使用会引导你输入 API 信息
2. 选择 PDF 文件（图形化选择器）
3. 坐等 AI 处理
4. 查看质量报告

### 方式 2️⃣：命令行

```powershell
# 单个文件
python main.py paper.pdf

# 指定输出路径
python main.py paper.pdf output.md

# 批量处理（在启动器中选择）
```

---

## 📊 效果展示

### 输入：学术论文 PDF
```
📄 6 页学术论文
- 复杂公式
- 多个表格
- 参考文献
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

📈 统计信息：
  总行数：286
  标题数：17
  公式数：113 ✅
  表格数：40 ✅

🎯 质量得分：100/100

✅ 通过
```

---

## ⚙️ 配置

### 基础配置

```yaml
model:
  type: openai_compatible
  name: qwen3.6-plus          # 模型名称
  api_key: your-key-here      # API 密钥
  base_url: https://api.xxx   # API 地址

pdf:
  dpi: 150                    # 分辨率（150=标准，300=高清）

chunk_size: 10                # 分段大小（每次处理页数）
quality_check: true           # 质量检查开关
```

---

## 📁 项目结构

```
pdf2md/
├── 🚀 start.ps1                 # 一键启动脚本
├── 🎮 launcher.py               # 交互式启动器
├── ⚙️ config_manager.py         # 配置管理
├── 🔧 main.py                   # 主处理程序
├── 📄 pdf_processor.py          # PDF 转图片
├── 🔍 quality_checker.py        # 质量检查
├── 📦 models/                   # 模型适配器
│   ├── base.py                 # 抽象基类
│   └── openai_compatible.py    # OpenAI 兼容接口
├── 📋 config.yaml.example       # 配置模板
├── 📝 requirements.txt          # 依赖列表
└── 📖 README.md                 # 你正在看的文档
```

---

## 🎨 高级功能

### 📦 分段处理

超长文档（50+ 页）自动分段，避免上下文过长：

```yaml
chunk_size: 5  # 每 5 页一段
```

### 🔍 质量检查

自动检查：
- ✅ 内容长度是否合理
- ✅ 公式符号是否配对
- ✅ 表格格式是否正确
- ✅ 是否有乱码或模型错误

### 📁 批量处理

在启动器中选择"批量处理"，一次转换整个文件夹的 PDF。

---

## 🤔 常见问题

<details>
<summary><b>Q: 支持哪些语言的 PDF？</b></summary>

A: 支持所有语言！取决于你选择的视觉大模型能力。
</details>

<details>
<summary><b>Q: 质量检查不通过怎么办？</b></summary>

A: 查看报告中的具体问题：
- 公式未配对 → 检查原 PDF 是否有特殊符号
- 内容过短 → 可能模型不支持视觉，换个模型
- 表格格式错误 → 手动补充分隔符
</details>

<details>
<summary><b>Q: 可以离线使用吗？</b></summary>

A: 需要调用在线 API。如果要离线，可以：
1. 部署本地大模型（如 Ollama + LLaVA）
2. 修改 `models/` 适配器支持本地模型
</details>

---

## 🛠️ 开发

### 贡献代码

欢迎 PR！请确保：
- ✅ 代码风格一致
- ✅ 添加必要的注释
- ✅ 测试通过
- ✅ 更新文档

---

## 📜 开源协议

MIT License - 随便用，记得点个 ⭐

---

## 🙏 致谢

- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF 处理
- [Rich](https://github.com/Textualize/rich) - 终端美化
- [OpenAI](https://openai.com/) - API 标准

---

<div align="center">

**觉得有用？给个 ⭐ 吧！**

Made with ❤️ by [Your Name]

[🐛 报告 Bug](https://github.com/yourusername/pdf2md/issues) • [💡 提建议](https://github.com/yourusername/pdf2md/issues) • [📖 文档](https://github.com/yourusername/pdf2md/wiki)

</div>
