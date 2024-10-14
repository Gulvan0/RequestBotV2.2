import discord
from discord.app_commands import CheckFailure
from discord.ext import commands

from services.disc import respond_forbidden


class ExceptionHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        bot.tree.error(coro = self.__dispatch_to_app_command_handler)

    async def __dispatch_to_app_command_handler(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        self.bot.dispatch("app_command_error", interaction, error)

    @commands.Cog.listener("on_app_command_error")
    async def get_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, CheckFailure):
            await respond_forbidden(interaction)

async def setup(bot: commands.Bot):
    await bot.add_cog(ExceptionHandler(bot))