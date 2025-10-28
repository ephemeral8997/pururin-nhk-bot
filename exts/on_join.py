import os
import discord
from discord.ext import commands
import mylogger

logger = mylogger.getLogger(__name__)


class OnMember(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_member_join")
    async def on_autorole(self, member: discord.Member):
        member_role_id = os.getenv("MEMBER_ROLE_ID")
        if not member_role_id:
            logger.error("MEMBER_ROLE_ID not set in environment")
            return

        try:
            member_role_id = int(member_role_id)
        except ValueError:
            logger.error(f"Invalid MEMBER_ROLE_ID: {member_role_id}")
            return

        role = member.guild.get_role(member_role_id)
        if not role:
            logger.error(f"Role {member_role_id} not found in {member.guild.name}")
            return

        try:
            await member.add_roles(role, reason="Auto-assign on join")
            logger.info(f"Assigned {role.name} to {member}")
        except discord.Forbidden:
            logger.error(f"Missing permissions to assign {role.name}")
        except discord.HTTPException as e:
            logger.error(f"Failed to assign {role.name} to {member}: {e}")

    @commands.Cog.listener("on_member_join")
    async def on_welcome(self, member: discord.Member):
        welcome_channel_id = os.getenv("WELCOME_CHANNEL_ID")
        if not welcome_channel_id:
            return

        try:
            channel = self.bot.get_channel(int(welcome_channel_id))
        except ValueError:
            logger.error(f"Invalid WELCOME_CHANNEL_ID: {welcome_channel_id}")
            return

        if channel:
            message = (
                "📡 **NHK Newsflash** 📡\n\n"
                f"Breaking: {member.mention} has just joined our community!\n"
                "🎉 Welcome aboard 🎉\n\n"
                "Fun Fact of the Day: *Welcome to the new members!*"
            )
            try:
                await channel.send(message)  # type: ignore
            except discord.HTTPException as e:
                logger.error(f"Failed to send welcome message: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(OnMember(bot))
