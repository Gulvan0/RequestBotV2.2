import json

import discord
import yaml

from discord import app_commands
from discord.ext import commands

from components.views.confirmation import ConfirmationView
from components.views.log_pagination import LogPaginationView
from facades.eventlog import (
    AlreadyExistsError, clear_current_filter, clear_filter_custom_fields, delete_filter, find_filters_by_prefix, get_current_filter, get_filter, list_filters, NotExistsError, save_filter, select_filter, update_filter_custom_field,
    update_filter_event_type,
    update_filter_user,
)
from services.disc import requires_permission, respond
from util.datatypes import CommandChoiceOption
from util.exceptions import AlreadySatisfiesError
from util.format import as_code, list_values
from util.identifiers import LoggedEventTypeID, PermissionFlagID, TextPieceID
from dateutil.parser import parse as parse_datetime, ParserError


class LogCog(commands.GroupCog, name="log", description="Commands for querying logs"):
    @app_commands.command(description="Only query actions performed by a provided user. Successive calls change the selected user")
    @app_commands.describe(user="Server member. Only his/her actions will be queried")
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def restrict_user(self, inter: discord.Interaction, user: discord.Member):
        try:
            update_filter_user(inter.user, user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Only query events of a provided type")
    @app_commands.describe(event_type="Only the events with this type will be queried. Successive calls change the selected type")
    @app_commands.choices(event_type=CommandChoiceOption.from_enum(LoggedEventTypeID))
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def restrict_type(self, inter: discord.Interaction, event_type: LoggedEventTypeID):
        try:
            update_filter_event_type(inter.user, event_type)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Only query events with a provided value of a provided custom field")
    @app_commands.describe(
        key="A key of a custom field to be restricted to a certain value",
        value="A value to restrict a certain custom field to. Only the events having this value of a provided custom field will be queried"
    )
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def restrict_custom_field(self, inter: discord.Interaction, key: str, value: str):
        try:
            update_filter_custom_field(inter.user, key, value)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Remove a user restriction in a current log filter")
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def unrestrict_user(self, inter: discord.Interaction):
        try:
            update_filter_user(inter.user, None)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Remove an event type restriction in a current log filter")
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def unrestrict_type(self, inter: discord.Interaction):
        try:
            update_filter_event_type(inter.user, None)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Remove one custom field value restriction in a current log filter")
    @app_commands.describe(key="A key of a custom field to remove a restriction for")
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def unrestrict_custom_field(self, inter: discord.Interaction, key: str):
        try:
            update_filter_custom_field(inter.user, key, None)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Remove all custom field value restrictions in a current log filter")
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def clear_custom_field_restrictions(self, inter: discord.Interaction):
        try:
            clear_filter_custom_fields(inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Remove all restrictions in a current log filter")
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def clear_filter(self, inter: discord.Interaction):
        try:
            clear_current_filter(inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Describes the filter")
    @app_commands.describe(name="Name of a filter to describe. Omit to describe the current filter")
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def describe_filter(self, inter: discord.Interaction, name: str | None = None):
        log_filter = get_filter(name) if name else get_current_filter(inter.user)

        if log_filter and not log_filter.is_empty():
            filter_dict = {}

            if log_filter.user_id:
                user = await inter.client.fetch_user(log_filter.user_id)
                filter_dict["user"] = user.mention

            if log_filter.event_type:
                filter_dict["event"] = as_code(log_filter.event_type.name)

            filter_dict.update(json.loads(log_filter.custom_data_values))

            # Here we don't format it as code block to preserve individual formats of values
            await respond(inter, yaml.safe_dump(filter_dict, sort_keys=False), ephemeral=True)
        elif not log_filter and name is not None:
            await respond(inter, TextPieceID.ERROR_FILTER_DOESNT_EXIST, substitutions=dict(name=as_code(name)), ephemeral=True)
        else:
            await respond(inter, TextPieceID.LOG_EMPTY_FILTER, ephemeral=True)


    @app_commands.command(description="Display logs matching the currently selected filter")
    @app_commands.describe(timestamp="An event timestamp to jump to. Omit to start from the beginning")
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def view(self, inter: discord.Interaction, timestamp: str | None = None):
        parsed_timestamp = None
        if timestamp:
            try:
                parsed_timestamp = parse_datetime(timestamp)
            except ParserError:
                await respond(inter, TextPieceID.ERROR_CANT_PARSE_TIMESTAMP, substitutions=dict(raw=timestamp), ephemeral=True)
                return

        await LogPaginationView().respond_with_view(inter, True, parsed_timestamp)

    @app_commands.command(description="Lists all the available filters")
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def list_filters(self, inter: discord.Interaction):
        filters = list_filters()
        if filters:
            await respond(inter, list_values(list_filters()), ephemeral=True)
        else:
            await respond(inter, TextPieceID.LOG_NO_FILTERS, ephemeral=True)

    @app_commands.command(description="Select a saved filter")
    @app_commands.describe(name="Name of a filter to select")
    @requires_permission(PermissionFlagID.LOG_VIEWER)
    async def select_filter(self, inter: discord.Interaction, name: str):
        try:
            select_filter(inter.user, name)
        except NotExistsError:
            await respond(inter, TextPieceID.ERROR_FILTER_DOESNT_EXIST, substitutions=dict(name=name), ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Save a currently selected filter. This allows it to be reused later")
    @app_commands.describe(name="Name under which the current filter will be saved")
    @requires_permission(PermissionFlagID.ADMIN)
    async def save_filter(self, inter: discord.Interaction, name: str):
        log_filter = get_current_filter(inter.user)

        if not log_filter or log_filter.is_empty():
            await respond(inter, TextPieceID.LOG_EMPTY_FILTER_WONT_BE_SAVED, ephemeral=True)
            return

        try:
            save_filter(name, log_filter)
        except AlreadyExistsError:
            def on_confirmed(_) -> None:
                save_filter(name, log_filter, force=True)
            await ConfirmationView().respond_with_view(inter, True, on_confirmed, TextPieceID.CONFIRMATION_OVERRIDE_FILTER, dict(name=name))
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Delete a certain filter")
    @app_commands.describe(name="Name of a filter to be deleted")
    @requires_permission(PermissionFlagID.ADMIN)
    async def delete_filter(self, inter: discord.Interaction, name: str):
        async def on_confirmed(following_inter: discord.Interaction) -> None:
            try:
                delete_filter(name)
            except AlreadySatisfiesError:
                await respond(following_inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
            else:
                await respond(following_inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)
        await ConfirmationView().respond_with_view(inter, True, on_confirmed, TextPieceID.CONFIRMATION_DELETE_FILTER, dict(name=name))

    @select_filter.autocomplete("name")
    @delete_filter.autocomplete("name")
    async def color_autocomplete(self, inter: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=option, value=option)
            for option in find_filters_by_prefix(current)[:25]
            if option.lower().startswith(current.lower())
        ]


async def setup(bot):
    await bot.add_cog(LogCog(bot))