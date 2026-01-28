import json
import os.path
import random
import string

import requests
from tqdm import trange


class QingdaoUProblem:
    __slots__ = ("data",)

    def __init__(self, data: dict):
        self.data = data


submission_result_table = {0: "AC", 1: "TLE", 3: "MLE", 4: "RE", 8: "PA", -1: "WA", -2: "CE"}
info_file = "qindaou_info.json"


class QingdaoUOJ:

    def __init__(self):
        self.info = {}
        if os.path.exists(info_file):
            with open(info_file) as f:
                self.info = json.load(f)
        if "url" not in self.info:
            if "QingdaoUOJ_URL" in os.environ:
                self.info["url"] = os.environ["QingdaoUOJ_URL"].strip()
            else:
                self.info["url"] = input("Please input the url of OJ: ").strip()
        if "account" not in self.info:
            if "QingdaoUOJ_ACCOUNT" in os.environ:
                self.info["account"] = os.environ["QingdaoUOJ_ACCOUNT"].strip()
            else:
                self.info["account"] = input("Please input the account of OJ: ").strip()
        if "password" not in self.info:
            if "QingdaoUOJ_PASSWORD" in os.environ:
                self.info["password"] = os.environ["QingdaoUOJ_PASSWORD"].strip()
            else:
                self.info["password"] = input("Please input the password of OJ: ").strip()
        url = self.info["url"]
        if url.endswith("/"):
            url = url[:-1]
        if not url.startswith("http"):
            url = "https://" + url
        self.info["url"] = url
        self.url: str = url
        self.cookie: str | None = None
        if "cookie" in self.info:
            self.cookie = self.info["cookie"]
            if not self.check_login():
                self.login()
                self.info["cookie"] = self.cookie
        else:
            self.login()
            self.info["cookie"] = self.cookie
        with open(info_file, "w") as f:
            json.dump(self.info, f)

    def check_login(self):
        dat = self.get_data("api/profile")
        return dat is not None

    def login(self):
        account = self.info["account"]
        password = self.info["password"]
        login_url = self.url+"/api/login"
        session = requests.Session()
        csrf_token = "".join(random.choices(string.ascii_letters + string.digits, k=64))
        session.cookies.set("csrftoken", csrf_token)
        headers = {
            "Content-Type": "application/json",
            "Referer": self.url,
            "Origin": self.url,
            "x-csrftoken": csrf_token
        }
        res = session.post(login_url, json={"username": account, "password": password}, headers=headers)
        print(res.text)
        cookie = session.cookies.get_dict()
        print(cookie)
        self.cookie = "; ".join([f"{k}={v}" for k, v in cookie.items()])

    def get_cookie(self) -> str:
        if self.cookie is None:
            raise ValueError("cookie can not be None here")
        return self.cookie

    def do_get(self, path: str) -> requests.Response:
        if not path.startswith("/") and len(path) > 0:
            path = "/" + path
        res = requests.get(self.url + path, headers={"Cookie": self.get_cookie()})
        if not res.ok:
            raise requests.exceptions.RequestException(f"request to {res.url} fail, error code={res.status_code}")
        return res

    def do_post(self, path: str, data: dict) -> requests.Response:
        if not path.startswith("/") and len(path) > 0:
            path = "/" + path
        csrf_token = "".join(random.choices(string.ascii_letters + string.digits, k=64))
        headers = {
            "Referer": self.url,
            "Origin": self.url,
            "x-csrftoken": csrf_token,
            "Cookie": self.get_cookie() + ";csrftoken=" + csrf_token,
        }
        res = requests.post(self.url + path, headers=headers, json=data)
        if not res.ok:
            raise requests.exceptions.RequestException(f"request to {res.url} fail, error code={res.status_code}")
        return res

    def get_data(self, path: str):
        res = self.do_get(path)
        dat = res.json()
        if dat["error"]:
            if dat['data'] == 'Please login first.':
                self.login()
                return self.get_data(path)
            raise Exception(f"request to {res.url} fail, {dat['data']}")
        return dat["data"]

    def get_problem(self, pid: str) -> QingdaoUProblem:
        path = "/api/admin/problem?id=" + pid
        return QingdaoUProblem(self.get_data(path))

    def save_problem(self, problem: QingdaoUProblem):
        link = self.url + "/api/admin/problem"
        res = requests.put(link, json=problem.data, headers={"Cookie": self.get_cookie()})
        return res

    def get_ranking(self, contest_id: str, progress: bool = False) -> list:
        limit = 50
        the_range = trange if progress else range
        link = f"api/contest_rank?offset={{0}}&limit={limit}&contest_id=" + contest_id
        dat1 = self.get_data(link.format(0))
        cnt = dat1["total"]
        ret: list = dat1["results"]
        n = (cnt - 1) // limit
        for i in the_range(n):
            s = link.format(limit + i * limit)
            dat = self.get_data(s)
            ret.extend(dat["results"])
        return ret

    def get_submissions(self, contest_id: str, progress: bool = False, had: int = 0) -> list:
        the_range = trange if progress else range
        limit = 50
        link = f"api/contest_submissions?contest_id={contest_id}&limit={limit}&offset={{0}}"
        dat1 = self.get_data(link.format(0))
        cnt = dat1["total"]
        ret: list = dat1["results"]
        n = (cnt - had - 1) // limit
        for i in the_range(n):
            s = link.format(limit + i * limit)
            dat = self.get_data(s)
            ret.extend(dat["results"])
        for o in ret:
            o["result"] = submission_result_table.get(o["result"], "?")
        return ret[:cnt-had]

    def get_contest_problems(self, contest_id: str) -> list:
        link = "api/contest/problem?contest_id=" + contest_id
        return self.get_data(link)

    def count_ac(self, contest_id: str):
        ranking = self.get_ranking(contest_id)
        problems_data = self.get_contest_problems(contest_id)
        problems = {}
        for o in problems_data:
            problems[str(o["id"])] = {"id": o["_id"],
                                      "name": o["title"],
                                      "score": o["total_score"]}
        out = []
        for dat in ranking:
            handle = dat["user"]["username"]
            real_name = dat["user"]["real_name"]
            score = 0
            for k, v in dat["submission_info"].items():
                if k not in problems:
                    continue
                if v >= problems[k]["score"]:
                    score += 1
            out.append({"handle": handle, "real_name": real_name, "ac": score})
        out.sort(key=lambda obj: -obj["ac"])
        return {"all": len(problems_data), "rank": out}


def main():
    oj = QingdaoUOJ()


if __name__ == '__main__':
    main()
