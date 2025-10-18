# Day 3 · 从 RAG 到“决策型”Agent（出行助手）

> 主题：让模型**结合事实**给建议：识别出门意图 → 查询天气 → 由 LLM 自主生成出行建议。

---

## 1) 今天做了什么（TL;DR）
- 写了一个 **出行助手**：当我说“想出门”“要不要带伞”等，它会：  
  ① 识别出门场景 → ② 调用天气接口拿**真实数据** → ③ 把事实交给 DeepSeek，由它**自己组织建议**。  
- 与 Day 2 的区别：不再是模板式回复；回答**基于事实**、语气自然。  
- 还没做到的：是否调用工具的决定权仍是**规则触发**（关键词）。这会在 Day 4 升级为“模型先产出**计划 JSON**，我再执行”。

---

## 2) 项目结构
```
Day3_ActionChain_Agent/
├── app.py                 # 主程序：加载 env、天气工具、LLM 封装、agent 流程
├── .env                   # 密钥/接口地址（只在本地）
└── requirements.txt       # 依赖：requests、python-dotenv（可选 langchain-*）
```

---

## 3) 关键代码详解（为什么这么写）

### 3.1 环境变量与接口拼接
```python
from dotenv import load_dotenv
import os
load_dotenv()

API_KEY  = (os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
API_BASE = (os.getenv("DEEPSEEK_API_BASE") or os.getenv("OPENAI_API_BASE") or "https://api.deepseek.com/v1").strip()
API_ENDPOINT = API_BASE.rstrip("/") + "/chat/completions"
```
**要点**：  
- `load_dotenv()` 读取 `.env`，避免把密钥硬编码进代码库。  
- 兼容两套变量名（防止我在不同教程间拷贝时名对不上）。  
- `rstrip("/")` + `"/chat/completions"`：避免 `.../v1//chat...` 这种双斜杠或漏路径导致 401/404。

### 3.2 DeepSeek 封装：`ask_deepseek`
```python
def ask_deepseek(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个理性温柔的出行助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    resp = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 400:
        print("❌ DeepSeek 返回：", resp.status_code, resp.text[:400])  # 便于定位 401/429/4xx 问题
        resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
```
**为什么不写死回答？**  
- 我只提供“角色 + 事实”，让 **LLM 自己组织语言**，这样输出不再是硬编码模板。  
- 失败时把服务端原文打印出来，排错更高效（比如 key 无效、接口路径错、限流等）。

### 3.3 天气工具：`get_weather`
```python
def get_weather(city="杭州"):
    url = f"https://wttr.in/{city}?format=j1"
    data = requests.get(url, timeout=8).json()
    current = data["current_condition"][0]
    desc = current["weatherDesc"][0]["value"]
    temp = int(float(current["temp_C"]))
    humidity = int(current["humidity"])
    return {"desc": desc, "temp": temp, "humidity": humidity}
```
**为什么选 wttr.in？**  
- 免费、无需注册、返回结构化 JSON，适合原型期。  
**为什么做 `int(float(...))`？**  
- 有些接口给的温度是字符串或带小数，显式转型更稳。

### 3.4 Agent 主流程：`travel_agent`
```python
def travel_agent(user_input: str, city="杭州") -> str:
    # 现在还是“规则触发”
    intent_words = ["出门", "外出", "天气", "下雨", "带伞", "热不热", "冷不冷", "去哪", "玩"]
    if not any(w in user_input for w in intent_words):
        return ask_deepseek(user_input)  # 普通对话

    w = get_weather(city)
    if not w:
        return "我现在查不到天气，先看看窗外/本地天气 App 吧～"

    prompt = (
        f"现在在{city}的天气：{w['desc']}，温度{w['temp']}℃，湿度{w['humidity']}%。\n"
        "请你自主判断：\n"
        "1) 今天是否适合外出；\n"
        "2) 如有降雨风险提醒带伞；\n"
        "3) 温度过高/过低是否不宜外出；\n"
        "4) 最后用自然一句话总结。"
    )
    return ask_deepseek(prompt)
```
**与 Day 2 的本质差异**：  
- Day 2：通常是“命中意图 → 我写死模板/拼接字符串返回”。  
- Day 3：拿到**真实世界数据**（天气），由 **LLM 决策表达**，输出不再是模板。  
**还欠缺**： 是否调用工具仍是 if/else；这会在 Day 4 改成 **Planner → Executor → Finalizer**。

---

## 4) 运行 & 示例

### 运行
```bash
python app.py
```
看到：  
```
🤖 DeepSeek 智能出行 Agent 已启动！
```
即可交流。

### 示例
**输入**：我今天想出门，要不要带伞？  
**（内部）拿到天气**：多云 26℃ 湿度 70%  
**输出**：（由 LLM 生成）  
> 今天以多云为主，温度适中、湿度偏高，外出总体可行。建议备一把折叠伞以防阵雨，出门记得补水。

---

## 5) 常见错误与排查清单
- **401 Unauthorized**：十有八九是 key/endpoint 问题  
  - `.env` 里不要有空格/引号；  
  - `API_ENDPOINT` 必须是 `.../v1/chat/completions`；  
  - `Bearer {sk-xxx}`；  
  - 用 `curl` 最小请求自测是否通。  
- **超时**：网络问题/接口慢 → 提高 `timeout` 或重试策略。  
- **JSON 结构变动**：访问其他天气源时，注意字段名不同。

---

## 6) 我今天的收获
- 让 **LLM + 真实世界数据** 一起工作，输出更可信、更“像人”。  
- 把“密钥/接口/错误”处理好，Agent 的**可靠性**才起来。  
- 明白“规则触发 ≠ Agent”，Agent 需要**让模型做计划**。

---

## 7) Day 4 预告（要做但不一次性塞太多）
- **Planner（模型产出 JSON 计划）**：是否用工具、用哪个、参数是什么；
- **Executor（我执行工具）**：把 observation 回给模型；
- **Finalizer（模型总结）**：基于事实给最终建议。  
这会把“是否调用工具”的控制权完全交给模型，实现一个轻量的 ReAct 闭环。



— 完 —
