"""Check today's courses - GitHub Actions daily reminder"""

from datetime import datetime, timezone, timedelta
from urllib.request import urlopen
from icalendar import Calendar
import sys

CST = timezone(timedelta(hours=8))

ICS_URLS = [
    "https://raw.githubusercontent.com/qc3353156-collab/course-calendar/main/396%E5%85%A8%E9%83%A8%E8%AF%BE%E7%A8%8B.ics",
    "https://raw.githubusercontent.com/qc3353156-collab/course-calendar/main/431%E5%85%A8%E9%83%A8%E8%AF%BE%E7%A8%8B.ics",
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
    h = f"{today.strftime('%m/%d')} {wd}\n"
    if not events:
        return h + "No class today!"
    lines = [h]
    for start, summary in events:
        lines.append(f"  {start}  {summary}")
    lines.append(f"\n{len(events)} course(s) today")
    return "\n".join(lines)

if __name__ == "__main__":
    today, events = get_today_events()
    print(format_message(today, events))
