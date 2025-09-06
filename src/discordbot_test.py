import discord
import os

TOKEN = os.environ["TOKEN"]

# intents設定
intents=discord.Intents.none()
intents.reactions = True
intents.guilds = True
intents.messages = True
intents.message_content = True

# 接続クライアント生成
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    # 起動時
    print('sasami_test logined.')

@client.event
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    # nekoとしてのやつ
    if message.content == '/neko':
        await message.channel.send('にゃー')
    if message.content == '/cat':
        await message.channel.send('meow')
    if message.content == '/naderu':
        await message.channel.send('purr...purr...')

# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
