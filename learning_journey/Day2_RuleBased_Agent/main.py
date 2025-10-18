# -*- coding: utf-8 -*-
import re
from dotenv import load_dotenv

# 新版 LangChain 组件（替代 LLMChain）
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

load_dotenv()  # 读取 .env 里的 OPENAI_API_KEY 与 OPENAI_API_BASE（或 base_url）

# ============ 0) 初始化 DeepSeek（Chat 模型） ============
# 说明：ChatOpenAI 同时兼容 DeepSeek（OpenAI 协议）。可用环境变量或代码传 base_url。
llm = ChatOpenAI(
    model="deepseek-chat",
    temperature=0.7,
    # 如果你没在 .env 里配 OPENAI_API_BASE，可取消下一行注释手动指定：
    # base_url="https://api.deepseek.com/v1"
)

# 统一的通用回答链：prompt → llm → 纯文本
prompt = ChatPromptTemplate.from_template("请用简洁中文回答：{question}")
default_chain = prompt | llm | StrOutputParser()

# ============ 1) 意图识别（规则版 Planner 雏形） ============
def detect_intent(user_input: str) -> str:
    # 补充了“哪个好/对比/比较/哪个更…”等关键词
    if re.search(r"(好不好|优缺点|值得买吗|评价|哪个好|对比|比较|哪个更)", user_input):
        return "analysis"
    elif re.search(r"(是什么|定义|介绍|功能)", user_input):
        return "fact"
    else:
        return "default"

# ============ 2) 工具函数（模拟工具箱） ============
def search_knowledge(query: str):
    docs = {
        "百岁山": "百岁山是天然矿泉水品牌，强调“天然好水”的品牌理念。",
        "农夫山泉": "农夫山泉以“我们不生产水，我们只是大自然的搬运工”为核心口号。"
    }
    return docs.get(query, "未找到相关资料。")

def compare_products(p1, p2):
    return f"{p1}在品牌理念上更强调自然纯净，而{p2}注重市场传播与用户触达。"

# ============ 3) 主控制逻辑（Executor） ============
def agent_response(user_input: str):
    intent = detect_intent(user_input)
    print(f"✅ 识别意图：{intent}")

    if intent == "fact":
        # 取出关键词：把“是什么”去掉，得到查询词
        product = user_input.replace("是什么", "").strip()
        info = search_knowledge(product)
        return f"{product}的简介如下：{info}"

    elif intent == "analysis":
        # 提取出现的品牌名
        products = re.findall(r"(百岁山|农夫山泉|怡宝)", user_input)
        products = list(dict.fromkeys(products))  # 去重，防止重复匹配

        if len(products) >= 2:
            return compare_products(products[0], products[1])
        elif len(products) == 1:
            return f"关于{products[0]}的总体评价：口感纯净，定位较高端。"
        else:
            # 没抓到品牌名，就走默认链请 LLM 先给出分析思路
            return default_chain.invoke({"question": f"用户要对比评价这类饮用水品牌：{user_input}，请先提出评价维度。"})

    else:
        # 新写法：使用 Runnable 的 invoke，而不是 LLMChain.run
        return default_chain.invoke({"question": user_input})

# ============ 4) 本地交互测试 ============
if __name__ == "__main__":
    # 预置三条
    print(agent_response("百岁山是什么"))
    print(agent_response("百岁山和农夫山泉哪个好？"))
    print(agent_response("你喜欢什么水？"))

    # 可选：交互模式
    # while True:
    #     q = input("💬 请输入（exit退出）：")
    #     if q.lower() == "exit":
    #         break
    #     print(agent_response(q))
