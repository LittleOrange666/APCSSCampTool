import threading
from datetime import datetime, timedelta

from .qindaou import QingdaoUOJ

oj = QingdaoUOJ()

type_table = {'A': '變數/輸入輸出', 'B': '條件判斷/迴圈', 'C': '陣列/字串', 'D': '函式/遞迴', 'E': '結構',
              'G': '資料結構', 'L': '實作與除錯技巧', 'H': '考古題解析 (p1,p2)', 'F': '時間複雜度', 'I': '枚舉/二分搜',
              'J': '貪心', 'K': '圖論', 'M': '動態規劃', 'N': '考古題解析 (p3, p4)', 'Z': '模擬測驗 (p1, p2, p3, p4)'}

cur_data = {}
detail_data = {}
detail_max = {k: 0 for k in type_table.keys()}


def update_data():
    problems_data = oj.get_contest_problems("29")
    ranking = oj.get_ranking("29")
    problems = {}
    for k in detail_max:
        detail_max[k] = 0
    for o in problems_data:
        pid = o["_id"]
        problems[str(o["id"])] = pid
        if pid[0].isupper():
            detail_max[pid[0]] += o["total_score"]

    for dat in ranking:
        handle = dat["user"]["username"]
        score_1 = 0
        score_2 = 0
        detail = {k: [0, detail_max[k]] for k in type_table.keys()}
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
            if pid[0].isupper():
                detail[pid[0]][0] += v
        cur_data[handle] = [score_1, score_2]
        detail_data[handle] = detail


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
            "last_update": last_update_time.isoformat(),
            "detail": detail_data[handle]
        }
