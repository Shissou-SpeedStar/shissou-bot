import discord
import os
from keep_alive import keep_alive
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timezone, timedelta
import time
import aiohttp

intents = discord.Intents.all()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --- 設定 ---
ALLOWED_GUILD_IDS = {1235503983179730944,1268381411904323655,1268199427865055345,1314588938358226986}
BOT_ID = 1347068262969774110
JST = timezone(timedelta(hours=9))

# 設定
SERVICE_ID = os.getenv("RENDER_SERVICE_ID")
API_KEY = os.getenv("RENDER_API_KEY")
WAKE_URL = "https://shippuu-bot.onrender.com/resume"  # 疾風ボットのresumeエンドポイント
PING_URL = "https://shippuu-bot.onrender.com/ping"
BOOT_LOG_CHANNEL = 1428880974820937902  # チャンネルIDを整数で
# ヘッダー
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    )
}

# --- イベント ---
@client.event
async def on_guild_join(guild):
    if guild.id not in ALLOWED_GUILD_IDS:
        print(f"❌ 許可されていないサーバー ({guild.name}) に参加したため退出します。")
        try:
            await guild.leave()
        except Exception as e:
            print(f"⚠️ サーバーから退出できませんでした: {e}")
    else:
        print(f"✅ 許可されたサーバー ({guild.name}) に参加しました。")

@client.event
async def on_ready():
    print('✅ ログインしました')
    activity = discord.Activity(name='疾風スピードスター', type=discord.ActivityType.competing)
    await client.change_presence(status=discord.Status.online, activity=activity)
    await tree.sync()
    if not auto_wake.is_running():
        auto_wake.start()

# --- コマンド: サーバー人数表示 ---
@tree.command(name='membercount', description='サーバーの人数を表示します')
@app_commands.default_permissions(administrator=True)
async def member_count(interaction: discord.Interaction):
    guild = interaction.guild
    await interaction.response.send_message(f'今の人数は {guild.member_count} 人です。')

# --- コマンド: ステータス確認 ---
@tree.command(name="stats", description="疾風Botの稼働状態を確認します")
@app_commands.default_permissions(administrator=True)
async def stats(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    start_time = time.monotonic()
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(PING_URL, timeout=5) as resp:
                end_time = time.monotonic()
                ping_ms = round((end_time - start_time) * 1000, 2)
                if resp.status == 200:
                    data = await resp.json()
                    status_text = data.get("status", "unknown")

                    embed = discord.Embed(
                        title="📊 疾風Bot ステータスレポート",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="🌐 状態", value=f"🟢 {status_text.capitalize()}", inline=True)
                    embed.add_field(name="📡 応答速度", value=f"`{ping_ms} ms`", inline=True)
                    embed.add_field(name="🔢 ステータスコード", value=f"`{resp.status}`", inline=True)
                    embed.set_footer(text=f"最終チェック: {datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')} (JST)")
                    await interaction.followup.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="📊 疾風Bot ステータスレポート",
                        description=f"⚠️ 応答に異常があります（HTTP {resp.status}）",
                        color=discord.Color.orange()
                    )
                    await interaction.followup.send(embed=embed)
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="📊 疾風Bot ステータスレポート",
            description="🔴 疾風Botはオフライン、またはスリープ状態です（タイムアウト）。",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="📊 疾風Bot ステータスレポート",
            description=f"❌ 予期せぬエラーが発生しました:\n```{e}```",
            color=discord.Color.dark_red()
        )
        await interaction.followup.send(embed=embed)

# --- /boot コマンド ---
@bot.tree.command(name="boot", description="疾風Botサーバーを起動します")
@app_commands.default_permissions(administrator=True)
async def boot(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    async with aiohttp.ClientSession() as session:
        # ① 起動リクエスト送信
        try:
            async with session.post(WAKE_URL, timeout=10) as resp:
                text = await resp.text()
                await interaction.followup.send(
                    f"⚙️ 起動リクエスト送信: HTTP {resp.status}\n```\n{text}\n```"
                )
                if resp.status not in (200, 202):
                    await interaction.followup.send("❌ 起動リクエストが期待どおりの応答ではありませんでした。")
                    return
        except Exception as e:
            await interaction.followup.send(f"❌ 起動リクエストに失敗しました: {e}")
            return
        # ② 起動完了まで待機
        await interaction.followup.send("⌛ 起動を確認中…（最大 5 分待機）")
        MAX_WAIT_TIME = 300  # 秒
        CHECK_INTERVAL = 15  # 秒
        start_time = time.monotonic()
        elapsed = 0
        while elapsed < MAX_WAIT_TIME:
            await asyncio.sleep(CHECK_INTERVAL)
            elapsed = time.monotonic() - start_time
            try:
                async with session.get(PING_URL, timeout=5) as ping_resp:
                    if ping_resp.status == 200:
                        data = await ping_resp.json()
                        status_text = data.get("status", "unknown")
                        boot_time = round(elapsed, 1)
                        embed = discord.Embed(
                            title="✅ 疾風Bot 起動確認完了",
                            description=f"状態：**{status_text}**\n起動時間：約 `{boot_time} 秒`",
                            color=discord.Color.green(),
                        )
                        embed.set_footer(
                            text=f"最終確認：{datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')} JST"
                        )
                        await interaction.followup.send(embed=embed)
                        return
                    else:
                        print(f"🔄 起動待機中… HTTP {ping_resp.status} (経過 {int(elapsed)} 秒)")
            except Exception as e:
                print(f"🔄 起動確認エラー：{e} (経過 {int(elapsed)} 秒)")
        # ③ タイムアウト
        embed = discord.Embed(
            title="❌ 起動確認タイムアウト",
            description=f"最大待機時間 {MAX_WAIT_TIME} 秒を超えました。\n疾風Botがまだ起動準備中の可能性があります。",
            color=discord.Color.red(),
        )
        embed.set_footer(
            text=f"最終確認：{datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')} JST"
        )
        await interaction.followup.send(embed=embed)


# --- 自動起動チェック ---
@tasks.loop(hours=1)
async def auto_wake():
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        try:
            async with session.get(PING_URL, timeout=10) as resp:
                if resp.status == 200:
                    return  # すでに起動している
        except Exception:
            pass
        try:
            async with session.get(WAKE_URL) as wake_resp:
                channel = client.get_channel(BOOT_LOG_CHANNEL)
                if wake_resp.status == 200:
                    await channel.send("✅ 疾風Botを再起動しました！")
                else:
                    await channel.send(f"⚠️ 応答コード: {wake_resp.status}")
        except Exception as e:
            channel = client.get_channel(BOOT_LOG_CHANNEL)
            await channel.send(f"❌ 自動起動中にエラー発生: {e}")

# --- 実行 ---
TOKEN = os.getenv("DISCORD_TOKEN")
keep_alive()
client.run(TOKEN)
