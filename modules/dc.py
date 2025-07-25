import os

import discord
from discord import app_commands

from .tool import query_handle

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


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


@bot.event
async def on_ready():
    slash = await tree.sync()
    print(f"目前登入身份 --> {bot.user}")
    print(f"載入 {len(slash)} 個斜線指令")


@tree.command(description="查詢證書")
@app_commands.describe(username="要查詢的使用者名稱（可選）")
async def 查詢證書(interaction: discord.Interaction, username: str = None):
    allowed_channel_ids = [1392374490553516052, 1267373672126218243]
    if interaction.channel_id not in allowed_channel_ids:
        await interaction.response.send_message("❌ 此指令僅能在指定頻道中使用。", ephemeral=True)
        return
    if username is None:
        username = interaction.user.name
    result = query_data(username)
    await interaction.response.send_message(result)


def main():
    bot.run(os.environ["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    main()
