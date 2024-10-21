import discord

from discord import app_commands
from discord.ext import commands

from services.disc import respond
from user_preferences import update_value
from util.datatypes import CommandChoiceOption, Language
from util.identifiers import TextPieceID, UserPreferenceID


class GeneralCog(commands.Cog, name="general", description="Common commands"):
    @app_commands.command(description="Sets the bot's language")
    @app_commands.describe(language="Language you want the bot to speak with you")
    @app_commands.choices(language=CommandChoiceOption.from_str_enum(Language))
    async def language(self, inter: discord.Interaction, language: str):
        update_value(UserPreferenceID.LANGUAGE, inter.user, language)

        await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)


async def setup(bot):
    await bot.add_cog(GeneralCog(bot))