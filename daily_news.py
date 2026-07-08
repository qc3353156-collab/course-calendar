"""Daily News Digest — 金融硕士备考视角"""

import urllib.request, json, sys, ssl, re, html as html_mod
import feedparser
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))
now = datetime.now(CST)

FEEDS = [
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

MAX_PER_SOURCE = 3  # 减少条数，给摘要留空间

# ── 翻译器 ──
_translator = None

def get_translator():
    global _translator
    if _translator is None:
        try:
            from deep_translator import GoogleTranslator
            _translator = GoogleTranslator(source="auto", target="zh-CN")
            _translator.translate("test")
        except Exception:
            _translator = False
    return _translator if _translator else None


def translate_to_cn(text):
    t = get_translator()
    if t is None: return text
    try:
        result = t.translate(text)
        return result if result else text
    except Exception:
        return text


def needs_translation(text):
    chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
    return chinese_chars < len(text) * 0.3


def clean_html(raw):
    """去除 HTML 标签，提取纯文本"""
    if not raw: return ""
    text = re.sub(r'<[^>]+>', '', raw)
    text = html_mod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def truncate(text, max_len):
    if len(text) <= max_len: return text
    return text[:max_len-1] + "…"


def fetch_feed(name, url):
    """返回 [{title, summary, link}, ...]"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as resp:
            data = resp.read()
        feed = feedparser.parse(data)
        items = []
        for entry in feed.entries[:MAX_PER_SOURCE]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            # 摘要：优先用 summary，其次 description，再次 content
            raw_summary = (
                entry.get("summary", "") or
                entry.get("description", "") or
                ""
            )
            summary = clean_html(raw_summary)
            items.append({"title": title, "summary": summary, "link": link})
        return items
    except Exception as e:
        print(f"  [{name}] 暂时不可用 ({type(e).__name__})", file=sys.stderr)
        return []


def collect_all():
    result = {}
    for category, name, url in FEEDS:
        print(f"  正在获取 {name}...", file=sys.stderr)
        entries = fetch_feed(name, url)
        if entries:
            clean = []
            seen = set()
            for e in entries:
                key = e["title"][:40]
                if key not in seen:
                    seen.add(key)
                    clean.append(e)
            result[category] = clean[:MAX_PER_SOURCE]
        else:
            result[category] = []
    return result


def format_digest(news):
    today_str = now.strftime("%Y年%m月%d日")
    weekday = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
    exam_date = datetime(2026, 12, 19, tzinfo=CST)
    days_left = (exam_date.date() - now.date()).days

    lines = [
        f"【每日资讯摘要】{today_str} 周{weekday}",
        f"距考研初试 {days_left} 天 · 今日要闻",
        "─" * 28,
    ]

    total = 0
    for category, items in news.items():
        lines.append(f"\n▎{category}")
        if not items:
            lines.append("  （暂无更新）")
        else:
            for i, e in enumerate(items, 1):
                title = e["title"]
                summary = e["summary"]
                link = e["link"]

                # 翻译英文标题
                if needs_translation(title):
                    display = translate_to_cn(title)
                    if not display or display == title:
                        display = title
                else:
                    display = title

                display = truncate(display, 80)
                lines.append(f"  {i}. {display}")

                # 摘要（限长80字）
                if summary:
                    # 如果是英文摘要，翻译
                    if needs_translation(summary):
                        cn_summary = translate_to_cn(summary)
                        if cn_summary and cn_summary != summary:
                            summary = cn_summary
                    summary = truncate(summary, 100)
                    lines.append(f"     {summary}")

                # 链接
                if link:
                    # 企业微信支持超链接格式
                    lines.append(f"     🔗 {link}")

                total += 1

    lines.append(f"\n{'─' * 28}")
    lines.append(f"共 {total} 条 | {now.strftime('%H:%M')} 生成")

    return "\n".join(lines)


if __name__ == "__main__":
    print("获取新闻资讯中...", file=sys.stderr)
    news = collect_all()
    msg = format_digest(news)
    print(msg)

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
