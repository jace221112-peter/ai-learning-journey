import feedparser
import re
from datetime import date

def get_ai_news(input_text=None):
    """抓取Google News RSS的AI相关新闻"""
    feed_url = "https://news.google.com/rss/search?q=artificial+intelligence&hl=en&gl=US&ceid=US:en"
    feed = feedparser.parse(feed_url)
    today = date.today().strftime("%Y-%m-%d")

    if not feed.entries:
        return f"[{today}] 暂未获取到AI相关新闻，请稍后再试。"

    news_items = []
    for entry in feed.entries[:5]:
        title = entry.title.replace("\n", " ").strip()
        summary = re.sub(r"<.*?>", "", entry.get("summary", "")).strip()
        news_line = f"{title} - {summary[:100]}..."
        news_items.append(news_line)

    formatted_news = "\n".join([f"{i+1}. {n}" for i, n in enumerate(news_items)])
    return f"📅 {today} AI圈新闻精选：\n{formatted_news}"

def write_draft(news_text):
    """生成新闻报道初稿"""
    return f"请根据以下AI新闻生成一篇有逻辑的中文报道：\n{news_text}"

def polish_article(draft_text):
    """润色新闻报道"""
    return f"请将以下报道润色，使语言自然、逻辑通顺、符合新闻写作风格：\n{draft_text}"
