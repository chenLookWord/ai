# .github/scripts/fetch_tech_news.py
import feedparser
import time
from datetime import datetime, timedelta, timezone
import requests
import os

# 配置
FEED_URLS = [
    "https://www.infoq.cn/aibriefs"
]

SERVERCHAN_SENDKEY = os.getenv("SERVERCHAN_SENDKEY")
if not SERVERCHAN_SENDKEY:
    raise EnvironmentError("SERVERCHAN_SENDKEY environment variable is not set.")

# 计算 24 小时前的时间（UTC）
now = datetime.now(timezone.utc)
one_day_ago = now - timedelta(hours=24)

def is_recent(entry):
    """判断文章是否在过去24小时内发布"""
    pub_time = None
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        pub_time = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return pub_time and pub_time >= one_day_ago

def fetch_news():
    articles = []
    for url in FEED_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if is_recent(entry):
                    title = entry.get('title', 'No Title')
                    link = entry.get('link', '#')
                    articles.append(f"<a href='{link}'>{title}</a>")
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
    return articles

def fetch_latest_articles():
    url = "https://www.infoq.cn/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        articles = []
        # 根据当前网页结构，提取文章链接和标题（需定期维护选择器）
        for item in soup.select('a[href^="/article/"], a[href^="/news/"]'):
            title_elem = item.find(['h2', 'h3', 'div'], class_=lambda x: x and 'title' in x.lower())
            desc_elem = item.find(['p', 'div'], class_=lambda x: x and ('desc' in x or 'summary' in x))
            
            title = title_elem.get_text(strip=True) if title_elem else item.get_text(strip=True)
            desc = desc_elem.get_text(strip=True) if desc_elem else ''
            link = "https://www.infoq.cn" + item['href'] if item['href'].startswith('/') else item['href']

            if title and link not in [a['link'] for a in articles]:
                articles.append({
                    "title": title,
                    "description": desc,
                    "link": link,
                    "time_fetched": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                if len(articles) >= 10:  # 只取前10篇
                    break

        return articles
    except Exception as e:
        print(f"[Error] {e}")
        return []

def send_to_serverchan(title, content):
    url = f"https://sctapi.ftqq.com/{SERVERCHAN_SENDKEY}.send"
    data = {
        "title": title,
        "desp": content,
        "channel": "9"  # 默认推送至企业微信（兼容性最好）
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("✅ 消息推送成功！")
    else:
        print(f"❌ 推送失败: {response.text}")

if __name__ == "__main__":
    print("🔍 正在抓取过去24小时的科技新闻...")
    news = fetch_latest_articles()

    if not news:
        print("📭 未找到过去24小时内的新科技新闻。")
        send_to_serverchan("科技日报", "📭 今日暂无新科技新闻。")
    else:
        content = "<br>".join(news[:20])  # 最多推送20条
        send_to_serverchan("📰 过去24小时科技要闻", content)
