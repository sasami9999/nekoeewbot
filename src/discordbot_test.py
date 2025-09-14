import discord
from discord.ext import commands
import os
import asyncio
import websockets

CHANNEL_ID = os.getenv("CHANNEL_ID")
TOKEN = os.getenv("TOKEN")
WS_URI=os.getenv("WS_URI")
WS_TOKEN=os.getenv("WS_TOKEN")

# intents settings
intents=discord.Intents.none()
intents.reactions = True
intents.guilds = True
intents.messages = True
intents.message_content = True

# client of connect to websocket
async def websocketClient(uri):
    # get channel info
    count = 0
    channel = bot.get_partial_messageable(CHANNEL_ID)
    while not channel and count < 10:
        print("Channel not found. Search again after 2sec...")
        await asyncio.sleep(2)
        channel = bot.get_partial_messageable(CHANNEL_ID)
        count += 1

    if not channel:
        print("[ERROR] Channel not found. Please check ID or bot permissions.")
        return

    print(f"Channel found. Connecting to {uri}...")

    # connecting websocket server
    async with websockets.connect(uri) as websocket:
        # if need auth token, send auth token here
        await websocket.send(WS_TOKEN)
        print("Connected.")
        
        # receive message from server
        async def receive_msg():
            try:
                while True:
                    msg = await websocket.recv()
                    print(f"Receive message from server: {msg}")
                    if channel:
                        await channel.send(f"message from other client:\n{msg}")
                    else:
                        print("Cannot send message. channel is null.")
            except websockets.ConnectionClosedOK:
                print("[INFO] Connection closed normaly.")
            except websockets.ConnectionClosedError:
                print("[ERROR] Connection lost due to an unexpected error")

        try:
            async with asyncio.TaskGroup() as tg:
                task = tg.create_task(receive_msg())
                await task
        except Exception as err:
            print(f"{err.exceptions=}")

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        # wake websocket client
        self.loop.create_task(websocketClient(WS_URI))

# client for discord
bot = MyBot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} logged in.')

@bot.event
async def on_message(message):
    # ignore when the sender is a bot
    if message.author.bot:
        return
    # as cat
    if message.content == '/neko':
        await message.channel.send('にゃー')

    if message.content == '/cat':
        await message.channel.send('meow')
        
    if message.content == '/naderu':
        await message.channel.send('purr...purr...')

# wake bot and connecing channel
bot.run(TOKEN)
