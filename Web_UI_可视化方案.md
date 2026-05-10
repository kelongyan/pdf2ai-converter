# PDF2AI Converter Web UI 可视化方案

> 目标：为 PDF2AI Converter 构建浏览器端可视化界面，替代当前 CLI + Tkinter 交互方式。
> 场景：本地单人使用，localhost 访问。
> 技术栈：FastAPI 后端 + React 18 + shadcn/ui + Tailwind CSS + Framer Motion 前端。
> 设计标杆：Linear / Vercel Dashboard 级别的工具型产品质感。

---

## 一、技术栈选型与论证

### 最终技术栈

```
后端：FastAPI + uvicorn
前端：React 18 + Vite + TypeScript
UI 组件：shadcn/ui（基于 Radix Primitives）
样式：Tailwind CSS
动画：Framer Motion
状态管理：Zustand
API 层：TanStack Query
Markdown 预览：react-markdown + remark-gfm + rehype-katex + rehype-highlight
代码高亮：Shiki
图标：Lucide React
```

### 后端：FastAPI

| 考量 | 结论 |
|------|------|
| 语言一致性 | 项目已是 Python，无需引入新语言 |
| 异步支持 | 原生 async，适合长时间转换任务 + WebSocket 推送 |
| 自动文档 | 内置 Swagger UI，开发调试方便 |
| 轻量 | 比 Django 轻得多，适合工具型项目 |
| 生态 | uvicorn 启动，单命令运行 |

### 前端：为什么选 React 而非 Vue

| 维度 | React 18 | Vue 3 |
|------|----------|-------|
| shadcn 支持 | 原版，功能最完整，更新最快 | shadcn-vue 社区移植，滞后 |
| 动画生态 | Framer Motion（业界无对手） | 无同级方案 |
| Markdown 渲染 | react-markdown + rehype 插件链（最强） | markdown-it（够用但扩展性弱） |
| TypeScript | 最成熟，类型推导最完善 | 好，但 JSX 类型不如 React |
| 生态深度 | 最大社区，任何需求都有成熟方案 | 好，但长尾场景库少 |

### 为什么选 shadcn/ui 而非传统组件库

| 维度 | shadcn/ui | Naive UI / Element Plus / Ant Design |
|------|-----------|--------------------------------------|
| 设计质量 | 极高（Linear/Vercel 同款质感） | 中等（通用企业风） |
| 定制性 | 源码级（组件直接在项目中，完全可控） | 黑盒（受限于 API 暴露的 props） |
| 底层 | Radix Primitives（无障碍标杆） | 各自实现 |
| 暗色模式 | 原生支持，过渡自然 | 需额外配置 |
| 风格 | 现代极简，像原生桌面应用 | 偏传统 Web 应用 |
| 体积 | 按需引入，tree-shaking 完美 | 整包引入或配置复杂 |

### 为什么加 Framer Motion

Framer Motion 是 React 动画的事实标准，核心能力：

- **Spring physics**：弹簧物理动画，有质量感和惯性，不是机械的 ease-in-out
- **Layout animations**：列表增删、尺寸变化自动过渡，零配置
- **AnimatePresence**：元素卸载时的退出动画（任务完成淡出、错误提示消失）
- **Shared layout transitions**：跨组件的共享元素动画（任务卡片展开为详情面板）
- **Gesture support**：拖拽、hover、tap 的物理反馈

这是"能用"和"好用"的分界线——没有它，UI 是静态跳变的；有了它，每个交互都有物理感的反馈。

### 为什么不选其他方案

| 方案 | 否决原因 |
|------|----------|
| Streamlit / Gradio | 定制性差，无法实现精细动画和复杂交互 |
| Electron / Tauri | 核心逻辑是 Python，套壳增加复杂度无实质收益 |
| Vue + Naive UI | shadcn 原版只有 React，Vue 移植版滞后；无 Framer Motion 对等方案 |
| HTMX + Alpine | 实时进度、Markdown 预览等复杂交互难以实现 |
| Svelte | shadcn-svelte 社区维护，生态深度不足 |

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    浏览器 (localhost:5173)                 │
│                                                         │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  │
│  │ 上传区域 │  │ 任务列表  │  │ 实时进度 │  │ 结果预览  │  │
│  └────┬────┘  └────┬─────┘  └────┬────┘  └────┬─────┘  │
│       │            │             │             │         │
└───────┼────────────┼─────────────┼─────────────┼─────────┘
        │ REST API   │ REST API    │ WebSocket   │ REST API
        ▼            ▼             ▼             ▼
┌─────────────────────────────────────────────────────────┐
│                 FastAPI 后端 (localhost:8000)              │
│                                                         │
│  ┌──────────┐  ┌───────────┐  ┌───────────────────────┐ │
│  │ 文件管理  │  │ 任务调度器 │  │ WebSocket 进度广播     │ │
│  └────┬─────┘  └─────┬─────┘  └───────────┬───────────┘ │
│       │              │                     │             │
│       ▼              ▼                     │             │
│  ┌──────────────────────────────────────┐  │             │
│  │         转换引擎（复用现有管道）        │◄─┘             │
│  │  pdf_processor → model → cache → output │             │
│  └──────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

### 关键设计决策

1. **前后端分离但同进程部署**：开发时 Vite dev server + FastAPI 分别启动；生产时前端构建产物放入 `web/dist/`，FastAPI 直接 serve 静态文件，用户只需启动一个进程。

2. **任务异步化**：转换是耗时操作（几十秒到几分钟），不能阻塞 HTTP 请求。后端用 `asyncio.to_thread` 在后台执行，前端通过 WebSocket 接收实时进度。

3. **复用现有管道**：不重写转换逻辑，而是给 `main.py` / `main_word.py` 的 `main()` 函数增加可选的 `progress_callback` 参数。CLI 不传则行为不变，Web 注入回调获得实时进度。

---

## 三、目录结构

```
pdf2ai-converter/
├── server.py                  # FastAPI 入口，一键启动
├── api/
│   ├── __init__.py
│   ├── app.py                 # FastAPI app 定义、中间件、静态文件挂载
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── convert.py         # 转换任务相关接口
│   │   ├── files.py           # 文件上传/下载
│   │   ├── config.py          # 配置管理接口
│   │   └── ws.py              # WebSocket 进度推送
│   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── task.py
│   │   └── config.py
│   └── services/
│       ├── __init__.py
│       ├── task_manager.py    # 任务生命周期管理
│       └── progress.py        # 进度收集与广播
├── web/                       # React 前端项目
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── components.json        # shadcn/ui 配置
│   ├── index.html
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── router.tsx
│   │   ├── lib/utils.ts       # shadcn/ui 工具函数
│   │   ├── hooks/             # 自定义 hooks（WebSocket、API）
│   │   ├── stores/            # Zustand 状态管理
│   │   ├── components/
│   │   │   ├── ui/            # shadcn/ui 基础组件（CLI 自动生成）
│   │   │   ├── file-upload.tsx
│   │   │   ├── task-list.tsx
│   │   │   ├── progress-panel.tsx
│   │   │   ├── result-preview.tsx
│   │   │   ├── config-panel.tsx
│   │   │   └── convert-options.tsx
│   │   ├── pages/
│   │   │   ├── home.tsx
│   │   │   ├── history.tsx
│   │   │   └── settings.tsx
│   │   └── styles/globals.css # Tailwind 指令 + CSS 变量主题
│   └── dist/                  # 生产构建产物（git ignore）
├── # ... 现有文件不变
```

---

## 四、后端 API 设计

### 4.1 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload` | 上传 PDF 文件，返回 file_id |
| POST | `/api/convert` | 创建转换任务（指定格式、模式、是否 resume） |
| GET | `/api/tasks` | 列出所有任务 |
| GET | `/api/tasks/{id}` | 查询单个任务详情 |
| DELETE | `/api/tasks/{id}` | 取消/删除任务 |
| GET | `/api/tasks/{id}/download` | 下载结果文件 |
| GET | `/api/tasks/{id}/preview` | 获取 Markdown 预览内容 |
| WS | `/api/ws/progress` | WebSocket 实时进度推送 |
| GET | `/api/config/profiles` | 列出所有配置 |
| POST | `/api/config/profiles` | 创建/更新配置 |
| DELETE | `/api/config/profiles/{name}` | 删除配置 |

### 4.2 核心数据结构

**任务状态字段**：id、文件名、输出格式、模式、状态（pending/processing/completed/failed/cancelled）、进度详情、创建时间、完成时间、输出路径、错误信息。

**进度详情字段**：当前页、总页数、缓存命中数、失败页列表、阶段（uploading/rendering/processing/writing/done）、描述消息。

### 4.3 WebSocket 消息类型

- `progress`：逐页进度更新（阶段、当前页、总页数、缓存命中）
- `completed`：任务完成（下载路径、耗时、统计信息）
- `error`：任务失败（错误消息、失败页列表）

---

## 五、前端页面设计

### 5.1 页面结构（单页应用，3 个视图）

```
┌─────────────────────────────────────────────────────────────┐
│  PDF2AI Converter                    [设置] [历史]           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                                                     │    │
│  │         拖拽 PDF 文件到此处，或点击选择文件            │    │
│  │                                                     │    │
│  │              支持单个文件或批量上传                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─ 转换选项 ──────────────────────────────────────────┐    │
│  │  输出格式：  ○ Markdown   ○ Word                    │    │
│  │  转换模式：  ○ 快速（仅内容） ○ 精确（保留样式）      │    │
│  │  □ 恢复模式（仅补处理失败页）                        │    │
│  │                                                     │    │
│  │                          [ 开始转换 ]                │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─ 任务进度 ──────────────────────────────────────────┐    │
│  │  report.pdf          Markdown    ████████░░ 80%     │    │
│  │  第 16/20 页 · 缓存命中 3 页 · 预计剩余 12s          │    │
│  │                                                     │    │
│  │  paper.pdf           Word/精确   ✅ 完成 (45s)       │    │
│  │  thesis.pdf          Markdown    ❌ 失败 (第7页超时)  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌─ 结果预览 ──────────────────────────────────────────┐    │
│  │  ┌─────────┐  ┌──────────────────────────────────┐  │    │
│  │  │ PDF原文  │  │  # 第一章 引言                    │  │    │
│  │  │ (缩略图) │  │                                  │  │    │
│  │  │         │  │  本文研究了...                     │  │    │
│  │  │         │  │                                  │  │    │
│  │  └─────────┘  └──────────────────────────────────┘  │    │
│  │  [下载文件]  [在文件夹中打开]                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 核心组件职责

| 组件 | 职责 | 动画要点 |
|------|------|----------|
| `file-upload` | 拖拽上传区域，支持多文件 | 拖入时边框呼吸脉冲，文件落入弹性缩放 |
| `convert-options` | 格式/模式选择，恢复模式开关 | 选项切换时 layout 动画平滑过渡 |
| `task-list` | 任务卡片列表，状态标签，操作按钮 | AnimatePresence 驱动增删，交错入场 |
| `progress-panel` | 进度条、当前页、缓存命中、预计时间 | spring 物理进度条，数字跳动动画 |
| `result-preview` | Markdown 渲染 + PDF 缩略图左右对照 | 面板展开的 shared layout transition |
| `config-panel` | API 配置 CRUD，连接测试 | 表单字段的 stagger 入场 |

### 5.3 状态管理思路

- **Zustand** 管理全局状态（任务列表、配置信息），比 Redux 轻量，比 Context 性能好
- **TanStack Query** 管理服务端状态（API 请求缓存、自动重试、loading/error 状态），避免手写 fetch + useState 样板代码
- **WebSocket hook** 接收实时进度，直接更新 Zustand store 中对应任务的 progress 字段
- 断线自动重连（指数退避），重连后通过 REST 拉取最新状态补齐

### 5.4 Markdown 预览思路

使用 react-markdown 的插件架构，将每个 Markdown 元素映射到自定义 React 组件：

- 表格 → shadcn 的 Table 组件渲染
- 代码块 → Shiki 语法高亮（支持主题切换）
- 公式 → KaTeX 实时渲染
- 标题 → 自动生成侧边目录导航

这比简单的 HTML 渲染质量高一个量级。

---

## 六、后端与现有管道的集成

### 6.1 核心问题：如何获取逐页进度

当前 `main.py` / `main_word.py` 的进度通过 `print()` 输出，无法被后端捕获。

**解决方案：进度回调注入**

给 `main()` 函数增加可选的 `progress_callback` 参数。回调对象提供 `on_page_start`、`on_page_done`、`on_complete` 等方法。后端构造一个 `ProgressReporter` 实例注入，内部通过 WebSocket broadcaster 推送给前端。

CLI 调用不传 callback，行为完全不变。Web 调用注入 callback，获得实时进度。这是对现有代码侵入最小的集成方式。

### 6.2 文件管理

- 上传时生成唯一 task ID，PDF 存入 `uploads/{id}/input.pdf`
- 转换结果存入同目录 `uploads/{id}/output.md` 或 `output.docx`
- 提供自动清理机制：超过 N 天的任务目录自动删除（可配置）

---

## 七、启动方式

### 开发模式

两个终端分别启动后端（`python server.py --dev`）和前端（`cd web && npm run dev`）。Vite 配置 proxy 将 `/api` 和 WebSocket 请求代理到 FastAPI。

### 生产模式

前端 `npm run build` 后产物放入 `web/dist/`，FastAPI 同时 serve 静态文件和 API。用户只需运行 `python server.py`，自动打开浏览器访问 `http://localhost:8000`。

### 一键启动

提供 `start_web.ps1` 脚本，调用 venv 中的 Python 启动 server.py。

---

## 八、设计系统规范

为确保 UI 质量达到 Linear/Vercel 水准，需要在编码前定义设计系统：

### 8.1 配色

- 基于 shadcn/ui 默认的 Zinc 中性色阶（11 级灰度）
- 单一强调色：蓝色系（用于主按钮、进度条、链接）
- 语义色：green（成功）、red（失败）、amber（警告）
- 暗色模式为默认主题（工具软件气质）

### 8.2 字体与排版

- 系统字体栈（-apple-system, Inter, sans-serif）
- 5 级字号阶梯：xs(12) / sm(14) / base(16) / lg(18) / xl(20)
- 行高统一 1.5，标题 1.2
- 代码字体：JetBrains Mono / Fira Code

### 8.3 间距

- 4px 基准网格
- 组件内间距：8/12/16px
- 组件间间距：16/24/32px
- 页面边距：32/48px

### 8.4 动画时长规范

| 类型 | 时长 | 场景 |
|------|------|------|
| Micro | 100-150ms | 按钮 hover、focus ring |
| Normal | 200-300ms | 面板展开、选项切换 |
| Page | 400-500ms | 页面过渡、大面板动画 |
| Spring | stiffness: 300, damping: 30 | 进度条、列表项 |

### 8.5 关键视觉特征

- 卡片：1px border（`border-zinc-800`），无阴影或极浅阴影
- 圆角：统一 8px（`rounded-lg`）
- 输入框：内嵌式，背景色区分而非边框突出
- 按钮：primary 实心，secondary 幽灵/outline
- 进度条：圆角胶囊形，spring 动画驱动，带微光扫过效果

---

## 九、关键交互流程

### 9.1 转换流程

```
用户拖入 PDF → 前端上传文件 → 后端返回 file_id
    ↓
用户选择格式/模式 → 点击"开始转换" → 后端创建异步任务
    ↓
WebSocket 推送阶段：rendering → processing (逐页) → writing → done
    ↓
前端实时更新进度条（spring 动画）+ 当前页/总页数/缓存命中
    ↓
完成 → 显示预览面板（Markdown 渲染）+ 下载按钮
```

### 9.2 错误恢复流程

```
任务失败（部分页面超时）
    ↓
前端显示失败详情卡片：哪些页失败、错误原因
    ↓
用户点击"重试失败页"按钮
    ↓
后端以 resume=true 重新执行，只处理失败页
    ↓
WebSocket 推送恢复进度 → 完成后合并结果
```

---

## 十、新增依赖

### 后端（Python）

| 包 | 用途 |
|----|------|
| fastapi | Web 框架 |
| uvicorn[standard] | ASGI 服务器 |
| python-multipart | 文件上传支持 |
| websockets | WebSocket 支持 |
| aiofiles | 异步文件操作 |

### 前端（Node.js）

| 包 | 用途 |
|----|------|
| react / react-dom | UI 框架 |
| react-router-dom | 路由 |
| zustand | 状态管理 |
| @tanstack/react-query | 服务端状态管理 |
| framer-motion | 动画 |
| react-markdown | Markdown 渲染 |
| remark-gfm | GFM 表格/任务列表支持 |
| rehype-katex / katex | LaTeX 公式 |
| shiki | 代码高亮 |
| tailwindcss | 样式 |
| lucide-react | 图标 |
| shadcn/ui 组件 | 通过 CLI 按需添加 |

---

## 十一、实现阶段划分

### Phase 1：最小可用版本（MVP）

**目标**：能上传 PDF、选择格式、看到进度、下载结果。

- FastAPI 骨架 + 文件上传/下载接口
- 转换任务异步执行 + 状态查询
- WebSocket 进度推送（阶段级：开始/完成/失败）
- React 项目初始化 + shadcn/ui + Tailwind + 路由
- 文件上传组件（拖拽 + 点击）
- 转换选项组件（格式/模式）
- 任务列表组件（基础状态显示）
- 下载功能
- `server.py` 一键启动 + 自动打开浏览器

### Phase 2：体验完善

**目标**：逐页进度、预览、暗色模式、配置管理。

- 改造 main() 注入 progress_callback，实现逐页进度推送
- spring 物理进度条 + 预计剩余时间
- Markdown 预览（react-markdown + KaTeX + Shiki）
- 暗色/亮色模式切换（默认暗色）
- 配置管理页面（CRUD profiles + 连接测试）
- Framer Motion 动画：任务列表增删、面板展开、选项切换

### Phase 3：打磨

**目标**：批量、历史、对照预览、错误恢复 UI 化。

- 批量上传 + 批量转换
- 历史记录页面（localStorage 持久化）
- PDF 缩略图 + Markdown 预览左右对照
- 任务取消功能
- 错误重试按钮（resume 模式 UI 化）
- 响应式布局适配
- 微交互打磨（hover 状态、skeleton loading、toast 通知）

---

## 十二、与现有 CLI 的关系

Web UI 是**新增入口**，不替代 CLI。两者共存：

```
pdf2ai-converter/
├── start.ps1          # CLI 启动器（现有，不变）
├── start_web.ps1      # Web UI 启动器（新增）
├── server.py          # Web 后端入口（新增）
├── api/               # Web 后端代码（新增）
├── web/               # React 前端代码（新增）
├── main.py            # CLI 直接调用（仅增加可选 callback 参数）
├── main_word.py       # CLI 直接调用（仅增加可选 callback 参数）
├── launcher.py        # Rich 交互菜单（不变）
└── pipeline_utils.py  # 共享核心逻辑（不变）
```

**共享层**：`pipeline_utils.py`、`cache_manager.py`、`config_manager.py`、`models/` 等核心模块被 CLI 和 Web 共同使用，不重复实现。

---

## 十三、风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| 大文件上传超时 | 用户体验差 | 分片上传 + 上传进度条 |
| 转换任务内存占用 | 大 PDF 可能 OOM | 限制单任务最大页数，前端提示 |
| WebSocket 断连 | 丢失进度更新 | 指数退避自动重连 + 重连后 REST 补齐状态 |
| 前端构建工具链 | 需要 Node.js 环境 | 提供完整脚本，README 说明安装步骤 |
| 端口冲突 | 8000 被占用 | 支持 `--port` 参数，自动寻找可用端口 |
| 动画性能 | 低端设备卡顿 | Framer Motion 默认 GPU 加速，必要时 `will-change` |

---

## 十四、总结

| 维度 | 决策 |
|------|------|
| 后端 | FastAPI + uvicorn |
| 前端框架 | React 18 + Vite + TypeScript |
| UI 组件 | shadcn/ui（Radix Primitives） |
| 样式 | Tailwind CSS |
| 动画 | Framer Motion |
| 状态 | Zustand + TanStack Query |
| Markdown 预览 | react-markdown + rehype 插件链 |
| 通信 | REST API + WebSocket |
| 部署 | 单进程（FastAPI serve 前端构建产物） |
| 启动 | `python server.py` → 自动打开浏览器 |
| 设计质感 | Linear/Vercel 级别，暗色主题为主 |
| 与 CLI 关系 | 并存，共享核心管道，互不影响 |
