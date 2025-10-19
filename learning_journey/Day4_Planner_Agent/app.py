# Day4: Planner(LLM JSON) -> Executor(调用工具) -> Finalizer(LLM总结)
import os, json, re, requests
from typing import Optional, Literal
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

# ============ 配置 ============
load_dotenv()
API_KEY  = (os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
API_BASE = (os.getenv("DEEPSEEK_API_BASE") or os.getenv("OPENAI_API_BASE") or "https://api.deepseek.com/v1").strip()
API_ENDPOINT = API_BASE.rstrip("/") + "/chat/completions"

def assert_ready():
    if not API_KEY:
        raise RuntimeError("找不到 API Key，请在 .env 里配置 DEEPSEEK_API_KEY")
    if not API_ENDPOINT.endswith("/chat/completions"):
        raise RuntimeError(f"API_ENDPOINT 不正确：{API_ENDPOINT}")

# ============ LLM 封装 ============
def ask_deepseek(messages: list, temperature: float = 0.7) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": temperature
    }
    resp = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)
    if resp.status_code >= 400:
        # 打印服务端信息，便于排错（401/429/4xx）
        print("❌ DeepSeek 返回：", resp.status_code, resp.text[:400])
        resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

def ask_chat(prompt: str, system: str = "你是理性温柔的出行助手。") -> str:
    return ask_deepseek([
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ])

# ============ 天气工具 ============
def get_weather(city: str = "杭州"):
    """使用 wttr.in 免费接口，不需注册"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        data = requests.get(url, timeout=8).json()
        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        temp = int(float(current["temp_C"]))
        humidity = int(current["humidity"])
        return {"city": city, "desc": desc, "temp": temp, "humidity": humidity}
    except Exception as e:
        print("⚠️ 天气获取失败：", e)
        return {"error": "weather_api_failed", "city": city}

# ============ 计划 Schema ============
class ToolArgs(BaseModel):
    city: Optional[str] = Field(default=None, description="城市名")

class Plan(BaseModel):
    intent: str
    use_tool: bool
    tool_name: Optional[Literal["get_weather"]] = None
    tool_args: Optional[ToolArgs] = None
    reason: str

def extract_json_block(s: str) -> str:
    """尽量从模型输出中提取 JSON 体（防止有```json 包裹或多余说明）"""
    s = s.strip()
    s = re.sub(r"^```json|```$", "", s, flags=re.IGNORECASE | re.MULTILINE).strip()
    # 如果依然含有非 JSON 文本，尝试截取第一个 {...} 块
    m = re.search(r"\{[\s\S]*\}$", s)
    return m.group(0) if m else s

# ============ Planner：模型产出 JSON 计划 ============
def plan_with_llm(user_input: str, default_city: str = "杭州") -> Plan:
    prompt = f"""
你是出行助手。用户说：{user_input}
你可以使用的工具：
- get_weather(city): 查询某城市实时天气（必须提供 city）

请只输出一个 JSON，字段如下：
{{
  "intent": "用户真实意图（简短一句）",
  "use_tool": true/false,
  "tool_name": "get_weather" 或 null,
  "tool_args": {{"city": "城市名"}} 或 null,
  "reason": "为什么这样计划"
}}

要求：
- 如果用户没说城市，就给出最合理的城市，比如默认 {default_city}，或根据语境推断。
- 只输出 JSON，不要任何解释。
"""
    raw = ask_chat(prompt, system="你是精确的计划生成器，只输出严格 JSON。")
    cleaned = extract_json_block(raw)
    try:
        plan = Plan.model_validate_json(cleaned)
    except ValidationError:
        # 兜底方案：不使用工具，转成普通聊天
        plan = Plan(intent="闲聊", use_tool=False, tool_name=None, tool_args=None, reason="解析失败，回退")
    # 参数补全
    if plan.use_tool and plan.tool_name == "get_weather":
        if not plan.tool_args:
            plan.tool_args = ToolArgs(city=default_city)
        if not plan.tool_args.city:
            plan.tool_args.city = default_city
    return plan

# ============ Executor：按计划调用工具 ============
def execute_plan(plan: Plan):
    if plan.use_tool and plan.tool_name == "get_weather":
        return {"observation": get_weather(plan.tool_args.city)}
    return {"observation": None}

# ============ Finalizer：基于计划+观察结果生成最终答复 ============
def finalize_answer(plan: Plan, observation) -> str:
    plan_json = plan.model_dump()
    prompt = f"""
这是你为用户生成的计划（JSON）：
{json.dumps(plan_json, ensure_ascii=False)}

这是你根据计划执行后的观察结果（JSON）：
{json.dumps(observation, ensure_ascii=False)}

请面向用户给出最终建议，要求：
- 如果 observation 里有天气事实：判断是否适合外出、是否需要带伞、温度是否不宜外出，并给出一句温暖总结；
- 如果 observation 里有 error：坦诚说明工具不可用，给出常识性建议；
- 只输出给用户看的内容，不要暴露 JSON 或内部术语。
"""
    return ask_chat(prompt)

# ============ Agent 对话循环 ============
def run_cli(default_city: str = "杭州"):
    assert_ready()
    print("🤖 DeepSeek Planner Agent 已启动！")
    print(f"🔗 API_BASE = {API_BASE}")
    print(f"🔗 ENDPOINT = {API_ENDPOINT}\n")
    print("输入 exit 退出\n")

    while True:
        user = input("你：").strip()
        if user.lower() in {"exit", "quit", "q"}:
            print("👋 再见！")
            break

        try:
            plan = plan_with_llm(user, default_city=default_city)
            print("🧠 PLAN:", json.dumps(plan.model_dump(), ensure_ascii=False))
            exec_result = execute_plan(plan)
            print("🔍 OBS :", json.dumps(exec_result, ensure_ascii=False))
            answer = finalize_answer(plan, exec_result)
            print("💬 ANSWER：", answer, "\n")
        except requests.HTTPError as e:
            print("❌ HTTP 错误：", e, "\n")
        except Exception as e:
            print("❌ 其他错误：", e, "\n")

if __name__ == "__main__":
    run_cli(default_city="杭州")
