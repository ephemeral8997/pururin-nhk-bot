from discord.ext import commands
from dotenv import load_dotenv
import discord

load_dotenv()


class Pururin(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", intents=discord.Intents.default(), help_command=None
        )
