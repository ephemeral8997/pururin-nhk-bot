import os
import discord
from discord.ext import commands, tasks
import aiohttp
import mylogger

logger = mylogger.getLogger(__name__)


class WelcomeNHKFeed(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_id = int(os.getenv("REDDIT_WELCOME_CHANNEL_ID", 0))
        self.last_post_id = None
        self.webhook_name = "r/WelcomeToTheNHK"
        self.fetch_reddit_posts.start()

    async def cog_unload(self) -> None:
        self.fetch_reddit_posts.cancel()

    @staticmethod
    def truncate_text(text: str, limit: int = 500) -> str:
        if not text:
            return "*No description.*"
        if len(text) <= limit:
            return text

        truncated = text[:limit]
        if " " in truncated:
            truncated = truncated.rsplit(" ", 1)[0]
        return truncated + "..."

    @tasks.loop(minutes=10)
    async def fetch_reddit_posts(self):
        if not self.channel_id:
            logger.debug("Channel ID not set, skipping fetch")
            return

        url = "https://www.reddit.com/r/WelcomeToTheNHK/new.json?limit=1"
        headers = {"User-Agent": "DiscordBot/1.0"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        logger.warning(f"Reddit API status {resp.status}")
                        return
                    data = await resp.json()
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {e}")
            return

        try:
            post = data["data"]["children"][0]["data"]
            post_id = post["id"]
            logger.info(f"Fetched: {post_id} - {post['title']}")
        except Exception as e:
            logger.error(f"Error parsing Reddit post: {e}")
            return

        if post_id == self.last_post_id:
            logger.debug("No new post")
            return

        self.last_post_id = post_id
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            logger.warning(f"Channel {self.channel_id} not found")
            return

        embed = discord.Embed(
            title=post["title"],
            url=f"https://reddit.com{post['permalink']}",
            description=self.truncate_text(post.get("selftext", ""), 500),
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow(),
        )

        embed.set_thumbnail(
            url="https://www.redditstatic.com/desktop2x/img/favicon/apple-icon-57x57.png"
        )

        if flair := post.get("link_flair_text"):
            embed.add_field(name="Flair", value=flair, inline=True)

        embed.add_field(name="Upvotes", value=str(post.get("ups", 0)), inline=True)
        embed.add_field(
            name="Comments", value=str(post.get("num_comments", 0)), inline=True
        )

        if (img := post.get("url_overridden_by_dest", "")) and img.endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".webp")
        ):
            embed.set_image(url=img)

        if crosspost := post.get("crosspost_parent_list"):
            origin = crosspost[0].get("subreddit_name_prefixed", "Unknown")
            embed.add_field(name="Crossposted from", value=origin, inline=False)

        embed.set_footer(text=f"Posted by u/{post.get('author', 'unknown')}")

        try:
            webhooks = await channel.webhooks()  # type: ignore
            webhook = discord.utils.get(webhooks, name=self.webhook_name)  # type: ignore

            if not webhook:
                webhook = await channel.create_webhook(name=self.webhook_name)  # type: ignore
                logger.info(f"Created webhook: {self.webhook_name}")

            history = [msg async for msg in channel.history(limit=10)]  # type: ignore
            for msg in history:  # type: ignore
                if msg.webhook_id == webhook.id and msg.embeds:  # type: ignore
                    if msg.embeds[0].url == embed.url:  # type: ignore
                        logger.info("Post already sent, skipping")
                        return

            await webhook.send(embed=embed, username=self.webhook_name)  # type: ignore
            logger.info(f"Posted to {channel.name}")  # type: ignore
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")

    @fetch_reddit_posts.before_loop
    async def before_fetch(self):
        await self.bot.wait_until_ready()
        logger.info("Starting Reddit fetch loop")


async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeNHKFeed(bot))
