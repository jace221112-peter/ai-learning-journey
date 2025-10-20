# 🤖 AI 新闻智能体系统（LangChain + DeepSeek）

自动抓取最新 AI 新闻 → 生成报道 → 润色优化 → 输出成品。  
本项目基于 **LangChain 框架** 构建，展示了如何通过 **ReAct 思维链** 与 **多智能体协作机制（Multi-Agent）**，实现一个能够自主决策和分工合作的智能新闻系统。

---

## 🧩 一、项目概述

系统由三个智能体组成：

1. **News Agent** —— 抓取最新 AI 新闻（RSS源）
2. **Writer Agent** —— 根据新闻生成中文报道
3. **Editor Agent** —— 对稿件进行润色与结构优化

三个智能体按顺序协作，通过 ReAct 推理机制（Think → Act → Observe）完成新闻生成全过程。

---

## ⚙️ 二、项目结构

```bash
ai_news_agent/
│
├── .env                # 环境变量配置（DeepSeek API Key）
├── requirements.txt    # 依赖包
│
├── config.py           # 模型配置与环境加载
├── tools.py            # 工具函数：抓新闻 / 写稿 / 润色
├── agents.py           # 智能体注册与定义
└── main.py             # 主流程逻辑
```

---

## 🧠 三、核心机制说明

### 1️⃣ ReAct 思维链

ReAct（Reason + Act）是一种让大语言模型“先思考再行动”的机制。  
每次执行时，模型会输出以下过程：

```
Thought: 我需要获取最新的AI新闻
Action: NewsFetcher
Action Input: AI领域新闻
Observation: 获取了5条新闻
Thought: 我可以根据这些新闻撰写报道
Action: DraftWriter
Observation: 生成初稿
Final Answer: 输出新闻稿
```

模型会不断循环“思考—执行—观察”，直到生成最终结果。  
这使得它具备了自我推理和动态决策的能力。

---

### 2️⃣ 多智能体协作（Multi-Agent Cooperation）

系统内的三个智能体相互独立，但由主流程统一调度：

```text
Manager Agent → 调用 News Agent → Writer Agent → Editor Agent
```

每个 Agent 都绑定独立的工具（Tool）与任务描述，  
LangChain 在后台自动传递结果，实现顺序决策与数据流转。

执行逻辑示例：

```python
news_result = news_agent.run("请获取AI领域最新新闻。")
draft_result = writer_agent.run(f"请根据以下新闻撰写报道：{news_result}")
final_article = editor_agent.run(f"请润色以下报道：{draft_result}")
```

---

## 🔍 四、功能说明

| 模块 | 功能 |
|------|------|
| **NewsFetcher** | 抓取并清洗 Google News RSS 中的 AI 新闻 |
| **DraftWriter** | 将新闻摘要转化为连贯报道 |
| **Editor** | 润色、调整逻辑结构与语言表达 |
| **DeepSeek 模型** | 提供自然语言生成与润色能力 |
| **LangChain Agent** | 管理思维链、工具调用与智能体状态 |

---

## 🧩 五、技术实现细节

### 1️⃣ RSS 新闻抓取
通过 `feedparser` 获取 Google News RSS 源：

```python
feed = feedparser.parse("https://news.google.com/rss/search?q=artificial+intelligence")
```

解析标题与摘要后，利用正则清洗 HTML 标签，输出结构化结果。

---

### 2️⃣ 工具（Tool）封装

每个功能（抓新闻、写稿、润色）都被封装为一个 `Tool` 对象：

```python
news_tool = Tool(
    name="NewsFetcher",
    func=get_ai_news,
    description="抓取AI新闻"
)
```

LangChain 会自动根据上下文调用这些工具，实现自主任务规划。

---

### 3️⃣ Agent 初始化

```python
news_agent = initialize_agent([news_tool], llm, agent_type="zero-shot-react-description", verbose=True)
writer_agent = initialize_agent([draft_tool], llm, agent_type="zero-shot-react-description", verbose=True)
editor_agent = initialize_agent([edit_tool], llm, agent_type="zero-shot-react-description", verbose=True)
```

---

## 💾 六、运行方式

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
echo "DEEPSEEK_API_KEY=你的APIKEY" > .env

# 运行程序
python main.py
```

运行后将自动生成 `final_ai_news.txt`，包含完整的中文新闻报道。

---

## 📈 七、项目特点

| 特性 | 说明 |
|------|------|
| **ReAct 推理链** | 模型具备自主思考与行动能力 |
| **多Agent协作** | 智能体分工明确，流程自然衔接 |
| **RSS实时数据** | 抓取当日最新AI新闻 |
| **自然语言润色** | 生成地道的中文报道风格 |
| **模块化设计** | 结构清晰，便于扩展与部署 |

---

## 🌐 八、扩展方向

| 方向 | 内容 |
|------|------|
| 视频脚本生成 | 将新闻稿自动转化为短视频解说稿 |
| 翻译智能体 | 自动生成中英文双语新闻稿 |
| 持久记忆 | 记录用户偏好和历史任务 |
| 部署服务化 | 使用 LangServe / FastAPI 发布为 API 服务 |
