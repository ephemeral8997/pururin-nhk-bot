from discord.ext import commands, tasks
import discord
import itertools
import mylogger

logger = mylogger.getLogger(__name__)


class ActivityRotator(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.activities = itertools.cycle(
            [
                discord.Activity(
                    type=discord.ActivityType.playing, name="Purupuru Pururin~ 🎶"
                ),
                discord.Activity(
                    type=discord.ActivityType.watching,
                    name="Satou spiral into conspiracy theories 👀",
                ),
                discord.Activity(
                    type=discord.ActivityType.listening, name="Moe tunes on loop 💿"
                ),
                discord.Activity(
                    type=discord.ActivityType.competing,
                    name="Waifu popularity contest 💘",
                ),
                discord.Activity(
                    type=discord.ActivityType.streaming,
                    name="Pururin's Magical Adventures 📺",
                ),
            ]
        )

        self.rotate_status.start()

    @tasks.loop(minutes=10)
    async def rotate_status(self):
        activity = next(self.activities)
        await self.bot.change_presence(activity=activity)
        logger.info(f"Changed activity to: {activity.name}")

    @rotate_status.before_loop
    async def before_rotate_status(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(ActivityRotator(bot))
