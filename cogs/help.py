import discord

from discord import app_commands
from discord.ext import commands

from services.disc import respond
from util.identifiers import TextPieceID


class HelpCog(commands.GroupCog, name="help", description="Explanations for various complicated aspects of the bot"):
    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_HELP_DURATION.as_locale_str())
    async def duration(self, inter: discord.Interaction):
        await respond(inter, TextPieceID.HELP_DURATION, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_HELP_TIMESTAMP.as_locale_str())
    async def timestamp(self, inter: discord.Interaction):
        await respond(inter, TextPieceID.HELP_TIMESTAMP, ephemeral=True)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))