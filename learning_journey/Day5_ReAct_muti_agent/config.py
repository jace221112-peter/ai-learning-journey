import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")

def get_deepseek_llm(model="deepseek-chat", temperature=0.7):
    """
    返回一个 DeepSeek 模型实例（兼容OpenAI接口）
    """
    llm = ChatOpenAI(
        model=model,
        openai_api_key=DEEPSEEK_API_KEY,
        openai_api_base=DEEPSEEK_API_BASE,
        temperature=temperature,
    )
    return llm