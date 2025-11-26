import asyncio
import os

import httpx


async def run(code, lang, inp):
    base_url = os.environ["ORANGEJUDGE_URL"].strip()
    username = os.environ["ORANGEJUDGE_USERNAME"].strip()
    api_key = os.environ["ORANGEJUDGE_API_KEY"].strip()
    url = base_url + "/api/submission"
    headers = {
        "api-key": api_key
    }
    async with (httpx.AsyncClient() as client):
        res = await client.post(url, data={
            "username": username,
            "pid": "test",
            "code": code,
            "lang": lang,
            "input": inp
        }, headers=headers)
        if res.status_code != 200:
            data = res.json()
            return "Failed to submit code: error " + str(res.status_code) + " - " + \
                data.get("description", "Unknown error")
        data = res.json()
        sub_id = data["data"]["submission_id"]
        url0 = f"{base_url}/api/submission?username={username}&submission_id={sub_id}"
        for _ in range(15):
            await asyncio.sleep(2)
            res = await client.get(url0, headers=headers)
            if res.status_code == 200:
                data = res.json()
                if data["data"]["completed"]:
                    res = data["data"]
                    if res["ce_msg"]:
                        return "Compilation Error:\n```\n" + res["ce_msg"].replace("`", "`\u200b") + "```"
                    ret = "Result: " + res["result"]
                    if res["output"].strip():
                        ret += "\nOutput:\n```\n" + res["output"].replace("`", "`\u200b") + "```"
                    if res["error"].strip():
                        ret += "\nStderr:\n```\n" + res["error"].replace("`", "`\u200b") + "```"
                    return ret
        return "Running time out."
