import discord

from discord import app_commands
from discord.ext import commands

from services.disc import post, respond
from util.datatypes import CommandChoiceOption, Language
from util.format import as_channel, as_role
from util.identifiers import RouteID, TextPieceID


class ResponseType(CommandChoiceOption):
    EPHEMERAL = "Ephemeral"
    REAL = "Real"
    SEPARATE = "Separate"
    BY_ROUTE_AND_TEXT_PIECE = "By route + text"


class GeneralCog(commands.GroupCog, name="general", description="A super cog"):
    @app_commands.command(description="Respond with a pong")
    @app_commands.describe(response_type="Response type")
    @app_commands.choices(response_type=ResponseType.to_choice_list())
    async def ping(self, inter: discord.Interaction, response_type: str):
        match response_type:
            case ResponseType.EPHEMERAL:
                await respond(inter, str(inter.user.id), ephemeral=True)
            case ResponseType.REAL:
                await respond(inter, inter.user.mention)
            case ResponseType.SEPARATE:
                await inter.client.get_channel(1180557849206734909).send(as_channel(1180557849206734909))
                await respond(inter, as_role(1293687410651041907), ephemeral=True)
            case ResponseType.BY_ROUTE_AND_TEXT_PIECE:
                await respond(inter, as_role(1293687410651041907), ephemeral=True)


async def setup(bot):
    await bot.add_cog(GeneralCog(bot))