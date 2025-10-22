import discord
import os
from keep_alive import keep_alive
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import random
from datetime import datetime, timezone, timedelta
import time
import requests
import json
from urllib.parse import urlparse  # emoji
import aiohttp

intents=discord.Intents.all()
intents.message_content = True
intents.members = True  # メンバー参加イベントを取得するために必要
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

WAKE_URL = "https://shippuu-bot.onrender.com/"  # RenderのURL
BOOT_LOG_CHANNEL = 1428880974820937902
ALLOWED_GUILD_IDS = {1235503983179730944,1268381411904323655,1268199427865055345,1314588938358226986}  # ✅ Botが所属できるサーバーIDをここに記入（複数対応可）
BOT_ID = 1347068262969774110  # botのユーザーID
# 日本時間（JST）
JST = timezone(timedelta(hours=9))

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
    print('ログインしました')
    # アクティビティを設定
    activity = discord.Activity(name='疾風スピードスター', type=discord.ActivityType.competing)
    await client.change_presence(status=discord.Status.online, activity=activity)
    # スラッシュコマンドを同期
    await tree.sync()
    if not auto_wake.is_running():
        auto_wake.start()  # 自動起動タスクを開始

#スラッシュコマンド
@tree.command(name='membercount', description='サーバーの人数を表示します') 
@app_commands.default_permissions(administrator=True)
async def member_count(message):
    # message インスタンスから guild インスタンスを取得
    guild = message.guild 
    # ユーザとBOTを区別しない場合
    member_count = guild.member_count
    await message.response.send_message(f'今の人数は{member_count}です')

PING_URL = "https://shippuu-bot.onrender.com/ping"  # 新しいping用エンドポイント
@tree.command(name="stats", description="疾風Botの稼働状態を確認します")
@app_commands.default_permissions(administrator=True)
async def stats(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    start_time = time.monotonic()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PING_URL, timeout=5) as resp:
                end_time = time.monotonic()
                ping_ms = round((end_time - start_time) * 1000, 2)
                # ステータスチェック
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
                        description=f"⚠️ 疾風Botが応答しましたが異常があります。\nHTTPコード: `{resp.status}`",
                        color=discord.Color.orange()
                    )
                    await interaction.followup.send(embed=embed)
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="📊 疾風Bot ステータスレポート",
            description="🔴 疾風Botはオフライン、またはスリープ状態です（タイムアウト）。",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"最終チェック: {datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')} (JST)")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="📊 疾風Bot ステータスレポート",
            description=f"❌ 予期せぬエラーが発生しました:\n```{e}```",
            color=discord.Color.dark_red()
        )
        embed.set_footer(text=f"最終チェック: {datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')} (JST)")
        await interaction.followup.send(embed=embed)
    
@tree.command(name="boot", description="疾風Botサーバーを起動します")
@app_commands.default_permissions(administrator=True)
async def boot(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    MAX_WAIT_TIME = 120  # 最大待機時間（秒）
    RETRY_INTERVAL = 10  # 再試行間隔（秒）
    async with aiohttp.ClientSession() as session:
        start_time = time.monotonic()
        elapsed = 0
        await interaction.followup.send("⚙️ 疾風Botのサーバーを起動中です。少々お待ちください...", ephemeral=True)
        while elapsed < MAX_WAIT_TIME:
            try:
                async with session.get(WAKE_URL, timeout=10) as resp:
                    if resp.status == 200:
                        end_time = time.monotonic()
                        boot_time = round(end_time - start_time, 1)
                        await interaction.followup.send(
                            f"✅ 疾風Botがオンラインになりました！（起動時間: `{boot_time} 秒`）"
                        )
                        return
                    elif resp.status in (429, 502, 503):
                        print(f"⚠️ 起動待機中... ステータス: {resp.status}")
                        await asyncio.sleep(RETRY_INTERVAL)
                    else:
                        await interaction.followup.send(f"⚠️ 予期しない応答: HTTP {resp.status}")
                        return
            except asyncio.TimeoutError:
                print("⏳ タイムアウト。再試行します。")
                await asyncio.sleep(RETRY_INTERVAL)
            except Exception as e:
                await interaction.followup.send(f"❌ エラーが発生しました: {e}")
                return
            elapsed = time.monotonic() - start_time
        await interaction.followup.send("⏰ 起動待機時間がタイムアウトしました（2分経過しても起動しませんでした）。")
             
# 1時間ごとの自動チェック
@tasks.loop(hours=1)
async def auto_wake():
    async with aiohttp.ClientSession() as session:
        try:
            # --- ① まず /ping にアクセスしてオンライン確認 ---
            async with session.get(PING_URL, timeout=10) as resp:
                if resp.status == 200:
                    return  # 起動不要なので終了
        except asyncio.TimeoutError:
            print("🕓 タイムアウト: サーバーはスリープ中の可能性あり。")
        except Exception as e:
            print(f"⚠️ /ping 接続エラー: {e}")
        # --- ② /ping に失敗したら / へアクセスして起動 ---
        try:
            async with session.get(WAKE_URL) as wake_resp:
                channel = client.get_channel(BOOT_LOG_CHANNEL)
                if wake_resp.status == 200:
                    await channel.send("✅ 疾風Botを再起動しました！")
                else:
                    await channel.send(f"⚠️ 起動リクエストを送信しました。応答コード: {wake_resp.status}")
        except Exception as e:
            channel = client.get_channel(BOOT_LOG_CHANNEL)
            await channel.send(f"❌ 起動リクエスト中にエラーが発生しました: {e}")

TOKEN = os.getenv("DISCORD_TOKEN")
# Web サーバの立ち上げ
keep_alive()
client.run(TOKEN)
