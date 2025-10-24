import os
import aiohttp
import discord
import datetime
from discord.ext import commands, tasks
import mylogger

logger = mylogger.getLogger(__name__)

API_ENDPOINT = "https://welcometothenhk.fandom.com/api.php"
WIKI_BASE = "https://welcometothenhk.fandom.com"
POLL_INTERVAL_SECONDS = 15
CHANNEL_ID = int(os.getenv("WIKI_RC_CHANNEL_ID", "0"))
WEBHOOK_NAME = "f/WelcomeToTheNHK"


class FandomRecentChanges(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = None
        self.latest_rcid = None
        self.webhook = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()
        await self._bootstrap_latest_rcid()
        await self._ensure_webhook()
        self.rc_loop.start()
        logger.info("FandomRecentChanges cog loaded and loop started")

    async def cog_unload(self):
        if self.session:
            await self.session.close()
        if self.rc_loop.is_running():
            self.rc_loop.cancel()
        logger.info("FandomRecentChanges cog unloaded and loop stopped")

    async def _bootstrap_latest_rcid(self):
        try:
            params = {
                "action": "query",
                "list": "recentchanges",
                "rcprop": "ids",
                "rclimit": 1,
                "format": "json",
            }
            async with self.session.get(API_ENDPOINT, params=params) as resp:
                data = await resp.json()
            rc = data.get("query", {}).get("recentchanges", [])
            if rc:
                self.latest_rcid = rc[0].get("rcid")
                logger.debug(f"Bootstrapped latest_rcid={self.latest_rcid}")
        except Exception as e:
            logger.exception(f"Failed to bootstrap latest_rcid: {e}")

    async def _ensure_webhook(self):
        if not CHANNEL_ID:
            logger.warning("No WIKI_RC_CHANNEL_ID set")
            return
        channel = self.bot.get_channel(CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            logger.error("Invalid channel ID for webhook")
            return
        hooks = await channel.webhooks()
        for hook in hooks:
            if hook.name == WEBHOOK_NAME:
                self.webhook = hook
                logger.info(f"Using existing webhook {WEBHOOK_NAME}")
                return
        self.webhook = await channel.create_webhook(name=WEBHOOK_NAME)
        logger.info(f"Created new webhook {WEBHOOK_NAME}")

    @tasks.loop(seconds=POLL_INTERVAL_SECONDS)
    async def rc_loop(self):
        if not self.webhook:
            return
        try:
            params = {
                "action": "query",
                "list": "recentchanges",
                "rcprop": "title|ids|user|comment|timestamp|sizes",
                "rclimit": 10,
                "rcdir": "newer",
                "format": "json",
            }
            if self.latest_rcid:
                params["rcstartid"] = self.latest_rcid
            async with self.session.get(API_ENDPOINT, params=params) as resp:
                data = await resp.json()
            changes = data.get("query", {}).get("recentchanges", [])
            new_events = []
            for ev in changes:
                rcid = ev.get("rcid")
                if self.latest_rcid is None or (rcid and rcid > self.latest_rcid):
                    new_events.append(ev)
            for ev in new_events:
                embed = self._build_embed(ev)
                await self.webhook.send(embed=embed, username=WEBHOOK_NAME)
                if ev.get("rcid"):
                    self.latest_rcid = ev["rcid"]
                    logger.debug(f"Posted rcid={self.latest_rcid}")
        except Exception as e:
            logger.exception(f"Error in rc_loop: {e}")

    def _build_embed(self, ev: dict) -> discord.Embed:
        title = ev.get("title", "Unknown")
        user = ev.get("user", "Unknown")
        comment = ev.get("comment") or "(no summary)"
        ts = ev.get("timestamp")
        revid = ev.get("revid")
        newlen = ev.get("newlen")
        oldlen = ev.get("oldlen")
        size_delta = None
        if newlen is not None and oldlen is not None:
            size_delta = newlen - oldlen
        if revid:
            diff_url = f"{WIKI_BASE}/wiki/Special:Diff/{revid}"
        else:
            diff_url = f"{WIKI_BASE}/wiki/{title.replace(' ','_')}?action=history"
        page_url = f"{WIKI_BASE}/wiki/{title.replace(' ','_')}"
        embed = discord.Embed(
            title=title,
            url=page_url,
            description=comment,
            timestamp=(
                datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if ts
                else None
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Editor", value=user, inline=True)
        if size_delta is not None:
            sign = "+" if size_delta >= 0 else ""
            embed.add_field(name="Size", value=f"{sign}{size_delta}", inline=True)
        embed.add_field(name="Diff", value=f"[Open]({diff_url})", inline=True)
        return embed

    @rc_loop.before_loop
    async def before_rc_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(FandomRecentChanges(bot))
