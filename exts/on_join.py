import discord
from discord.ext import commands


class OnJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not member.bot:
            role = member.guild.get_role(os.getenv("MEMBER_ROLE_ID", 0))
            if role:
                await member.add_roles(role)


async def setup(bot):
    await bot.add_cog(OnJoin(bot))
