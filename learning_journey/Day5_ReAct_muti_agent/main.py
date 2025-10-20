from agents import news_agent, writer_agent, editor_agent

def manager_agent(task="写一篇AI圈最新新闻报道"):
    print(f"\n🧭 客户任务：{task}")

    # 1️⃣ 抓取新闻
    print("\n[News Agent] 正在抓取AI新闻...")
    news_result = news_agent.run("请帮我获取AI领域最新新闻。")
    print(f"\n📰 抓取结果:\n{news_result}")

    # 2️⃣ 生成新闻稿
    print("\n[Writer Agent] 正在撰写新闻初稿...")
    draft_result = writer_agent.run(f"请根据以下新闻内容写一篇中文新闻报道：{news_result}")
    print(f"\n✍️ 新闻初稿:\n{draft_result}")

    # 3️⃣ 润色优化
    print("\n[Editor Agent] 正在润色新闻稿...")
    final_article = editor_agent.run(f"请润色以下报道：{draft_result}")
    print(f"\n🎨 最终报道:\n{final_article}")

    with open("final_ai_news.txt", "w", encoding="utf-8") as f:
        f.write(final_article)

    print("\n✅ 已生成文件：final_ai_news.txt")

if __name__ == "__main__":
    manager_agent()
