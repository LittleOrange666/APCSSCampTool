import time
from zoneinfo import ZoneInfo

import json
import datetime


def main():
    from modules import tool
    print("Updating data...")
    tool.update_data()
    print("Caching data...")
    data = {
        "cur_data": tool.cur_data,
        "detail_data": tool.detail_data,
    }
    with open("cache.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("Caching completed.")


def cal():
    t = datetime.datetime(2026, 1, 1)
    print(t)
    print(t.timestamp())
    print(t.isoformat())
    print(datetime.datetime.fromisoformat(t.isoformat()).replace(tzinfo=ZoneInfo("Asia/Taipei")))
    while datetime.datetime.now() < t:
        print("now=",datetime.datetime.now())
        d = t - datetime.datetime.now()
        print("d=", d)
        x = d.seconds % 60 + d.microseconds / 1_000_000
        print("sleeping for", x if x else 60, "seconds")
        time.sleep(x if x else 60)
    main()


if __name__ == '__main__':
    cal()
