import discord
from discord.ext import commands
import mylogger

logger = mylogger.getLogger(__name__)


class ErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_error(self, event_method, *args, **kwargs):
        logger.error(f"Unhandled exception in event '{event_method}':", exc_info=True)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You don’t have permission to use this command.")
        else:
            logger.error(f"Error in command '{ctx.command}': {error}", exc_info=True)

    @commands.Cog.listener()
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ):
        logger.error(f"Slash command error: {error}", exc_info=True)
        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    "⚠️ Something went wrong.", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "⚠️ Something went wrong.", ephemeral=True
                )
        except Exception as notify_error:
            logger.error(
                f"Failed to notify user of error: {notify_error}", exc_info=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))
