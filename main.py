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

intents=discord.Intents.all()
intents.message_content = True
intents.members = True  # メンバー参加イベントを取得するために必要
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

ALLOWED_GUILD_IDS = {1235503983179730944,1268381411904323655,1268199427865055345}  # ✅ Botが所属できるサーバーIDをここに記入（複数対応可）
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

#スラッシュコマンド
@tree.command(name='membercount', description='サーバーの人数を表示します') 
async def member_count(message):
    # message インスタンスから guild インスタンスを取得
    guild = message.guild 
    # ユーザとBOTを区別しない場合
    member_count = guild.member_count
    await message.response.send_message(f'今の人数は{member_count}です')
@tree.command(name='boot', description='botを起動します') 
async def bot_boot(message):
    url = "https://shissou-bot.onrender.com/"
    try:
        response = requests.get(url)
        await message.response.send_message("起動完了")
    except requests.exceptions.RequestException as e:
        await message.response.send_message("エラーが発生しました:", e)

@client.event
async def on_message(message):
    emoji ="👍"
    await message.add_reaction(emoji)

TOKEN = os.getenv("DISCORD_TOKEN")
# Web サーバの立ち上げ
keep_alive()
client.run(TOKEN)
