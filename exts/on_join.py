import discord
from discord.ext import commands


class OnMember(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        member_role_id = os.getenv("MEMBER_ROLE_ID")
        if not member_role_id:
            raise EnvironmentError(
                "MEMBER_ROLE_ID is not set in environment variables."
            )

        try:
            member_role_id = int(member_role_id)
        except ValueError as e:
            raise EnvironmentError(f"Invalid MEMBER_ROLE_ID value: {e}")

        role = member.guild.get_role(member_role_id)
        if not role:
            raise LookupError(
                f"Role with ID {member_role_id} not found in guild {member.guild.name} ({member.guild.id})"
            )

        try:
            await member.add_roles(role, reason="Auto-assign on join")
        except discord.Forbidden as e:
            raise PermissionError(
                f"Missing permissions to assign role {role.name}: {e}"
            )
        except discord.HTTPException as e:
            raise discord.DiscordException(
                f"Failed to assign role {role.name} to {member}: {e}"
            )


async def setup(bot):
    await bot.add_cog(OnMember(bot))
