import asyncio
import os

import httpx


async def run(code, lang, inp):
    base_url = os.environ["ORANGEJUDGE_URL"].strip()
    username = os.environ["ORANGEJUDGE_USERNAME"].strip()
    api_key = os.environ["ORANGEJUDGE_API_KEY"].strip()
    url = base_url+"/api/submit"
    headers = {
        "x-api-key": api_key
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
                        return "Compilation Error:\n```\n" + res["ce_msg"] + "```"
                    if res["result"][:2] == "OK":
                        return res["result"]+"\nOutput:\n```\n" + res["output"] + "```"
                    return "Result: " + res["result"]
        return "Running time out."
