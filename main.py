from discord.ext import commands
from dotenv import load_dotenv
import discord
import mylogger
import asyncio
import os

load_dotenv()

logger = mylogger.getLogger(__name__)


class Pururin(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", intents=discord.Intents.default(), help_command=None
        )


async def main():
    bot = Pururin()
    try:
        await bot.start(os.getenv("TOKEN")) # type: ignore
    except KeyboardInterrupt:
        pass
    except discord.LoginFailure:
        mylogger.error("Invalid token")
    finally:
        await bot.close()


asyncio.run(main())
