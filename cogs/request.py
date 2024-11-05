import discord
from discord import app_commands
from discord.ext import commands

from services.disc import requires_permission, respond
from util.identifiers import PermissionFlagID, TextPieceID


class RequestCog(commands.GroupCog, name="request", description="Commands for managing requests"):
    @app_commands.command(description="Request a level")
    async def create(self, inter: discord.Interaction) -> None:
        await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)


async def setup(bot):
    await bot.add_cog(RequestCog(bot))