from langchain.agents import Tool, initialize_agent
from langchain.memory import ConversationBufferMemory
from tools import get_ai_news, write_draft, polish_article
from config import get_deepseek_llm

# === 使用 DeepSeek 模型 ===
llm = get_deepseek_llm(model="deepseek-chat", temperature=0.7)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# === 定义工具 ===
news_tool = Tool(name="NewsFetcher", func=get_ai_news, description="抓取AI领域最新新闻")
draft_tool = Tool(name="DraftWriter", func=write_draft, description="生成AI新闻初稿")
edit_tool = Tool(name="Editor", func=polish_article, description="润色和优化稿件")

# === 定义三个Agent ===
news_agent = initialize_agent([news_tool], llm, agent_type="zero-shot-react-description", verbose=True)
writer_agent = initialize_agent([draft_tool], llm, agent_type="zero-shot-react-description", verbose=True)
editor_agent = initialize_agent([edit_tool], llm, agent_type="zero-shot-react-description", verbose=True)
