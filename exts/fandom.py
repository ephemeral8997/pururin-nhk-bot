import os
import aiohttp
import discord
from discord.ext import commands, tasks
import mylogger

logger = mylogger.getLogger(__name__)

API_ENDPOINT = "https://welcometothenhk.fandom.com/api.php"
WIKI_BASE = "https://welcometothenhk.fandom.com"
POLL_INTERVAL_SECONDS = 15

CHANNEL_ID = int(os.getenv("WIKI_RC_CHANNEL_ID", "0"))
WEBHOOK_NAME = os.getenv("WIKI_RC_WEBHOOK_NAME", "f/WelcomeToTheNHK")


class Fandom(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.poll_changes.start()

    async def cog_unload(self):
        self.poll_changes.cancel()

    @tasks.loop(seconds=POLL_INTERVAL_SECONDS)
    async def poll_changes(self):
        if CHANNEL_ID == 0:
            logger.warning("No channel ID configured for Fandom cog.")
            return

        channel = self.bot.get_channel(CHANNEL_ID)
        if channel is None:
            logger.warning("Channel with ID %s not found.", CHANNEL_ID)
            return

        params = {
            "action": "query",
            "list": "recentchanges",
            "rcprop": "ids|title|user|comment|timestamp",
            "rclimit": "1",
            "format": "json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_ENDPOINT, params=params) as resp:
                    if resp.status != 200:
                        logger.error("API request failed with status %s", resp.status)
                        return
                    data = await resp.json()
        except Exception as e:
            logger.exception("Error fetching recent changes: %s", e)
            return

        changes = data.get("query", {}).get("recentchanges", [])
        if not changes:
            return

        change = changes[0]
        rcid = str(change["rcid"])

        last_messages = [m async for m in channel.history(limit=10)]  # type: ignore
        for msg in last_messages:  # type: ignore
            if msg.author.bot and msg.embeds:  # type: ignore
                embed = msg.embeds[0]  # type: ignore
                if embed.footer and embed.footer.text == f"rcid:{rcid}":  # type: ignore
                    return

        embed = discord.Embed(
            title=change["title"],
            url=f"{WIKI_BASE}/?curid={change['pageid']}",
            description=change.get("comment", "(no summary)"),
            color=discord.Color.blue(),
            timestamp=discord.utils.parse_time(change["timestamp"]),  # type: ignore
        )
        embed.set_author(name=change["user"])
        embed.set_footer(text=f"rcid:{rcid}")

        webhooks = await channel.webhooks()  # type: ignore
        webhook = discord.utils.get(webhooks, name=WEBHOOK_NAME)  # type: ignore
        if webhook is None:
            webhook = await channel.create_webhook(name=WEBHOOK_NAME)  # type: ignore
            logger.info("Created webhook '%s' in channel %s", WEBHOOK_NAME, CHANNEL_ID)

        await webhook.send(  # type: ignore
            embed=embed,
        )
        logger.info(
            "Posted recent change rcid=%s by %s on %s",
            rcid,
            change["user"],
            change["title"],
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Fandom(bot))
