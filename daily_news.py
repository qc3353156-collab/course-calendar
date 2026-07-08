"""Daily News Digest — 金融硕士备考视角"""

import urllib.request, json, sys, ssl
import feedparser
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
now = datetime.now(CST)

# ── 已验证可用的 RSS 源 ───────────────────────────────────
# 每个源独立抓取，某个挂了不影响其他
FEEDS = [
    # (类别标签, 源名称, RSS/URL)
    ("宏观政策 · 金融财经", "FT中文网", "https://www.ftchinese.com/rss/news"),
    ("产业经济 · 科技前沿", "36氪", "https://36kr.com/feed"),
    ("全球市场 · 要闻", "Google News 财经", "https://news.google.com/rss/search?q=global+finance+markets&hl=en-US&gl=US&ceid=US:en"),
    ("国际局势 · 地缘", "BBC News", "http://feeds.bbci.co.uk/news/world/rss.xml"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

MAX_PER_SOURCE = 4  # 每个源取几条


def fetch_feed(name, url):
    """抓取单个 RSS，返回条目列表"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as resp:
            data = resp.read()
        feed = feedparser.parse(data)
        items = []
        for entry in feed.entries[:MAX_PER_SOURCE]:
            title = entry.get("title", "").strip()
            items.append(title)
        return items
    except Exception as e:
        print(f"  [{name}] 暂时不可用 ({type(e).__name__})", file=sys.stderr)
        return []


def collect_all():
    """抓取所有源，返回 {类别: [标题列表]}"""
    result = {}
    for category, name, url in FEEDS:
        print(f"  正在获取 {name}...", file=sys.stderr)
        titles = fetch_feed(name, url)
        if titles:
            # 去重 & 截断
            clean = []
            seen = set()
            for t in titles:
                key = t[:40]
                if key not in seen:
                    seen.add(key)
                    if len(t) > 80:
                        t = t[:77] + "..."
                    clean.append(t)
            result[category] = clean[:MAX_PER_SOURCE]
        else:
            result[category] = []
    return result


def format_digest(news):
    """排版为群消息"""
    today_str = now.strftime("%Y年%m月%d日")
    weekday = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
    exam_date = datetime(2026, 12, 26, tzinfo=CST)
    days_left = (exam_date.date() - now.date()).days

    lines = [
        f"【每日资讯摘要】{today_str} 周{weekday}",
        f"考研初试倒计时 {days_left} 天",
        "─" * 30,
    ]

    total = 0
    for category, titles in news.items():
        lines.append(f"\n▎{category}")
        if not titles:
            lines.append("  （暂无更新）")
        else:
            for i, t in enumerate(titles, 1):
                lines.append(f"  {i}. {t}")
                total += 1

    lines.append(f"\n{'─' * 30}")
    lines.append(f"共 {total} 条 | {now.strftime('%H:%M')} 生成")
    lines.append("FT中文 · 36氪 · Google News · BBC")

    return "\n".join(lines)


if __name__ == "__main__":
    print("获取新闻资讯中...", file=sys.stderr)
    news = collect_all()
    msg = format_digest(news)
    print(msg)

    # 推送到企业微信群机器人
    webhook = sys.argv[1] if len(sys.argv) > 1 else ""
    if webhook:
        payload = json.dumps({"msgtype": "text", "text": {"content": msg}}).encode()
        req = urllib.request.Request(
            webhook, data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
            result = resp.read().decode()
            print(f"推送结果: {result}", file=sys.stderr)
    else:
        print("(未提供 webhook URL，仅预览)", file=sys.stderr)
