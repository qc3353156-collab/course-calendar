"""Check today's courses - GitHub Actions daily reminder"""

from datetime import datetime, timezone, timedelta
from urllib.request import urlopen
from icalendar import Calendar
import random
import sys

CST = timezone(timedelta(hours=8))
EXAM_DATE = datetime(2026, 12, 26, tzinfo=CST)

ICS_URLS = [
    "https://raw.githubusercontent.com/qc3353156-collab/course-calendar/main/396%E5%85%A8%E9%83%A8%E8%AF%BE%E7%A8%8B.ics",
    "https://raw.githubusercontent.com/qc3353156-collab/course-calendar/main/431%E5%85%A8%E9%83%A8%E8%AF%BE%E7%A8%8B.ics",
]

QUOTES = [
    "你今天受的苦，都会变成考场上你手里的分。",
    "别人在刷短视频，你在刷题。这就是差距。",
    "考研不是看到了希望才坚持，而是坚持了才看到希望。",
    "每一个早起都是你对未来的投票。",
    "你觉得累，是因为你在走上坡路。",
    "今天不学习，明天变垃圾。话糙理不糙。",
    "你想要的录取通知书，正在一页一页被你写出来。",
    "图书馆里坐得住，考场上才能写得顺。",
    "别等了，就现在，去图书馆。",
    "比你优秀的人，比你还努力。你有什么资格偷懒？",
    "努力不一定成功，但不努力一定很舒服——然后后悔一辈子。",
    "今天多学一小时，考场上就多一分底气。",
    "你不是在应付考试，你是在给自己挣一个更好的未来。",
    "累了就歇一下，但别停下来。",
]

def get_today_events():
    today = datetime.now(CST).date()
    all_events = []
    for url in ICS_URLS:
        try:
            res = urlopen(url)
            cal = Calendar.from_ical(res.read())
            for component in cal.walk():
                if component.name != "VEVENT":
                    continue
                dt = component.get("dtstart").dt
                if isinstance(dt, datetime):
                    event_date = dt.astimezone(CST).date()
                    start = dt.astimezone(CST).strftime("%H:%M")
                else:
                    event_date = dt
                    start = "All day"
                if event_date == today:
                    summary = str(component.get("summary", ""))
                    all_events.append((start, summary))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
    all_events.sort(key=lambda x: x[0] if x[0] != "All day" else "99:99")
    return today, all_events

def format_message(today, events):
    wd = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][today.weekday()]
    days_left = (EXAM_DATE.date() - today).days
    quote = random.choice(QUOTES)

    header = f"{chr(0x1F4C5)} {today.strftime('%m/%d')} {wd}  |  考研倒计时 {days_left} 天"
    sep = f"{chr(0x2500) * 28}"

    if not events:
        body = f"{chr(0x1F4DA)} 今天没有课，自己去图书馆刷题！"
    else:
        lines = []
        for start, summary in events:
            tag = chr(0x1F539) if "396" in summary else chr(0x1F538)
            lines.append(f"  {tag} {start}  {summary}")
        body = f"{chr(0x1F3AB)} 今日课程 ({len(events)} 节):\n" + "\n".join(lines)
        body += f"\n\n{chr(0x1F4D6)} 上课结束后记得去图书馆巩固！"

    msg = f"{header}\n{sep}\n{body}\n{sep}\n{chr(0x1F4AC)} {quote}"

    return msg

if __name__ == "__main__":
    today, events = get_today_events()
    print(format_message(today, events))
