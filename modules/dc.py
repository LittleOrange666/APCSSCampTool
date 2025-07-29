import asyncio
import json
import os
import threading

import discord
from discord import app_commands

from .tool import query_handle, type_table

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
allowed_channel_ids = [1392374490553516052, 1267373672126218243]


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
    if interaction.channel_id not in allowed_channel_ids:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    if username is None:
        username = interaction.user.name
    result = query_data(username)
    await interaction.response.send_message(result)


@tree.command(name="進度分析", description="進度分析")
@app_commands.describe(username="要查詢的使用者名稱（可選）")
async def query_progress(interaction: discord.Interaction, username: str = None):
    if interaction.channel_id not in allowed_channel_ids:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    if username is None:
        username = interaction.user.name
    res = query_handle(username)
    if res is None:
        await interaction.response.send_message(f"❌ 使用者 {username!r} 不存在。")
        return
    detail = res['detail']
    msg = [f"使用者名稱: {username}", f"更新時間: {res['last_update']}"]
    for k, v in type_table.items():
        msg.append(f"{k} {v}: {detail[k][0]}/{detail[k][1]}, {detail[k][0] / detail[k][1] * 100:.2f}%")
    await interaction.response.send_message("\n".join(msg))


count_lock = threading.Lock()
count_cache = {}
count_cache_file = "data/count_cache.json"
if os.path.exists(count_cache_file):
    with open(count_cache_file, "r") as f:
        count_cache = json.load(f)


@tree.command(name="訊息排名", description="查詢目前訊息數排名")
@app_commands.describe(channel="目標頻道")
@app_commands.describe(output_cnt="要統計的訊息數量（預設為5，最多為10）")
async def count_messages(interaction: discord.Interaction, channel: discord.TextChannel, output_cnt: int = 5):
    global count_using, count_cache
    if interaction.channel_id not in allowed_channel_ids:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    if count_lock.locked():
        await interaction.response.send_message("❌ 正在進行訊息數統計，請稍後再試。", ephemeral=True)
        return
    with count_lock:
        await interaction.response.send_message(f"正在統計頻道 <#{channel.id}> 的訊息數，請稍候...")
        ch_id = channel.id
        if ch_id in count_cache:
            result = count_cache[ch_id]
        else:
            result = {"data": {}, "start_msg": None}
        start_msg_obj = None if result["start_msg"] is None else await channel.fetch_message(result["start_msg"])
        msg_cnt = 0
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
        res = sorted(result["data"].items(), key=lambda x: x[1]["count"], reverse=True)
        count_cache[ch_id] = result
        with open(count_cache_file, "w") as f:
            json.dump(count_cache, f, indent=4)
        if output_cnt > len(res):
            output_cnt = len(res)
        res = res[:output_cnt]
        msg = [f"頻道: <#{channel.id}>"]
        for i, (user_id, data) in enumerate(res, start=1):
            msg.append(f"{i}. {data['name']}: {data['count']} 則訊息")
        await interaction.edit_original_response(content="\n".join(msg))


def main():
    bot.run(os.environ["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    main()
