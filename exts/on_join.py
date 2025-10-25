import discord
from discord.ext import commands
import mylogger
import os

logger = mylogger.getLogger(__name__)


class OnJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        logger.info(f"New member joined: {member} (ID: {member.id})")

        if member.bot:
            logger.info(f"Skipping bot account: {member}")
            return

        role_id = os.getenv("MEMBER_ROLE_ID")
        if not role_id:
            logger.error("MEMBER_ROLE_ID not set in environment variables.")
            return

        try:
            role_id = int(role_id)
        except ValueError:
            logger.error(f"Invalid MEMBER_ROLE_ID value: {role_id}")
            return

        role = member.guild.get_role(role_id)
        if not role:
            logger.error(
                f"Role with ID {role_id} not found in guild {member.guild.name} ({member.guild.id})"
            )
            return

        try:
            await member.add_roles(role, reason="Auto-assign on join")
            logger.info(
                f"Assigned role '{role.name}' (ID: {role.id}) to member {member} (ID: {member.id})"
            )
        except discord.Forbidden:
            logger.error(
                f"Missing permissions to assign role '{role.name}' in guild {member.guild.name}"
            )
        except discord.HTTPException as e:
            logger.error(f"Failed to assign role '{role.name}' to {member}: {e}")


async def setup(bot):
    await bot.add_cog(OnJoin(bot))
