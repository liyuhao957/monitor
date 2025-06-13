# Web Content Monitor

这是一个通用的网页内容监控系统，由一个 FastAPI 后端和一个 Vue.js 前端组成。它允许用户通过配置文件或 Web UI 来定义和管理监控任务，当检测到指定网页内容发生显著变化时，会通过多种渠道发送通知。

## ✨ 主要功能

- **动态任务配置**: 通过 `config.yaml` 或 Web UI 实时增、删、改、查监控任务。
- **强大的内容提取**: 支持 `CSS Selector`, `XPath` 和 `Regex` 三种规则提取网页内容。
- **即时变更检测**: 只要内容发生任何变化，立即触发通知。
- **AI智能通知**: 🆕 使用AI分析内容变化，生成简洁美观的通知，告别冗长的HTML摘要。
- **多种通知渠道**: 内置支持 **Telegram** 和 **飞书** 机器人通知。
- **失败重试与截图**: 任务执行失败时自动重试，并可在变更时自动截图存档。
- **现代化 Web UI**: 基于 Vue 3 和 Element Plus 的管理后台，操作直观。
- **异步任务调度**: 使用 APScheduler 并发执行所有监控任务，性能优秀。

## 🏛️ 项目结构

```
.
├── backend/            # FastAPI 后端应用
│   ├── app/
│   │   ├── api/        # API 路由
│   │   ├── core/       # 核心模块 (配置, 调度器)
│   │   ├── services/   # 业务逻辑 (监控, 通知)
│   │   └── main.py     # 应用入口
│   └── requirements.txt
├── frontend/           # Vue.js 前端应用
│   ├── src/
│   └── ...
├── logs/               # 日志文件
├── storage/            # 任务内容持久化存储
├── screenshots/        # 监控截图
└── config.yaml         # 监控任务配置文件
```

## 🚀 快速启动

你需要 **Node.js (v18+)** 和 **Python (v3.9+)** 环境。

### 1. 后端启动

打开**第一个终端窗口**：

```bash
# 进入后端目录
cd backend

# 创建并激活 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate
# (Windows 用户: venv\Scripts\activate)

# 安装依赖
pip install -r requirements.txt

# 首次运行需要安装 Playwright 的浏览器驱动
# 此命令已集成在应用启动事件中，但也可手动执行
playwright install

# 启动后端开发服务器
uvicorn app.main:app --reload
```
后端服务运行在 `http://127.0.0.1:8000`。

### 3. AI智能通知配置（可选）

如果你想使用AI智能通知功能，需要配置OpenAI API：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的OpenAI API密钥
# OPENAI_API_KEY=your_actual_api_key_here
```

**AI功能说明：**
- 启用后，AI会分析内容变化并生成简洁美观的通知
- 支持用自然语言描述监控重点，如"我想监控版本号变化、下载链接更新"
- 如果不配置API密钥，系统会自动回退到传统的HTML摘要通知
- 推荐使用飞书通知以获得最佳的Markdown渲染效果

### 4. 前端启动

打开**第二个终端窗口**：

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动前端开发服务器
# 如果遇到连接后端超时 (ETIMEDOUT) 的问题，请尝试使用下面的命令
# http_proxy="" https_proxy="" npm run dev
npm run dev
```
前端服务运行在 `http://localhost:5173`。在浏览器中打开此地址即可访问管理后台。

## ⚙️ 配置说明

所有任务配置都在根目录的 `config.yaml` 文件中。

- **`default_notification`**: 全局默认的通知设置。
- **`tasks`**: 监控任务列表。

每个任务包含以下字段：
- `name`: (必须) 任务唯一名称。
- `url`: (必须) 要监控的网页 URL。
- `frequency`: (必须) 监控频率，格式为 `数字`+`单位` (s, m, h, d)。例如 `10m`, `1h`。
- `rule`: 提取规则，格式为 `css:selector`, `xpath:expression` 或 `regex:pattern`。
- `enabled`: (可选) 是否启用任务，默认为 `true`。
- `screenshot`: (可选) 是否在每次检测时截图，默认为 `false`。
- `notification`: (可选) 独立的通知配置，会覆盖全局配置。
- `notification_template`: (可选) 自定义通知消息模板。

### 示例 `config.yaml`

```yaml
default_notification:
  telegram:
    enabled: false
    bot_token: "YOUR_TELEGRAM_BOT_TOKEN"
    chat_id: "YOUR_TELEGRAM_CHAT_ID"
  feishu:
    enabled: true
    webhook: "YOUR_FEISHU_WEBHOOK_URL"

tasks:
  - name: "V2EX-热榜"
    url: "https://www.v2ex.com/?tab=hot"
    frequency: "10m"
    rule: "css:span.item_title > a"
    enabled: true
    screenshot: false

  - name: "GitHub-Trending-Python"
    url: "https://github.com/trending/python?since=daily"
    frequency: "1h"
    rule: "css:article.Box-row"
    enabled: true
    screenshot: true
    # 可选的通知模板。如果不提供，则使用默认格式。
    # 可用占位符: {task_name}, {url}, {change_ratio}, {old_summary}, {new_summary}
    notification_template: "【{task_name}】发生更新！\n变更幅度: {change_ratio}\n摘要:\n{new_summary}"

```

---
*This project was built with the assistance of an AI programming partner.* 