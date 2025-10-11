from discord.ext import commands
from dotenv import load_dotenv
import discord
import mylogger
import asyncio
import os
import pkgutil

load_dotenv()

logger = mylogger.getLogger(__name__)


class Pururin(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", intents=discord.Intents.default(), help_command=None
        )

    async def setup_hook(self) -> None:
        for module in pkgutil.iter_modules(["cogs"], prefix="cogs."):
            try:
                await self.load_extension(module.name)
            except commands.ExtensionAlreadyLoaded:
                mylogger.info(f"Extension {module.name} is already loaded")
            except commands.ExtensionNotFound:
                mylogger.error(f"Failed to load extension {module.name}")
            except commands.ExtensionFailed:
                mylogger.error(f"Failed to load extension {module.name}")
            except Exception as e:
                mylogger.error(f"Failed to load extension {module.name}", exc_info=e)
        await self.tree.sync()
        return await super().setup_hook()


async def main():
    bot = Pururin()
    try:
        await bot.start(os.getenv("TOKEN"))  # type: ignore
    except KeyboardInterrupt:
        pass
    except discord.LoginFailure:
        mylogger.error("Invalid token")
    finally:
        await bot.close()


asyncio.run(main())
