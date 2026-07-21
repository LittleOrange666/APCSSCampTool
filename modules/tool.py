import os
import threading
from datetime import datetime, timedelta
from typing import TypedDict
from zoneinfo import ZoneInfo
import json

from .qindaou import QingdaoUOJ

oj = QingdaoUOJ()

type_table: dict[str, str] = {'A': '變數/輸入輸出', 'B': '條件判斷/迴圈', 'C': '陣列/字串', 'D': '函式/遞迴', 'E': '結構',
              'G': '資料結構', 'L': '實作與除錯技巧', 'H': '考古題解析 (基礎)', 'F': '時間複雜度', 'I': '枚舉/二分搜',
              'J': '貪心', 'K': '圖論', 'M': '動態規劃', 'N': '考古題解析 (進階)', 'Z': '模擬測驗'}

freeze_time = None
freeze = False
OJ_CONTEST_ID = os.getenv("OJ_CONTEST_ID", "29").strip()

if "OJ_FREEZE_TIME" in os.environ:
    freeze_time = datetime.fromisoformat(os.environ["OJ_FREEZE_TIME"].strip()).replace(tzinfo=ZoneInfo("Asia/Taipei"))
    freeze = True

cur_data: dict[str, tuple[int, int]] = {}
detail_data: dict[str, dict[str, tuple[int, int]]] = {}
detail_max = {k: 0 for k in type_table.keys()}
maxs: tuple[int, int] = (0, 0)
cur_time_zone = ZoneInfo("Asia/Taipei")
cache_file = "cache.json"
if "OJ_CACHE_FILE" in os.environ:
    cache_file = os.environ["OJ_CACHE_FILE"].strip()

name_table = {}
if os.path.exists("data/names.csv"):
    with open("data/names.csv", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            oj_handle, name = line.split(",", 1)
            name_table[oj_handle] = name


def is_easy(pid):
    return pid[0] in "ABCDEGHL" or pid in ("Z01", "Z02", "Z03")


def is_hard(pid):
    return pid[0] in "FIJKMN" or pid in ("Z04", "Z05", "Z06")


def update_data():
    global maxs
    if freeze:
        with open(cache_file, encoding="utf-8") as f:
            data = json.load(f)
            global cur_data, detail_data
            cur_data = data["cur_data"]
            detail_data = data["detail_data"]
        return
    problems_data = oj.get_contest_problems(OJ_CONTEST_ID)
    ranking = oj.get_ranking(OJ_CONTEST_ID)
    problems = {}
    for k in detail_max:
        detail_max[k] = 0
    easy_max = 0
    hard_max = 0
    for o in problems_data:
        pid = o["_id"]
        problems[str(o["id"])] = pid
        easy = is_easy(pid)
        hard = is_hard(pid)
        if pid[0].isupper():
            detail_max[pid[0]] += o["total_score"]
        if easy:
            easy_max += o["total_score"]
        if hard:
            hard_max += o["total_score"]
    maxs = (easy_max, hard_max)

    for dat in ranking:
        handle = dat["user"]["username"]
        score_1 = 0
        score_2 = 0
        detail = {k: 0 for k in type_table.keys()}
        for k, v in dat["submission_info"].items():
            if k not in problems:
                continue
            pid = problems[k]
            easy = is_easy(pid)
            hard = is_hard(pid)
            if easy:
                score_1 += v
            if hard:
                score_2 += v
            if pid[0].isupper():
                detail[pid[0]] += v
        cur_data[handle] = (score_1, score_2)
        detail_data[handle] = {k: (detail[k], detail_max[k]) for k in type_table.keys()}


last_update_time = datetime.now(cur_time_zone) - timedelta(days=1)
lock = threading.Lock()


def get_data():
    global last_update_time
    with lock:
        now = datetime.now(cur_time_zone)
        if now - last_update_time > timedelta(minutes=10):
            update_data()
            if freeze:
                last_update_time = freeze_time
            else:
                last_update_time = now
        return cur_data


class QueryRes(TypedDict):
    data: tuple[int, int]
    last_update: str
    detail: dict[str, tuple[int, int]]
    maxs: tuple[int, int]


def query_handle(handle) -> QueryRes | None:
    get_data()
    res: QueryRes | None = None
    if handle not in cur_data:
        if handle in name_table:
            res = {
                "data": (0, 0),
                "last_update": last_update_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "detail": {k: (0, detail_max[k]) for k in type_table.keys()},
                "maxs": maxs
            }
    else:
        res = {
            "data": cur_data[handle],
            "last_update": last_update_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "detail": detail_data[handle],
            "maxs": maxs
        }
    return res



def all_names() -> list[str]:
    return sorted(set(name_table.keys()) | set(cur_data.keys()))
