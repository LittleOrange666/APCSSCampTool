import asyncio
import json
import os
import threading
import traceback

import discord
from discord import app_commands
from discord.ui import Modal, TextInput

from .tool import query_handle, type_table, get_data
from .submit import run

intents = discord.Intents.all()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
allowed_channel_ids = [1392374490553516052, 1267373672126218243]
allowed_any_channel = True
OUTPUT_LIMIT = int(os.environ.get("OUTPUT_LIMIT", "10"))


@bot.event
async def on_ready():
    slash = await tree.sync()
    print(f"目前登入身份 --> {bot.user}")
    print(f"載入 {len(slash)} 個斜線指令")


def query_data(username: str) -> str:
    res = query_handle(username)
    if res is None:
        return f"❌ 使用者 {username!r} 不存在。"
    msg1 = "恭喜獲得基礎班結業證書！" if res['data'][
                                            0] >= 9600 else f"基礎班結業證書尚未達成，還差{9600 - res['data'][0]}分。"
    msg2 = "恭喜獲得進階班結業證書！" if res['data'][
                                            1] >= 7900 else f"進階班結業證書尚未達成，還差{7900 - res['data'][1]}分。"
    ret = f"""更新時間: {res['last_update']}
使用者名稱: {username}
基礎題進度: {res['data'][0]}/9600，{msg1}
進階題進度: {res['data'][1]}/7900，{msg2}"""
    return ret


@tree.command(name="查詢證書", description="查詢證書")
@app_commands.describe(username="要查詢的使用者名稱（可選）")
async def query_cmd(interaction: discord.Interaction, username: str = None):
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    if username is None:
        username = interaction.user.name
    await interaction.response.defer(thinking=True)
    try:
        result = query_data(username)
        await interaction.followup.send(result)
    except Exception as e:
        traceback.print_exception(e)
        await interaction.followup.send(content=f"❌ 發生錯誤，請洽詢管理員")


@tree.command(name="進度分析", description="進度分析")
@app_commands.describe(username="要查詢的使用者名稱（可選）")
async def query_progress(interaction: discord.Interaction, username: str = None):
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    if username is None:
        username = interaction.user.name
    await interaction.response.defer(thinking=True)
    try:
        res = query_handle(username)
        if res is None:
            await interaction.followup.send(f"❌ 使用者 {username!r} 不存在。")
            return
        detail = res['detail']
        msg = [f"使用者名稱: {username}", f"更新時間: {res['last_update']}"]
        for k, v in type_table.items():
            msg.append(f"{k} {v}: {detail[k][0]}/{detail[k][1]}, {detail[k][0] / detail[k][1] * 100:.2f}%")
        await interaction.followup.send("\n".join(msg))
    except Exception as e:
        traceback.print_exception(e)
        await interaction.followup.send(content=f"❌ 發生錯誤，請洽詢管理員")


@tree.command(name="組別排行", description="組別排行")
@app_commands.choices(group=[
    app_commands.Choice(name="基礎班", value="easy"),
    app_commands.Choice(name="進階班", value="hard"),
])
@app_commands.describe(group="要查詢的組別", count=f"要顯示的前幾名（預設為5，最多為{OUTPUT_LIMIT}）")
async def group_ranking(interaction: discord.Interaction, group: app_commands.Choice[str], count: int = 5):
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    try:
        if count <= 0:
            await interaction.followup.send("❌ 請輸入合法的數量。")
            return
        count = min(count, OUTPUT_LIMIT)
        idx = 0 if group.value == "easy" else 1
        data = get_data()
        res = [(v[idx], k) for k, v in data.items() if v[idx] > 0]
        res.sort(reverse=True, key=lambda x: x[0])
        count = min(count, len(res))
        res = res[:count]
        msg = [f"組別: {group.name}"]
        for i, (score, username) in enumerate(res, start=1):
            msg.append(f"{i}. {username}: {score} 分")
        await interaction.followup.send("\n".join(msg))
    except Exception as e:
        traceback.print_exception(e)
        await interaction.followup.send(content=f"❌ 發生錯誤，請洽詢管理員")


count_lock = threading.Lock()
count_cache = {}
count_cache_file = "data/count_cache.json"
if os.path.exists(count_cache_file):
    with open(count_cache_file, "r") as f:
        count_cache = json.load(f)


@tree.command(name="訊息排名", description="查詢目前訊息數排名")
@app_commands.describe(channel="目標頻道")
@app_commands.describe(output_cnt=f"要統計的訊息數量（預設為5，最多為{OUTPUT_LIMIT}）")
async def count_messages(interaction: discord.Interaction, channel: discord.TextChannel, output_cnt: int = 5):
    global count_using, count_cache
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    if count_lock.locked():
        await interaction.response.send_message("❌ 正在進行訊息數統計，請稍後再試。", ephemeral=True)
        return
    if output_cnt <= 0:
        await interaction.response.send_message("❌ 請輸入合法的訊息數量。", ephemeral=True)
        return
    with count_lock:
        await interaction.response.defer(thinking=True)
        try:
            ch_id = channel.id
            if ch_id in count_cache:
                result = count_cache[ch_id]
            else:
                result = {"data": {}, "start_msg": None}
            start_msg_obj = None if result["start_msg"] is None else await channel.fetch_message(result["start_msg"])
            msg_cnt = 0
            try:
                async for message in channel.history(limit=None, oldest_first=True, after=start_msg_obj):
                    if message.author.id not in result["data"]:
                        result["data"][message.author.id] = {"name": message.author.display_name, "count": 0}
                    result["data"][message.author.id]["count"] += 1
                    result["data"][message.author.id]["name"] = message.author.display_name
                    result["start_msg"] = message.id
                    msg_cnt += 1
                    if msg_cnt >= 100:
                        msg_cnt = 0
                        await asyncio.sleep(1)
            except discord.Forbidden:
                await interaction.edit_original_response(
                    content=f"❌ 無法讀取頻道 <#{channel.id}> 的歷史訊息，請確認機器人有足夠的權限。")
                return
            except Exception as e:
                await interaction.edit_original_response(content=f"❌ 發生錯誤: {str(e)}")
                return
            res = sorted(result["data"].items(), key=lambda x: x[1]["count"], reverse=True)
            count_cache[ch_id] = result
            with open(count_cache_file, "w") as f:
                json.dump(count_cache, f, indent=4)
            output_cnt = min(output_cnt, OUTPUT_LIMIT)
            if output_cnt > len(res):
                output_cnt = len(res)
            res = res[:output_cnt]
            msg = [f"頻道: <#{channel.id}>"]
            for i, (user_id, data) in enumerate(res, start=1):
                msg.append(f"{i}. {data['name']}: {data['count']} 則訊息")
            await interaction.followup.send(content="\n".join(msg))
        except Exception as e:
            traceback.print_exception(e)
            await interaction.followup.send(content=f"❌ 發生錯誤，請洽詢管理員")

lang_full_names = {
    "cpp": "C++17",
    "python": "Python3.10.12",
}


class CodeModal(Modal, title="輸入程式碼"):
    code = TextInput(label="程式碼內容", style=discord.TextStyle.paragraph, placeholder="貼上你的程式碼...",
                     max_length=4000)
    inp = TextInput(
        label="輸入內容",
        style=discord.TextStyle.paragraph,
        placeholder="貼上你的輸入內容...",
        required=False,
        max_length=4000
    )

    def __init__(self, lang: str):
        super().__init__()
        self.lang = lang
        self.code.label = f"程式碼 ({lang})"
        self.code.placeholder = f"請輸入 {lang} 程式碼..."
        self.inp.label = "輸入內容（可選）"
        self.inp.placeholder = "如果需要，請輸入測試用的輸入內容..."

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            code_content = self.code.value.strip()
            if not code_content:
                await interaction.followup.send("❌ 程式碼內容不能為空。", ephemeral=True)
                return
            inp_content = self.inp.value.strip() if self.inp.value else ""
            res = await run(code_content, lang_full_names[self.lang], inp_content)
            results = [f"Code:\n```{self.lang}\n{code_content}\n```"]
            if inp_content:
                results.append(f"Input:\n```\n{inp_content}\n```")
            results.append(res)
            await interaction.followup.send("\n".join(results))
        except Exception as e:
            traceback.print_exception(e)
            await interaction.followup.send(content=f"❌ 發生錯誤，請洽詢管理員")


@tree.command(name="執行程式", description="輸入程式碼並執行")
@app_commands.choices(lang=[
    app_commands.Choice(name="C++", value="cpp"),
    app_commands.Choice(name="Python", value="python"),
])
@app_commands.describe(lang="要選擇的語言")
async def code_command(interaction: discord.Interaction, lang: app_commands.Choice[str]):
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    await interaction.response.send_modal(CodeModal(lang.value))


def main():
    bot.run(os.environ["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    main()
