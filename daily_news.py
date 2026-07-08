"""Daily News Digest — 金融硕士备考视角"""

import urllib.request, json, sys, ssl
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

MAX_PER_SOURCE = 4

# ── 翻译器（惰性初始化）──
_translator = None

def get_translator():
    global _translator
    if _translator is None:
        try:
            from deep_translator import GoogleTranslator
            _translator = GoogleTranslator(source="auto", target="zh-CN")
            _translator.translate("test")
        except Exception:
            _translator = False  # 标记不可用
    return _translator if _translator else None


def translate_to_cn(text):
    """英→中翻译，失败则返回原文"""
    t = get_translator()
    if t is None:
        return text
    try:
        result = t.translate(text)
        return result if result else text
    except Exception:
        return text


def needs_translation(text):
    """判断是否包含非中文字符（需要翻译）"""
    chinese_chars = sum(1 for c in text if '一' <= c <= '鿿')
    return chinese_chars < len(text) * 0.3


def extract_summary(title, category):
    """从标题提取具体摘要标签"""
    t = title.lower()

    # 金融财经类
    if "金融" in category or "市场" in category:
        if any(w in t for w in ["央行", "利率", "通胀", "fed", "ecb", "cpi"]):
            return "→ 货币政策信号"
        if any(w in t for w in ["贸易", "关税", "tariff", "trade", "export"]):
            return "→ 国际贸易博弈"
        if any(w in t for w in ["油价", "能源", "oil", "energy", "gold", "黄金"]):
            return "→ 大宗商品动向"
        if any(w in t for w in ["股", "stock", "market", "指数", "ipo"]):
            return "→ 资本市场波动"
        if any(w in t for w in ["人民", "汇率", "yen", "dollar", "fx", "rmb"]):
            return "→ 汇率与资本流动"
        return "→ 宏观经济信号"

    # 产业科技类
    if "产业" in category or "科技" in category:
        if any(w in t for w in ["ai", "人工智能", "大模型", "gpt", "llm", "智能"]):
            return "→ AI 产业落地"
        if any(w in t for w in ["新能源", "电动", "ev", "光伏", "锂电", "储能"]):
            return "→ 新能源产业"
        if any(w in t for w in ["芯片", "半导体", "chip", "算力", "gpu"]):
            return "→ 半导体竞争"
        if any(w in t for w in ["电商", "跨境", "出海", "国际化"]):
            return "→ 中企全球化"
        return "→ 产业趋势观察"

    # 国际地缘类
    if "国际" in category or "地缘" in category:
        if any(w in t for w in ["iran", "伊朗", "israel", "以色列", "中东", "middle east"]):
            return "→ 中东局势"
        if any(w in t for w in ["ukraine", "乌克兰", "russia", "俄罗斯", "nato"]):
            return "→ 俄乌冲突"
        if any(w in t for w in ["china", "中国", "beijing", "xi", "taiwan", "台湾"]):
            return "→ 中美关系"
        if any(w in t for w in ["trump", "特朗普", "biden", "拜登", "election", "选举"]):
            return "→ 国际政治变局"
        if any(w in t for w in ["eu", "europe", "欧洲", "germany", "德国", "france", "法国"]):
            return "→ 欧洲政经"
        return "→ 地缘政治风险"

    return "→ 关注"


def fetch_feed(name, url):
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
    result = {}
    for category, name, url in FEEDS:
        print(f"  正在获取 {name}...", file=sys.stderr)
        titles = fetch_feed(name, url)
        if titles:
            clean = []
            seen = set()
            for t in titles:
                key = t[:40]
                if key not in seen:
                    seen.add(key)
                    clean.append(t)
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
        f"考研初试倒计时 {days_left} 天 · 今日关注要点如下",
        "─" * 30,
    ]

    total = 0
    for category, titles in news.items():
        lines.append(f"\n▎{category}")
        if not titles:
            lines.append("  （暂无更新）")
        else:
            for i, t in enumerate(titles, 1):
                # 翻译
                if needs_translation(t):
                    cn_title = translate_to_cn(t)
                    if cn_title and cn_title != t:
                        display = cn_title
                    else:
                        display = t
                else:
                    display = t

                # 截断
                if len(display) > 80:
                    display = display[:77] + "..."

                lines.append(f"  {i}. {display}")

                # 摘要
                summary = extract_summary(t, category)
                if summary:
                    lines.append(f"     {summary}")

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
