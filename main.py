from discord.ext import commands
from dotenv import load_dotenv
import discord
import mylogger
import asyncio
import os
import pkgutil
import webapp # type: ignore # Trick LeapCode into running the webserver
load_dotenv()

logger = mylogger.getLogger(__name__)


class Pururin(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self) -> None:
        for module in pkgutil.iter_modules(["exts"], prefix="exts."):
            try:
                await self.load_extension(module.name)
            except commands.ExtensionAlreadyLoaded:
                logger.info(f"Extension {module.name} is already loaded")
            except commands.ExtensionNotFound:
                logger.error(f"Failed to load extension {module.name}")
            except commands.ExtensionFailed:
                logger.error(f"Failed to load extension {module.name}")
            except commands.NoEntryPointError:
                logger.error(f"{module.name} has no setup() function")
            except Exception as e:
                logger.error(f"Failed to load extension {module.name}", exc_info=e)
            else:
                logger.info(f"Loaded extension {module.name}")
        await self.tree.sync()
        return await super().setup_hook()

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")


async def main():
    bot = Pururin()
    try:
        await bot.start(os.getenv("TOKEN"))  # type: ignore
    except KeyboardInterrupt:
        pass
    except discord.LoginFailure:
        logger.error("Invalid token")
    finally:
        await bot.close()


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
