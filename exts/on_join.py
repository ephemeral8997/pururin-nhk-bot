import os
import discord
from discord.ext import commands
import mylogger

logger = mylogger.getLogger(__name__)


class OnMember(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
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


async def setup(bot: commands.Bot):
    await bot.add_cog(OnMember(bot))
