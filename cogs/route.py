import discord

from discord import app_commands, TextChannel
from discord.ext import commands

from config.routes import enlist
from services.disc import requires_permission, respond
from facades.routes import explain, reset_channel_id, update_channel_id, enable, disable
from util.datatypes import CommandChoiceOption
from util.exceptions import AlreadySatisfiesError
from util.format import as_channel, list_described_values
from util.identifiers import PermissionFlagID, RouteID, TextPieceID


class RouteCog(commands.GroupCog, name="route", description="Utilities for working with routes, which dictate whether and where the messages are delivered"):
    @app_commands.command(description="View details about a route")
    @app_commands.describe(route="Route to describe")
    @app_commands.choices(route=CommandChoiceOption.from_enum(RouteID))
    @requires_permission(PermissionFlagID.ADMIN)
    async def describe(self, inter: discord.Interaction, route: RouteID) -> None:
        route_details = explain(route)
        current_state = ':green_square: Включен' if route_details.is_enabled else ':red_square: Выключен'

        lines = [
            f"**Route `{route.value}`**",
            f"_{route_details.description}_",
            "",
            f"**Канал по умолчанию:** {as_channel(route_details.default_channel_id)}",
            f"**Текущий канал:** {as_channel(route_details.current_channel_id)}",
            f"**Текущее состояние:** {current_state}",
        ]

        await respond(inter, lines, ephemeral=True)

    @app_commands.command(description="Update a route's destination channel")
    @app_commands.describe(
        route="Route to update",
        new_value="New destination channel"
    )
    @app_commands.choices(route=CommandChoiceOption.from_enum(RouteID))
    @requires_permission(PermissionFlagID.ADMIN)
    async def update_channel(self, inter: discord.Interaction, route: RouteID, new_value: TextChannel) -> None:
        try:
            await update_channel_id(route, new_value.id, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Reset a route's destination channel to its default value")
    @app_commands.describe(route="Route to reset")
    @app_commands.choices(route=CommandChoiceOption.from_enum(RouteID))
    @requires_permission(PermissionFlagID.ADMIN)
    async def reset_channel(self, inter: discord.Interaction, route: RouteID) -> None:
        try:
            await reset_channel_id(route, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Enable a route, allowing the messages to be delivered through it")
    @app_commands.describe(route="Route to enable")
    @app_commands.choices(route=CommandChoiceOption.from_enum(RouteID))
    @requires_permission(PermissionFlagID.ADMIN)
    async def enable(self, inter: discord.Interaction, route: RouteID) -> None:
        try:
            await enable(route, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Disable a route, preventing the messages sent through it to be delivered")
    @app_commands.describe(route="Route to disable")
    @app_commands.choices(route=CommandChoiceOption.from_enum(RouteID))
    @requires_permission(PermissionFlagID.ADMIN)
    async def disable(self, inter: discord.Interaction, route: RouteID) -> None:
        try:
            await disable(route, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="List all available routes")
    @requires_permission(PermissionFlagID.ADMIN)
    async def list(self, inter: discord.Interaction) -> None:
        await respond(inter, list_described_values(enlist()), ephemeral=True)


async def setup(bot):
    await bot.add_cog(RouteCog(bot))