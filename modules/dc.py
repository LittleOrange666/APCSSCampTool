import asyncio
import datetime
import json
import os
import re
import traceback

import discord
from discord import app_commands
from discord.ui import Modal, TextInput

from .submit import run
from .tool import query_handle, type_table, get_data, name_table, all_names

intents = discord.Intents.all()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
allowed_channel_ids = [1392374490553516052, 1267373672126218243]
if "ALLOWED_CHANNEL_IDS" in os.environ:
    allowed_channel_ids = [int(x) for x in os.environ["ALLOWED_CHANNEL_IDS"].strip().split(",") if x.strip().isdigit()]
allowed_any_channel = True
OUTPUT_LIMIT = int(os.getenv("OUTPUT_LIMIT", "10"))

username_pattern = os.getenv("USERNAME_PATTERN", "aw(p|o)26[0-9]{2}")
no_ping = discord.AllowedMentions(users=False)
val1 = 12400
val2 = 6900
deadline = datetime.datetime(2027, 1, 1)

query_memory_file = "data/query_memory.json"
query_memory: dict[str, list[str]] = {}
if os.path.exists(query_memory_file):
    with open(query_memory_file) as f:
        query_memory = json.load(f)


def add_memory(user_id: int, value: str):
    user_id = str(user_id)
    if user_id not in query_memory:
        query_memory[user_id] = []
    if value in query_memory[user_id]:
        query_memory[user_id].remove(value)
    query_memory[user_id].append(value)
    if len(query_memory[user_id]) > 10:
        query_memory[user_id] = query_memory[user_id][-10:]
    with open(query_memory_file, "w") as f:
        json.dump(query_memory, f, indent=4)


def ack_memory(user_id: int, targets: list[str]):
    user_id = str(user_id)
    res = query_memory.get(user_id, [])
    targets.sort(key=lambda x: res.index(x) if x in res else -1, reverse=True)


@bot.event
async def on_ready():
    slash = await tree.sync()
    print(f"目前登入身份 --> {bot.user}")
    print(f"載入 {len(slash)} 個斜線指令")


async def name_autocomplete(interaction: discord.Interaction, current: str):
    user_id = interaction.user.id
    names = all_names()
    ack_memory(user_id, names)
    good_names = [x for x in names if x.startswith(current)][:25]
    return [app_commands.Choice(name=x + [" (非標準帳號)", " (標準帳號)"][x in name_table], value=x) for x in
            good_names]


def query_data_tmp(username: str) -> str:  # 證書未定義的臨時格式
    res = query_handle(username)
    if res is None:
        return f"❌ 使用者 {username!r} 無資料。"
    if username not in name_table:
        ex = "\n[警告] 此使用者名稱不是標準帳號，無法用於申請證書"
    else:
        ex = " (標準帳號)"
    ret = f"""更新時間: {res['last_update']}
使用者名稱: {username}{ex}
基礎題進度: {res['data'][0]}/????
進階題進度: {res['data'][1]}/????"""
    return ret


def query_data(username: str) -> str:
    if os.getenv("USE_TMP", "false").lower() == "true":
        return query_data_tmp(username)
    res = query_handle(username)
    if res is None:
        return f"❌ 使用者 {username!r} 無資料。"
    if username not in name_table:
        ex = "\n[警告] 此使用者名稱不是標準帳號，無法用於申請證書"
    else:
        ex = " (標準帳號)"
    msg1 = "恭喜獲得基礎班結業證書！" if res['data'][
                                            0] >= val1 else f"基礎班結業證書尚未達成，還差{val1 - res['data'][0]}分。"
    msg2 = "恭喜獲得進階班結業證書！" if res['data'][
                                            1] >= val2 else f"進階班結業證書尚未達成，還差{val2 - res['data'][1]}分。"
    ret = f"""更新時間: {res['last_update']}
使用者名稱: {username}{ex}
基礎題進度: {res['data'][0]}/{val1}，{msg1}
進階題進度: {res['data'][1]}/{val2}，{msg2}"""
    return ret


def query_data_pro(username: str) -> str:
    if os.getenv("USE_TMP", "false").lower() == "true":
        return "此功能尚未開放"
    if username not in name_table:
        return f"""唉你不能這樣啦
你要用那個as什麼的那個帳號來寫啊
你這樣用這什麼奇怪的`{username}`我是不認的啦"""
    res = query_handle(username)
    if res is None:
        return "❌ 查詢異常，請洽詢管理員"
    beg = f"""更新時間: {res['last_update']}
使用者名稱: {username}
"""
    last_update = datetime.datetime.strptime(res['last_update'], "%Y-%m-%d %H:%M:%S %Z")
    last_time = (deadline - last_update).total_seconds() / 86400
    score1 = res['data'][0]
    score2 = res['data'][1]
    suc1 = score1 >= val1
    suc2 = score2 >= val2
    last1 = val1 - score1
    last2 = val2 - score2
    if suc1 and suc2:
        return beg+"""大佬好強 :place_of_worship: 
居然已經完成所有證書了 :place_of_worship: 
大佬受我一拜 :place_of_worship: """
    if suc1:
        return beg+f"""恭喜你!
你已經完成了基礎班結業證書!
如果想要進階班結業證書可以再接再勵!
進階班結業證書還差{last2}分，每天寫個{last2/100/last_time:4.3f}題就可以了!"""
    if suc2:
        return beg+f"""恭喜你!
你已經完成了進階班結業證書!
如果想要基礎班結業證書可以再接再勵!
基礎班結業證書還差{last1}分，每天寫個{last1/100/last_time:4.3f}題就可以了!"""
    return beg+f"""目前你都還沒有完成證書
要再接再厲!
基礎班結業證書還差{last1}分，每天寫個{last1/100/last_time:4.3f}題就可以了!
進階班結業證書還差{last2}分，每天寫個{last2/100/last_time:4.3f}題就可以了!
加油!"""


@tree.command(name="查詢證書", description="查詢證書")
@app_commands.describe(username="要查詢的使用者名稱")
@app_commands.rename(username="使用者名稱")
@app_commands.autocomplete(username=name_autocomplete)
async def query_cmd(interaction: discord.Interaction, username: str):
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    user_id = interaction.user.id
    add_memory(user_id, username)
    try:
        result = query_data(username)
        await interaction.followup.send(result)
    except Exception as e:
        traceback.print_exception(e)
        await interaction.followup.send(content="❌ 發生錯誤，請洽詢管理員")


@tree.command(name="查詢證書pro", description="查詢證書pro")
@app_commands.describe(username="要查詢的使用者名稱")
@app_commands.rename(username="使用者名稱")
@app_commands.autocomplete(username=name_autocomplete)
async def query_cmd_pro(interaction: discord.Interaction, username: str):
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    user_id = interaction.user.id
    add_memory(user_id, username)
    try:
        result = query_data_pro(username)
        await interaction.followup.send(result)
    except Exception as e:
        traceback.print_exception(e)
        await interaction.followup.send(content="❌ 發生錯誤，請洽詢管理員")


@tree.command(name="進度分析", description="進度分析")
@app_commands.describe(username="要查詢的使用者名稱")
@app_commands.rename(username="使用者名稱")
@app_commands.autocomplete(username=name_autocomplete)
async def query_progress(interaction: discord.Interaction, username: str):
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    user_id = interaction.user.id
    add_memory(user_id, username)
    try:
        res = query_handle(username)
        if res is None:
            await interaction.followup.send(f"❌ 使用者 {username!r} 不存在。")
            return
        detail = res['detail']
        msg = [f"使用者名稱: {username}", f"更新時間: {res['last_update']}"]
        for k, v in type_table.items():
            rate = detail[k][0] / (detail[k][1] or 1) * 100
            msg.append(f"{k} {v}: {detail[k][0]}/{detail[k][1]}, {rate:.2f}%")
        await interaction.followup.send("\n".join(msg))
    except Exception as e:
        traceback.print_exception(e)
        await interaction.followup.send(content="❌ 發生錯誤，請洽詢管理員")


@tree.command(name="組別排行", description="組別排行")
@app_commands.choices(group=[
    app_commands.Choice(name="基礎班", value="easy"),
    app_commands.Choice(name="進階班", value="hard"),
])
@app_commands.describe(group="要查詢的組別", count=f"要顯示的前幾名（預設為5，最多為{OUTPUT_LIMIT}）")
@app_commands.rename(group="組別", count="數量")
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
        await interaction.followup.send(content="❌ 發生錯誤，請洽詢管理員")


count_lock = asyncio.Lock()
count_cache = {}
count_cache_file = "data/count_cache.json"
if os.path.exists(count_cache_file):
    with open(count_cache_file) as f:
        count_cache = json.load(f)


@tree.command(name="訊息排名", description="查詢目前訊息數排名")
@app_commands.describe(channel="目標頻道", count=f"要統計的訊息數量（預設為5，最多為{OUTPUT_LIMIT}）")
@app_commands.rename(channel="頻道", count="數量")
async def count_messages(interaction: discord.Interaction, channel: discord.TextChannel, count: int = 5):
    global count_cache
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    if count_lock.locked():
        await interaction.response.send_message("❌ 正在進行訊息數統計，請稍後再試。", ephemeral=True)
        return
    if count <= 0:
        await interaction.response.send_message("❌ 請輸入合法的訊息數量。", ephemeral=True)
        return
    async with count_lock:
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
            output_cnt = min(count, OUTPUT_LIMIT)
            if output_cnt > len(res):
                output_cnt = len(res)
            res = res[:output_cnt]
            msg = [f"頻道: <#{channel.id}>"]
            for i, (user_id, data) in enumerate(res, start=1):
                msg.append(f"{i}. <@{user_id}>: {data['count']} 則訊息")
            await interaction.followup.send(content="\n".join(msg), allowed_mentions=no_ping)
        except Exception as e:
            traceback.print_exception(e)
            await interaction.followup.send(content="❌ 發生錯誤，請洽詢管理員")


lang_full_names = {
    "cpp": "C++17",
    "python": "Python3.10.12",
    "java": "Java8",
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
            code_content = code_content.replace("`", "`\u200b")
            results = [f"Code:\n```{self.lang}\n{code_content}\n```"]
            if inp_content:
                inp_content = inp_content.replace("`", "`\u200b")
                results.append(f"Input:\n```\n{inp_content}\n```")
            results.append(res)
            result_text = "\n".join(results)
            if len(result_text) > 2000:
                result_text = result_text[:1970]
                if result_text.count("```") % 2 == 1:
                    result_text += "\n...\n```\n...(truncated)"
                else:
                    result_text += "\n...(truncated)"
            await interaction.followup.send(result_text)
        except Exception as e:
            traceback.print_exception(e)
            await interaction.followup.send(content="❌ 發生錯誤，請洽詢管理員")


@tree.command(name="執行程式", description="輸入程式碼並執行")
@app_commands.choices(lang=[
    app_commands.Choice(name="C++17", value="cpp"),
    app_commands.Choice(name="Python3.10.12", value="python"),
    app_commands.Choice(name="Java8", value="java"),
])
@app_commands.describe(lang="要選擇的語言")
@app_commands.rename(lang="語言")
async def code_command(interaction: discord.Interaction, lang: app_commands.Choice[str]):
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    await interaction.response.send_modal(CodeModal(lang.value))


@tree.command(name="破冰", description="破冰")
async def ice_breaker(interaction: discord.Interaction):
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    await interaction.response.send_message("Ciallo～(∠・ω< )⌒★")


convenor_pat = re.compile(r"^\[(.+?)\]\s+(.+)$")


@tree.command(name="總召", description="總召")
@app_commands.describe(
    user="交大最帥最強最電最有錢又會刷題比賽又會刷榜又會刷車票又會刷卡讓學妹們每天都黏在身邊的陽光籃球富豪總召",
    role_name="總召為何")
@app_commands.rename(user="總召", role_name="稱呼")
async def convenor(interaction: discord.Interaction, user: discord.User | None = None, role_name: str | None = None):
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    if user is None:
        user = interaction.user
    if role_name is None:
        role_name = "總召"
    name = user.display_name
    res = convenor_pat.match(name)
    if res:
        name = "[" + role_name + "/" + res.group(1) + "] " + res.group(2)
    else:
        name = "[" + role_name + "] " + name
    await interaction.response.send_message(f"你好，@{name}", allowed_mentions=no_ping)


@tree.command(name="jenny", description="jenny")
@app_commands.describe(
    user="Jenny",
    description="在電機系卻身兼競程、資安、開發、無人機等多項技能的資訊圈六邊形天才！未來世界的領頭羊，電機資工機械全都能多開！年紀輕輕就擁有臺大雙博士學位，CF、ATcoder紅人，人見人愛，左擁右抱，光是高一就考統測拿下電機電子群國排一，還囊括物奧、化奧、資奧、生奧、數奧、語奧金牌！智商高達3141592653589793 的超級電神！不過偶爾有點小暴力，打人超痛喔，而且見一個暈一個，還涵蓋所有樂器，木吉他finger style更是無人能及！還是寶可夢大師，甚至是水劍龜Vmax！電腦科學和體育細胞也拉滿的絕世奇才！大招是火箭頭槌！而且還會被別人認成厲害的男生！將會是2026圖靈獎得主！教授，你好，三軍統帥，川普的私生母，五星上將！好的，哥們！ :_1:")
@app_commands.rename(user="jenny", description="描述")
async def jenny(interaction: discord.Interaction, user: discord.User | None = None, description: str | None = None):
    if interaction.channel_id not in allowed_channel_ids and not allowed_any_channel:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    if user is None:
        user = interaction.user
    if description is None:
        description = "在電機系卻身兼競程、資安、開發、無人機等多項技能的資訊圈六邊形天才！未來世界的領頭羊，電機資工機械全都能多開！年紀輕輕就擁有臺大雙博士學位，CF、ATcoder紅人，人見人愛，左擁右抱，光是高一就考統測拿下電機電子群國排一，還囊括物奧、化奧、資奧、生奧、數奧、語奧金牌！智商高達3141592653589793 的超級電神！不過偶爾有點小暴力，打人超痛喔，而且見一個暈一個，還涵蓋所有樂器，木吉他finger style更是無人能及！還是寶可夢大師，甚至是水劍龜Vmax！電腦科學和體育細胞也拉滿的絕世奇才！大招是火箭頭槌！而且還會被別人認成厲害的男生！將會是2026圖靈獎得主！教授，你好，三軍統帥，川普的私生母，五星上將！好的，哥們！ :_1:"
    user_id = user.id
    msg = f"<@{user_id}> 喔～就是那位{description}"
    await interaction.response.send_message(msg, allowed_mentions=no_ping)


def main():
    bot.run(os.environ["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    main()
