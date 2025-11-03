# public library
import discord
from discord.ext import commands
import os
import asyncio
import websockets
import json
from logging import (
    DEBUG, ERROR, INFO, WARNING,
    Formatter, BASIC_FORMAT, Logger,
    StreamHandler, getLogger
)
import logging
from dotenv import load_dotenv
# other module
import eew

load_dotenv()

CHANNEL_ID = os.getenv("CHANNEL_ID")
TOKEN = os.getenv("TOKEN")
WS_URI=os.getenv("WS_URI")
WS_TOKEN=os.getenv("WS_TOKEN")
LOGGING_LEVEL=os.getenv("LOGGING_LEVEL")

# intents settings
intents=discord.Intents.none()
intents.reactions = True
intents.guilds = True
intents.messages = True
intents.message_content = True

# logging settings
logger: Logger = getLogger("botLogger")
logHandler = StreamHandler()
logHandler.setFormatter(Formatter(BASIC_FORMAT))
logging.lastResort.setLevel(DEBUG)
logging.lastResort.setFormatter(Formatter(BASIC_FORMAT))
if LOGGING_LEVEL == "DEBUG":
    logger.setLevel(DEBUG)
    logHandler.setLevel(DEBUG)
elif LOGGING_LEVEL == "INFO":
    logger.setLevel(INFO)
    logHandler.setLevel(INFO)
elif LOGGING_LEVEL == "ERROR":
    logger.setLevel(ERROR)
    logHandler.setLevel(ERROR)
else:
    logger.setLevel(WARNING)
    logHandler.setLevel(WARNING)
logger.addHandler(logHandler)

# client of connect to websocket
async def websocketClient(uri):
    # get channel info
    count = 0
    channel = bot.get_partial_messageable(CHANNEL_ID)
    while not channel and count < 10:
        logger.warning("Channel not found. Search again after 2sec...")
        await asyncio.sleep(2)
        channel = bot.get_partial_messageable(CHANNEL_ID)
        count += 1

    if not channel:
        logger.error("Channel not found. Please check ID or bot permissions.")
        return

    await channel.send(content="Nyaaa! (logged in!)")
    logger.info(f"Channel found. Connecting to {uri}...")

    retryCount = 0
    # connecting websocket server
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logger.info("P2Pquake connected!")
                retryCount = 0
                while True:
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            
                            embedObj = eew.formatData(logger, data)
                            logger.debug("format data end.")

                            if embedObj:
                                await channel.send(
                                    content=None, 
                                    embed=embedObj[0],
                                    file=embedObj[1]
                                )
                        except json.JSONDecodeError:
                            logger.error(f"decode json fail!!!: {message}")
                            break
                        except Exception as e:
                            logger.error(f"processing msg error!!!: {e}")
                            break
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket disconnected!!!: {e}")
        except Exception as e:
            logger.error(f"WebSocket connection error!!!: {e}")
            
        if retryCount >= 10:
            break

        if retryCount >= 5:
            await channel.send(content=f"Connection to P2Pquake failed more than 5 times. Reconnecting in 5 seconds... ")
        
        await asyncio.sleep(5)
        retryCount = retryCount + 1


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
    logger.info(f'{bot.user} logged in.')

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
