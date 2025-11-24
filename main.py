from discord.ext import commands
from dotenv import load_dotenv
import discord
import mylogger
import asyncio
import os
import pkgutil
import webserver # Trick Render

load_dotenv()

logger = mylogger.getLogger(__name__)


class Pururin(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            chunk_guilds_at_startup=False,
            max_messages=None,
        )

    async def setup_hook(self) -> None:
        modules = list(pkgutil.iter_modules(["exts"], prefix="exts."))

        tasks = []
        for module in modules:
            task = asyncio.create_task(self._load_extension_safe(module.name))
            tasks.append(task)  # type: ignore

        results = await asyncio.gather(*tasks, return_exceptions=True)  # type: ignore

        for module, result in zip(modules, results):  # type: ignore
            if isinstance(result, Exception):
                logger.error(f"Failed to load {module.name}: {result}")
            elif result is True:
                logger.info(f"Loaded extension {module.name}")

        synced = await self.tree.sync()
        logger.info(f"Synced {len(synced)} commands")

        return await super().setup_hook()

    async def _load_extension_safe(self, module_name: str) -> bool:
        try:
            await self.load_extension(module_name)
            return True
        except commands.ExtensionAlreadyLoaded:
            logger.info(f"Extension {module_name} is already loaded")
            return True
        except (
            commands.ExtensionNotFound,
            commands.ExtensionFailed,
            commands.NoEntryPointError,
        ) as e:
            logger.error(f"Failed to load extension {module_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading {module_name}", exc_info=e)
            return False

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
