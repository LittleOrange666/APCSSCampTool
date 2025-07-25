import threading
from datetime import datetime, timedelta

from .qindaou import QingdaoUOJ

oj = QingdaoUOJ()

cur_data = {}


def update_data():
    problems_data = oj.get_contest_problems("29")
    ranking = oj.get_ranking("29")
    problems = {}
    tot = 0
    for o in problems_data:
        problems[str(o["id"])] = o["_id"]
        tot += o["total_score"]
    for dat in ranking:
        handle = dat["user"]["username"]
        score_1 = 0
        score_2 = 0
        for k, v in dat["submission_info"].items():
            if k not in problems:
                continue
            pid = problems[k]
            easy = pid[0] in "ABCDEGHL" or pid in ("Z01", "Z02")
            hard = pid[0] in "FGIJKLMN" or pid in ("Z03", "Z04")
            if easy:
                score_1 += v
            if hard:
                score_2 += v
        cur_data[handle] = [score_1, score_2]


last_update_time = datetime.min
lock = threading.Lock()


def query_handle(handle):
    global last_update_time
    with lock:
        now = datetime.now()
        if now - last_update_time > timedelta(minutes=10):
            update_data()
            last_update_time = now
        if handle not in cur_data:
            return None
        return {
            "data": cur_data[handle],
            "last_update": last_update_time.isoformat()
        }
