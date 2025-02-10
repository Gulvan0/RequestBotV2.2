import discord
from discord import app_commands
from discord.ext import commands

from components.views.pagination.log import LogPaginationView
from facades.eventlog import LoadedLogFilter
from facades.parameters import get_value as get_parameter_value, update_value as update_parameter_value
from facades.requests import count_pending_requests
from services.disc import post_raw_text, requires_permission, respond
from util.exceptions import AlreadySatisfiesError
from util.identifiers import LoggedEventTypeID, ParameterID, PermissionFlagID, RouteID, TextPieceID


class QueueCog(commands.GroupCog, name="queue", description="Commands for controlling request queue"):
    @app_commands.command(description="Open a queue manually. Note that you might also want to disable auto-block")
    @requires_permission(PermissionFlagID.ADMIN)
    async def open(self, inter: discord.Interaction) -> None:
        try:
            await update_parameter_value(ParameterID.QUEUE_BLOCKED, "false")
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await post_raw_text(
                RouteID.REQUESTS_REOPENED,
                "<@everyone> Requests have been reopened / Реквесты были открыты"
            )
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Close a queue manually. Note that you might also want to disable auto-unblock")
    @requires_permission(PermissionFlagID.ADMIN)
    async def close(self, inter: discord.Interaction) -> None:
        try:
            await update_parameter_value(ParameterID.QUEUE_BLOCKED, "false")
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await post_raw_text(
                RouteID.REQUESTS_CLOSED,
                "<@everyone> Requests are temporarily closed / Реквесты временно закрыты"
            )
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Get info regarding the current state of the queue")
    @requires_permission(PermissionFlagID.ADMIN)
    async def info(self, inter: discord.Interaction) -> None:
        await respond(
            inter,
            TextPieceID.QUEUE_INFO,
            substitutions=dict(
                header=TextPieceID.QUEUE_INFO_CLOSED_HEADER if get_parameter_value(ParameterID.QUEUE_BLOCKED, bool) else TextPieceID.QUEUE_INFO_OPEN_HEADER,
                pending_cnt=await count_pending_requests(),
                blocks_at=get_parameter_value(ParameterID.QUEUE_BLOCK_AT, str) if get_parameter_value(ParameterID.QUEUE_BLOCK_ENABLED, bool) else TextPieceID.QUEUE_INFO_DISABLED,
                unblocks_at=get_parameter_value(ParameterID.QUEUE_UNBLOCK_AT, str) if get_parameter_value(ParameterID.QUEUE_UNBLOCK_ENABLED, bool) else TextPieceID.QUEUE_INFO_DISABLED
            ),
            ephemeral=True
        )

    @app_commands.command(description="Get block/unblock history")
    @requires_permission(PermissionFlagID.ADMIN)
    async def history(self, inter: discord.Interaction) -> None:
        await LogPaginationView(log_filter=LoadedLogFilter(event_type=LoggedEventTypeID.PARAMETER_EDITED)).respond_with_view(inter, True)


async def setup(bot):
    await bot.add_cog(QueueCog(bot))