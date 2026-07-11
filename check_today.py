"""Check today's courses - GitHub Actions daily reminder"""

from datetime import datetime, timezone, timedelta
from urllib.request import urlopen
from icalendar import Calendar
import random
import sys

CST = timezone(timedelta(hours=8))
EXAM_DATE = datetime(2026, 12, 19, tzinfo=CST)

ICS_URLS = [
    "https://raw.githubusercontent.com/qc3353156-collab/course-calendar/main/396全部课程.ics",
    "https://raw.githubusercontent.com/qc3353156-collab/course-calendar/main/431全部课程.ics",
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
                    start = "全天"
                if event_date == today:
                    summary = str(component.get("summary", ""))
                    all_events.append((start, summary))
        except Exception as e:
            print(f"ICS Error: {e}", file=sys.stderr)
    all_events.sort(key=lambda x: x[0] if x[0] != "全天" else "99:99")
    return today, all_events

def format_message(today, events):
    wd = ["一","二","三","四","五","六","日"][today.weekday()]
    days_left = (EXAM_DATE.date() - today).days
    quote = random.choice(QUOTES)
    header = "U0001F4C5 " + today.strftime("%m月%d日") + " 周" + wd + "  |  考研倒计时 " + str(days_left) + " 天"
    sep = "─" * 28
    if not events:
        body = "U0001F4DA 今天没有课，但图书馆永远有空座位，去刷题吧！"
    else:
        lines = []
        for start, summary in events:
            tag = "U0001F539" if "396" in summary else "U0001F538"
            lines.append("  " + tag + " " + start + "  " + summary)
        body = "U0001F3AB 今日课程 (" + str(len(events)) + " 节):
" + "
".join(lines)
        body += "

U0001F4D6 课后记得去图书馆巩固！"
    msg = header + "
" + sep + "
" + body + "
" + sep + "
U0001F4AC " + quote
    return msg

if __name__ == "__main__":
    today, events = get_today_events()
    msg = format_message(today, events)
    print(msg)
