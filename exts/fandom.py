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
            "rcprop": "ids|title|user|comment|timestamp|sizes|flags",
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

        HIDE_MINOR = os.getenv("WIKI_RC_HIDE_MINOR", "false").lower() in (
            "1",
            "true",
            "yes",
        )

        changes = data.get("query", {}).get("recentchanges", [])
        if not changes:
            return

        change = changes[0]
        is_minor = "minor" in change
        print(is_minor)

        if HIDE_MINOR and is_minor:
            logger.info(
                "Skipping minor edit rcid=%s by %s on %s",
                change["rcid"],
                change["user"],
                change["title"],
            )
            return

        rcid = str(change["rcid"])

        last_messages = [m async for m in channel.history(limit=10)]  # type: ignore
        for msg in last_messages:  # type: ignore
            if msg.author.bot and msg.embeds:  # type: ignore
                embed = msg.embeds[0]  # type: ignore
                if embed.footer and embed.footer.text == f"rcid:{rcid}":  # type: ignore
                    return

        revid = change.get("revid")
        old_revid = change.get("old_revid")
        if old_revid:
            diff_url = f"{WIKI_BASE}/wiki/Special:Diff/{revid}/{old_revid}"
        else:
            diff_url = f"{WIKI_BASE}/wiki/Special:Diff/{revid}"

        size_diff = ""
        if "oldlen" in change and "newlen" in change:
            diff_val = change["newlen"] - change["oldlen"]
            sign = "+" if diff_val >= 0 else ""
            size_diff = f"{sign}{diff_val} bytes"

        color = discord.Color.blue()
        color = discord.Color.blue()
        if "new" in change:
            color = discord.Color.green()
        elif is_minor:
            color = discord.Color.gold()

        embed = discord.Embed(
            title=change["title"],
            url=diff_url,
            description=change.get("comment", "(no summary)"),
            color=color,
            timestamp=discord.utils.parse_time(change["timestamp"]),  # type: ignore
        )
        embed.set_author(name=change["user"])
        if size_diff:
            embed.add_field(name="Size Change", value=size_diff, inline=True)
        embed.add_field(name="Revision ID", value=str(revid), inline=True)
        embed.set_footer(text=f"rcid:{rcid}")

        webhooks = await channel.webhooks()  # type: ignore
        webhook = discord.utils.get(webhooks, name=WEBHOOK_NAME)  # type: ignore
        if webhook is None:
            webhook = await channel.create_webhook(name=WEBHOOK_NAME)  # type: ignore
            logger.info("Created webhook '%s' in channel %s", WEBHOOK_NAME, CHANNEL_ID)

        await webhook.send(embed=embed)  # type: ignore
        logger.info(
            "Posted recent change rcid=%s by %s on %s",
            rcid,
            change["user"],
            change["title"],
        )

    @poll_changes.before_loop
    async def before_fetch(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Fandom(bot))
