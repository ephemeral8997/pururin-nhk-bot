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
CHANNEL_ID_ENV_VAR = "WIKI_RC_CHANNEL_ID"
WEBHOOK_NAME_ENV_VAR = "WIKI_RC_WEBHOOK_NAME"


class Fandom(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = None
        self.latest_rcid = None
        self.webhook = None
        self.channel_id = int(os.getenv(CHANNEL_ID_ENV_VAR, "0"))
        self.webhook_name = os.getenv(WEBHOOK_NAME_ENV_VAR, "f/WelcomeToTheNHK")

    async def cog_load(self):
        self.session = aiohttp.ClientSession()
        await self._bootstrap_latest_rcid()
        await self._ensure_webhook()
        self.rc_loop.start()
        logger.info("Fandom cog loaded")

    async def cog_unload(self):
        if self.session:
            await self.session.close()
        if self.rc_loop.is_running():
            self.rc_loop.cancel()
        logger.info("Fandom cog unloaded")

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
                logger.debug(f"Bootstrapped rcid={self.latest_rcid}")
        except Exception as e:
            logger.exception(f"Bootstrap failed: {e}")

    async def _ensure_webhook(self):
        if not self.channel_id:
            logger.warning("No channel ID set")
            return
        channel = self.bot.get_channel(self.channel_id)
        if not isinstance(channel, discord.TextChannel):
            logger.error("Invalid channel ID")
            return
        hooks = await channel.webhooks()
        for hook in hooks:
            if hook.name == self.webhook_name:
                self.webhook = hook
                logger.info(f"Using existing webhook {self.webhook_name}")
                return
        self.webhook = await channel.create_webhook(name=self.webhook_name)
        logger.info(f"Created new webhook {self.webhook_name}")

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
                await self.webhook.send(embed=embed, username=self.webhook_name)
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
            sign = "+" if size_delta >= 0 else "-"
            embed.add_field(name="Size", value=f"{sign}{size_delta}", inline=True)
        embed.add_field(name="Diff", value=f"[Open]({diff_url})", inline=True)
        return embed

    @rc_loop.before_loop
    async def before_rc_loop(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Fandom(bot))
