# 农业新闻分析与预警系统

Agricultural News Analysis & Early Warning System

## 一分钟上手

### 第一步：确保装了 Python

打开命令行 / PowerShell，输入：
```
python --version
```
如果显示 `Python 3.10+` 就没问题。没装的话先去 https://python.org 下载安装。

### 第二步：安装依赖

在 `agricultural-news-analysis` 文件夹里打开命令行，执行：
```
pip install aiohttp lxml cssselect
```
> 只需装这3个核心包。整个系统不需要 GPU、不需要下载 AI 模型，开箱即用。

### 第三步：启动

**方法 A — 双击（推荐）**
```
双击 "启动系统.bat"
```

**方法 B — 命令行**
```
python main.py
```

### 第四步：打开浏览器

访问：http://localhost:8000/dashboard

你会看到仪表盘，包含新闻分类、趋势、情感分析、热点词云和预警列表。

---

## 项目结构速览

```
agricultural-news-analysis/
│
├── main.py              ◀── 入口文件（运行它就行）
├── config.py                全局配置（端口、抓取间隔等）
├── 启动系统.bat             双击启动脚本（Windows）
│
├── crawler/                 爬虫模块（自动抓取新闻和预警）
├── nlp/                     分析模块（分类、摘要、情感、热点）
├── backend/                 后端服务（数据库、API、定时任务）
├── frontend/                前端页面（仪表盘HTML/CSS/JS）
├── data/                    数据存储目录（数据库+缓存）
└── tests/                   测试用例
```

---

## 拷贝到其他电脑

想把整个系统搬到另一台电脑？只需4步：

**1. 复制文件夹** — 把整个 `agricultural-news-analysis` 文件夹拷贝到U盘或网络传过去

**2. 确保目标电脑有 Python** — 必须是 Python 3.10 或更高版本（推荐 3.11，兼容性最好）

**3. 安装依赖** — 在目标电脑的项目目录下打开命令行：
```bash
pip install aiohttp lxml cssselect
```

**4. 启动** — 双击 `启动系统.bat` 或运行 `python main.py`

> 就这么简单。不需要配置环境变量，不需要改任何代码。

> **注意**：如果是 Windows 电脑，双击 `.bat` 文件就行。Mac/Linux 用户用 `python main.py`。

---

## 常见问题

| 问题 | 原因 | 解决方法 |
|------|------|---------|
| `pip 找不到命令` | Python 没装好 | 重新安装 Python，勾选"Add to PATH" |
| `端口 8000 被占用` | 已有一个服务在跑 | 关闭旧的服务，或改 config.py 里的 PORT = 8080 |
| `浏览器打开空白` | 没连上服务器 | 确认命令行窗口没有关闭，且显示 "服务启动" |
| `图表不显示` | ECharts 需要联网加载 | 仪表盘需要访问 CDN 加载图表库 |
| `爬虫抓不到新闻` | 网站结构变化 | 这是正常的。不影响分析功能（可以用测试数据） |

---

## 配置说明

编辑 `config.py` 可调整：

```python
HOST = "0.0.0.0"         # 监听地址（0.0.0.0 表示局域网也可访问）
PORT = 8000               # 端口号
MODEL_MODE = "mock"       # "mock"=规则模式（无需模型）| "local"=本地模型（需transformers）
SCHEDULER_ENABLED = True  # 是否开启自动抓取
CRAWL_INTERVAL_MINUTES = 60   # 抓取间隔（分钟）
REQUEST_DELAY = 2.0       # 爬虫请求间隔（秒）
```

---

## API 接口

| 地址 | 说明 |
|------|------|
| `http://localhost:8000/dashboard` | 可视化仪表盘 |
| `http://localhost:8000/api/statistics` | 数据统计 |
| `http://localhost:8000/api/news` | 新闻列表 |
| `http://localhost:8000/api/disasters` | 灾害预警 |
| `http://localhost:8000/api/analysis` | 完整分析报告 |
| `http://localhost:8000/api/health` | 健康检查 |
