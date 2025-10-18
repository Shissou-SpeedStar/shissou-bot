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
async def member_count(message):
    # message インスタンスから guild インスタンスを取得
    guild = message.guild 
    # ユーザとBOTを区別しない場合
    member_count = guild.member_count
    await message.response.send_message(f'今の人数は{member_count}です')
@tree.command(name="boot", description="メインBotを起動します")
async def wake_bot(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    status = await check_bot_status()
    if status == "offline":
        msg = await ping_render()
        await interaction.followup.send(f"🔴 BotBはオフライン → {msg}")
    elif status == "online":
        await interaction.followup.send("🟢 BotBはすでにオンラインです！")
    else:
        await interaction.followup.send(f"⚪ BotBの状態が不明です: {status}")
        

async def ping_render():
    async with aiohttp.ClientSession() as session:
            try:
                async with session.get(WAKE_URL) as resp:
                    if resp.status == 200:
                        await interaction.followup.send("✅ 疾風を起動しました！")
                    else:
                        await interaction.followup.send(f"⚠️ ステータスコード: {resp.status}")
            except Exception as e:
                await interaction.followup.send(f"❌ エラーが発生しました: {e}")

async def check_bot_status() -> str:
    """BotBの現在のステータスを取得"""
    user = client.get_user(BOT_ID)
    if user is None:
        # キャッシュに存在しない場合 → サーバー経由で取得
        for guild in client.guilds:
            member = guild.get_member(BOT_ID)
            if member:
                user = member
                break
    if user and hasattr(user, "status"):
        return str(user.status)  # online, offline, idle, dnd
    return "unknown"

async def ping_render():
    guild = member.guild
    shippuu-bot = guild.get_member(BOT_ID)  # Probotのステータスを取得
    if shippuu-bot is None or shippuu-bot.status == discord.Status.offline:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(WAKE_URL) as resp:
                    if resp.status == 200:
                        return "✅ 疾風を起動しました！（HTTP 200）"
                        channel_id = '1428880974820937902'
                        channel = client.get_channel(channel_id)
                        await channel.send("✅ 疾風を起動しました！（HTTP 200）")
                    else:
                        return f"⚠️ ステータスコード: {resp.status}"
            except Exception as e:
                return f"❌ エラーが発生しました: {e}"
# 1時間ごとの自動チェック
@tasks.loop(hours=1)
async def auto_wake():
    print("⏰ 自動チェック開始")
    status = await check_bot_status()
    if status == "offline":
        print("🔴 BotBがオフライン。起動します。")
        result = await ping_render()
        print(result)
    else:
        print(f"🟢 BotBはオンラインです。（状態: {status}）")

TOKEN = os.getenv("DISCORD_TOKEN")
# Web サーバの立ち上げ
keep_alive()
client.run(TOKEN)
