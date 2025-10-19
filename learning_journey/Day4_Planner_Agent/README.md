# Day3 → Day4 升级记录（单文件版）

> 日期：2025-10-19
> 本文对应的代码：**单文件 `app.py`**（未拆分模块）。目标是让读者一眼看懂：我如何从 Day3 的“规则触发 + 模板化回答”，升级到 Day4 的 **Planner → Executor → Finalizer** 决策型 Agent。

---

## 0. TL;DR

- **Day3（Action Chain / 规则触发）**：关键词命中 → 调用固定工具 `get_weather` → 把事实丢给 LLM 生成自然语言建议。
- **Day4（Planner Agent / 决策驱动）**：
  - 由 **LLM 规划器（Planner）** 输出结构化 **Plan JSON**（`use_tool / tool_name / tool_args / reason`）；
  - **执行器（Executor）** 按计划调用工具并拿到 **observation**；
  - **总结器（Finalizer）** 基于“计划 + 观察结果”生成面向用户的最终答案（自然语言）。

---

## 1. 单文件结构（今天不拆模块）

代码在一个 `app.py` 中，包含：

- **配置与 LLM 封装**
  - `ask_deepseek(messages, temperature)`：统一 headers、payload、错误处理；
  - `ask_chat(prompt, system)`：便捷封装，组装成 `messages` 调用上面函数。
- **工具（Tools）**
  - `get_weather(city)`：调用 `wttr.in` 免费天气 API，返回统一结构；异常时返回 `{{"error": ...}}`。
- **Schema（计划结构）**
  - `Plan / ToolArgs`（Pydantic）：校验 LLM 产出的 JSON，保证字段/类型正确，并支持默认值补全。
- **Planner（计划器）**
  - `plan_with_llm(user_input, default_city)`：专用 prompt 让 LLM 只输出 **严格 JSON**；清洗、校验、参数补全。
- **Executor（执行器）**
  - `execute_plan(plan)`：根据 `plan.use_tool / tool_name / tool_args` 调用工具，返回 `{{"observation": ...}}`。
- **Finalizer（总结器）**
  - `finalize_answer(plan, observation)`：把“计划 + 观察结果”交给 LLM → 输出用户可读的建议。
- **CLI 外壳（可观察）**
  - `run_cli()`：打印 `PLAN / OBS / ANSWER` 三段日志，便于调试与演示。

---

## 2. Day3 vs Day4：一张表看懂升级点

| 维度 | Day3（规则触发） | Day4（Planner Agent） |
|---|---|---|
| 触发方式 | if/else 判断关键词 | LLM 产出 **Plan JSON** 决定是否用工具与参数 |
| 数据结构 | 自由文本 | **Pydantic Schema（Plan/ToolArgs）** 强约束 |
| 工具调用 | 代码里写死 `get_weather()` | **Executor** 按 **Planner** 的计划执行 |
| 提示词 | 一个通用 prompt | **分阶段 prompt**：Planner（只出 JSON）、Finalizer（只说人话） |
| 错误处理 | try/except + 文本提示 | LLM 封装统一 4xx/5xx 打印+抛错；工具统一返回 `observation` |
| 可扩展性 | 新功能=改 if/else | 新增工具=加工具函数+在 Planner 声明+Executor 调派 |
| 可观测性 | 无结构日志 | 终端打印 **PLAN / OBS / ANSWER** 三段日志 |

---

## 3. LLM 封装：为什么与怎么做

**为什么封装？** 统一处理 `headers/payload/timeout/错误`；换模型或 base 时只改一处；日志一致、排错快。

**核心代码**
```python
def ask_deepseek(messages: list, temperature: float = 0.7) -> str:
    headers = { "Authorization": f"Bearer {{API_KEY}}", "Content-Type": "application/json" }
    payload = { "model": "deepseek-chat", "messages": messages, "temperature": temperature }
    resp = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 400:
        print("❌ DeepSeek 返回：", resp.status_code, resp.text[:400])
        resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def ask_chat(prompt: str, system: str = "你是理性温柔的出行助手。") -> str:
    return ask_deepseek([
        { "role": "system", "content": system },
        { "role": "user", "content": prompt },
    ])
```

> `ask_chat()` 是常用场景的“简写”，把 `system + user` 组装成 `messages`。

---

## 4. 工具（Tools）：干净的数据、统一的返回

**为什么要工具层？** 把“外部世界（接口返回的脏 JSON）”变成“自己世界（干净、固定字段）”；异常要兜底，别把 Agent 弄崩。

**示例：天气**
```python
def get_weather(city: str = "杭州"):
    try:
        data = requests.get(f"https://wttr.in/{city}?format=j1", timeout=8).json()
        current = data["current_condition"][0]
        return {
            "city": city,
            "desc": current["weatherDesc"][0]["value"],
            "temp": int(float(current["temp_C"])),
            "humidity": int(current["humidity"]),
        }
    except Exception as e:
        return {"error": "weather_api_failed", "city": city}
```

---

## 5. Schema（Plan/ToolArgs）：让 LLM 的 JSON 可被**强校验**

**为什么要 Schema？** LLM 偶尔会少字段/类型错；Pydantic 能第一时间报错并回退，避免更深处崩溃；同时提供类型提示与默认值补全。

**核心结构**
```python
class ToolArgs(BaseModel):
    city: Optional[str] = Field(default=None, description="城市名")

class Plan(BaseModel):
    intent: str
    use_tool: bool
    tool_name: Optional[Literal["get_weather"]] = None
    tool_args: Optional[ToolArgs] = None
    reason: str
```

---

## 6. Planner：让模型只输出“计划 JSON”

**关键点**：专用 prompt（只出 JSON）、清洗代码块、Schema 校验、参数补全。

```python
def plan_with_llm(user_input: str, default_city: str = "杭州") -> Plan:
    prompt = f"""
你是出行助手。用户说：{user_input}
可用工具：
- get_weather(city): 查询实时天气（必须提供 city）

请只输出 JSON：
{
  "intent": "...",
  "use_tool": true/false,
  "tool_name": "get_weather" 或 null,
  "tool_args": {"city": "城市名"} 或 null,
  "reason": "..."
}
要求：若用户没说城市，推断或用默认 {default_city}；只输出 JSON。
"""
    raw = ask_chat(prompt, system="你是精确的计划生成器，只输出严格 JSON。")
    cleaned = extract_json_block(raw)
    try:
        plan = Plan.model_validate_json(cleaned)
    except ValidationError:
        plan = Plan(intent="闲聊", use_tool=False, tool_name=None, tool_args=None, reason="解析失败，回退")
    if plan.use_tool and plan.tool_name == "get_weather":
        if not plan.tool_args:
            plan.tool_args = ToolArgs(city=default_city)
        if not plan.tool_args.city:
            plan.tool_args.city = default_city
    return plan
```

> 这一步把“用不用工具/用哪个/参数是什么”交给 LLM 决策，正式摆脱 if/else 关键词判断。

---

## 7. Executor：执行器只负责“按计划调用工具”

```python
def execute_plan(plan: Plan):
    if plan.use_tool and plan.tool_name == "get_weather":
        return {"observation": get_weather(plan.tool_args.city)}
    return {"observation": None}
```

- 统一返回 `{"observation": ...}`，为 Finalizer 提供事实输入。
- 新增工具时，这里按计划分发即可。

---

## 8. Finalizer：把“计划 + 观察结果”变成用户能读懂的答案

**为什么要单独的 Finalizer？** Planner 关注结构化计划；Finalizer 关注“面向用户的表达”，并在工具失败时给出**诚实的替代建议**。

```python
def finalize_answer(plan: Plan, observation) -> str:
    plan_json = plan.model_dump()
    prompt = f"""
这是计划（JSON）：
{json.dumps(plan_json, ensure_ascii=False)}

这是观察结果（JSON）：
{json.dumps(observation, ensure_ascii=False)}

请面向用户给出最终建议：
- 若有天气事实：判断是否适合外出、是否带伞、冷热是否不宜外出，并简要解释；
- 若 observation 有 error：坦诚说明工具不可用，并给出常识性建议；
- 只输出给用户看的内容，不要暴露 JSON 或内部术语。
"""
    return ask_chat(prompt)
```

---

## 9. 可观察的 CLI：快速验证闭环

```python
def run_cli(default_city="杭州"):
    print("🤖 DeepSeek Planner Agent 已启动！")
    while True:
        user = input("你：").strip()
        if user.lower() in { "exit", "quit", "q" }:
            break
        plan = plan_with_llm(user, default_city)
        print("🧠 PLAN:", json.dumps(plan.model_dump(), ensure_ascii=False))
        obs  = execute_plan(plan)
        print("🔍 OBS :", json.dumps(obs, ensure_ascii=False))
        ans  = finalize_answer(plan, obs)
        print("💬 ANSWER：", ans, "\n")
```

- 明确看到三段：**PLAN / OBS / ANSWER**，学习与排错都很直观。

---

## 10. 如何自己照着复刻一个新场景（备忘）

1. **写工具函数**（比如 `search_products(query)`），保证：输入明确、返回统一、失败 `{"error": ...}`；  
2. **在 Planner 的 prompt** 中把新工具描述清楚（功能、参数、限制），并把 `tool_name` 的 `Literal` 加上；  
3. **在 Executor** 中根据 `plan.tool_name` 分发调用；  
4. **在 Finalizer** 里写清输出风格与异常降级提示；  
5. **调试**：用 CLI 观察 `PLAN / OBS / ANSWER`，直到计划稳定为止。

---

## 11. 运行与测试

```bash
python app.py
```

**建议测试输入**
- 我想去上海外滩，需要带伞吗？
- 杭州今天太热了吗？适合跑步吗？
- 我心情有点低落（应走闲聊，不用工具）
- 我在苏州，晚上适合出门吗？

---

## 12. 后续（Day5 预告）

- 把今天的单文件拆成模块（`llm.py / tools.py / schema.py / planner.py / executor.py / finalizer.py / app.py`）；
- 新增一个工具（如 AQI），练习 Planner 同时选择合适工具；
- 为 Planner 加 **校验失败自动重试**；
- 把 CLI 换成 Web API（FastAPI/Flask）。

---
