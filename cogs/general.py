import discord

from discord import app_commands
from discord.ext import commands

from services.disc import respond
from facades.user_preferences import update_value
from util.datatypes import CommandChoiceOption, Language
from util.identifiers import TextPieceID, UserPreferenceID


class GeneralCog(commands.Cog, name="general", description="Common commands"):
    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LANGUAGE.as_locale_str())
    @app_commands.describe(language=TextPieceID.COMMAND_OPTION_LANGUAGE_LANGUAGE.as_locale_str())
    @app_commands.choices(language=CommandChoiceOption.from_str_enum(Language))
    async def language(self, inter: discord.Interaction, language: str):
        await update_value(UserPreferenceID.LANGUAGE, inter.user, language)

        await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)


async def setup(bot):
    await bot.add_cog(GeneralCog(bot))