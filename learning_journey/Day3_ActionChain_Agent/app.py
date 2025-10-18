import os
import requests
from dotenv import load_dotenv

# 读取 .env
load_dotenv()

# 兼容两种写法：DEEPSEEK_* 或 OPENAI_*
API_KEY = (
    os.getenv("DEEPSEEK_API_KEY")
    or os.getenv("OPENAI_API_KEY")
)
API_BASE = (
    os.getenv("DEEPSEEK_API_BASE")
    or os.getenv("OPENAI_API_BASE")
    or "https://api.deepseek.com/v1"
)

# 正确的聊天补全 endpoint（base 后必须拼上 /chat/completions）
API_ENDPOINT = API_BASE.rstrip("/") + "/chat/completions"

# 启动自检
def _startup_check():
    print(f"🔧 API_BASE     : {API_BASE}")
    print(f"🔧 API_ENDPOINT : {API_ENDPOINT}")
    if not API_KEY or not API_KEY.startswith("sk-"):
        raise RuntimeError("❌ 没有读取到有效的 API Key。请在 .env 写入 DEEPSEEK_API_KEY= 或 OPENAI_API_KEY=")

_startup_check()

# ====== 工具1：天气查询 ======
def get_weather(city="杭州"):
    try:
        url = f"https://wttr.in/{city}?format=j1"
        res = requests.get(url, timeout=8)
        res.raise_for_status()
        data = res.json()
        current = data["current_condition"][0]
        desc = current["weatherDesc"][0]["value"]
        temp = int(float(current["temp_C"]))
        humidity = int(current["humidity"])
        return {"desc": desc, "temp": temp, "humidity": humidity}
    except Exception as e:
        print("⚠️ 天气获取失败：", e)
        return None

# ====== 工具2：调用 DeepSeek ======
def ask_deepseek(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个理性温柔的出行助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    resp = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=30)
    # 便于排错：401/4xx 时把服务端返回打印出来
    if resp.status_code >= 400:
        try:
            print("❌ DeepSeek 返回：", resp.status_code, resp.text[:400])
        except Exception:
            pass
        resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

# ====== Agent 主逻辑 ======
def travel_agent(user_input: str, city="杭州") -> str:
    # 粗粒度意图判断（你也可以改成 LLM 规划）
    intent_words = ["出门", "外出", "天气", "下雨", "带伞", "热不热", "冷不冷", "去哪", "玩"]
    if not any(w in user_input for w in intent_words):
        return ask_deepseek(user_input)

    weather = get_weather(city)
    if not weather:
        return "我现在查不到天气，先看看窗外/本地天气 App 吧～"

    desc, temp, humidity = weather["desc"], weather["temp"], weather["humidity"]
    prompt = (
        f"现在在{city}的天气：{desc}，温度{temp}℃，湿度{humidity}%。\n"
        "请你自主判断：\n"
        "1) 今天是否适合外出；\n"
        "2) 如果有降雨风险请提醒带伞；\n"
        "3) 如果温度过高/过低请给出是否不宜外出的建议；\n"
        "4) 最后用自然温暖的一句话总结建议。"
    )
    return ask_deepseek(prompt)

# ====== 启动入口 ======
if __name__ == "__main__":
    print("🤖 DeepSeek 智能出行 Agent 已启动！")
    print("输入 exit 退出\n")
    while True:
        q = input("你：").strip()
        if q.lower() in {"exit", "quit", "q"}:
            print("👋 再见！")
            break
        try:
            ans = travel_agent(q)
            print("💬 Agent：", ans, "\n")
        except requests.HTTPError as e:
            print("❌ HTTP 错误：", e)
        except Exception as e:
            print("❌ 运行错误：", e)
