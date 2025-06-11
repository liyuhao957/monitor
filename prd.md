你是一名经验丰富的 Python 全栈开发助手，擅长使用 Flask/FastAPI 构建轻量级 Web 应用，熟悉 Playwright/Puppeteer 实现页面自动化渲染、内容提取与网页截图，具备丰富的定时调度、通知集成（如 Telegram/飞书）、配置管理与日志监控经验。

你好，Cursor：

请帮我开发一个通用型网页内容监控系统，满足以下完整功能需求：

---

## 一、主要功能模块

### 1. 页面加载

* 使用 Playwright 加载网页（支持 JavaScript 渲染）；
* 页面加载策略为 `networkidle`；
* 可获取页面 innerText、完整 HTML、截图（PNG）等；
* 截图保存在本地文件系统中，按照任务名称+时间戳命名。

### 2. 内容提取

* 每个任务支持以下三种提取规则格式（自动识别）：

  * `regex:` 前缀：正则表达式提取纯文本；
  * `css:` 前缀：CSS Selector 提取 DOM 内容；
  * `xpath:` 前缀：XPath 表达式提取 DOM 内容；
* 可对提取结果进行预处理：去 HTML 标签、解码实体、统一空格与换行。

### 3. 内容变更判断

* 首次运行时初始化，不触发报警；
* 对提取结果标准化后进行新旧值比对；
* 支持失败重试机制（最多 3 次，间隔 30 秒）；
* 同一任务在一个周期内仅发送一次告警（防抖机制）；
* 所有提取结果持久化保存，用于下一次对比（支持文件）。

### 4. 多任务配置

* 支持通过 `config.yaml` 定义多个监控任务；
* 每个任务包含：

  * 任务名称；
  * URL；
  * 提取规则；
  * 监控频率（如 10m、1h）；
  * 是否启用截图；
  * 通知方式及参数（Telegram / 飞书）；
  * 存储策略。

### 5. 通知机制

* 支持以下两种方式：

  * **Telegram Bot**（需 bot\_token + chat\_id）；
  * **飞书机器人**（需 webhook）；
* 通知内容包括任务名、变更前后摘要、URL、截图文件路径；
* 支持 Markdown 格式渲染；
* 通知失败时自动记录错误。

### 6. 调度与执行

* 每个任务按其设定的周期调度执行；
* 使用内置调度器（如 `apscheduler`）异步并发运行任务；
* 日志输出至文件，记录每次检测、对比、通知与异常。

---

## 二、Web UI 管理后台（可选但建议实现）

* 使用 Flask 或 FastAPI + Vue 或 React；
* 实现任务列表查看、增删改查、启停控制、日志查看；
* 支持热加载配置并重载任务；
* 界面支持简体中文。

---

## 三、CLI 启动说明与依赖安装

### 1. 依赖安装

```bash
pip install -r requirements.txt
playwright install
```

### 2. 启动方式（支持默认配置和自定义 config）

```bash
# 使用默认 config.yaml
python monitor.py

# 使用自定义配置文件
MONITOR_CONFIG=custom_config.yaml python monitor.py
# 或
python monitor.py --config custom_config.yaml
```

---

## 四、输出要求

```md
1. 主程序按模块组织，功能清晰（如：页面加载、内容提取、对比判断、通知发送、调度控制等）；
2. 包含 Web UI 示例（前后端分离或集成均可）；
3. 提供 config.yaml 模板文件（注释清晰）；
4. 依赖项统一管理于 requirements.txt；
5. 日志文件输出到本地（推荐 logs/ 目录）；
6. 项目结构清晰、可维护，适合继续拓展。
```
