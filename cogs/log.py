import json
from datetime import datetime

import discord
import yaml

from discord import app_commands
from discord.ext import commands

from components.views.confirmation import ConfirmationView
from components.views.pagination.log import LogPaginationView
from facades.eventlog import (
    AlreadyExistsError, clear_current_filter, clear_filter_custom_fields, delete_filter, find_filters_by_prefix, get_current_filter, get_filter, list_filters, NotExistsError, save_filter, select_filter, update_filter_custom_field,
    update_filter_event_type,
    update_filter_user,
)
from services.disc import CheckDeferringBehaviour, requires_permission, respond
from util.datatypes import CommandChoiceOption
from util.exceptions import AlreadySatisfiesError
from util.format import as_code, list_values
from util.identifiers import LoggedEventTypeID, PermissionFlagID, TextPieceID
from dateutil.parser import parse as parse_datetime, ParserError


class LogCog(commands.GroupCog, name="log", description="Commands for querying logs"):
    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_RESTRICT_USER.as_locale_str())
    @app_commands.describe(user=TextPieceID.COMMAND_OPTION_LOG_RESTRICT_USER_USER.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def restrict_user(self, inter: discord.Interaction, user: discord.Member):
        try:
            update_filter_user(inter.user, user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_RESTRICT_TYPE.as_locale_str())
    @app_commands.describe(event_type=TextPieceID.COMMAND_OPTION_LOG_RESTRICT_TYPE_EVENT_TYPE.as_locale_str())
    @app_commands.choices(event_type=CommandChoiceOption.from_enum(LoggedEventTypeID))
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def restrict_type(self, inter: discord.Interaction, event_type: LoggedEventTypeID):
        try:
            update_filter_event_type(inter.user, event_type)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_RESTRICT_CUSTOM_FIELD.as_locale_str())
    @app_commands.describe(
        key=TextPieceID.COMMAND_OPTION_LOG_RESTRICT_CUSTOM_FIELD_KEY.as_locale_str(),
        value=TextPieceID.COMMAND_OPTION_LOG_RESTRICT_CUSTOM_FIELD_VALUE.as_locale_str()
    )
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def restrict_custom_field(self, inter: discord.Interaction, key: str, value: str):
        try:
            update_filter_custom_field(inter.user, key, value)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_UNRESTRICT_USER.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def unrestrict_user(self, inter: discord.Interaction):
        try:
            update_filter_user(inter.user, None)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_UNRESTRICT_TYPE.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def unrestrict_type(self, inter: discord.Interaction):
        try:
            update_filter_event_type(inter.user, None)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_UNRESTRICT_CUSTOM_FIELD.as_locale_str())
    @app_commands.describe(key=TextPieceID.COMMAND_OPTION_LOG_UNRESTRICT_CUSTOM_FIELD_KEY.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def unrestrict_custom_field(self, inter: discord.Interaction, key: str):
        try:
            update_filter_custom_field(inter.user, key, None)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_CLEAR_CUSTOM_FIELD_RESTRICTIONS.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def clear_custom_field_restrictions(self, inter: discord.Interaction):
        try:
            clear_filter_custom_fields(inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_CLEAR_FILTER.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def clear_filter(self, inter: discord.Interaction):
        try:
            clear_current_filter(inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_DESCRIBE_FILTER.as_locale_str())
    @app_commands.describe(name=TextPieceID.COMMAND_OPTION_LOG_DESCRIBE_FILTER_NAME.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
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
            await respond(inter, yaml.safe_dump(filter_dict, sort_keys=False, allow_unicode=True), ephemeral=True)
        elif not log_filter and name is not None:
            await respond(inter, TextPieceID.ERROR_FILTER_DOESNT_EXIST, substitutions=dict(name=as_code(name)), ephemeral=True)
        else:
            await respond(inter, TextPieceID.LOG_EMPTY_FILTER, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_VIEW.as_locale_str())
    @app_commands.describe(timestamp=TextPieceID.COMMAND_OPTION_LOG_VIEW_TIMESTAMP.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def view(self, inter: discord.Interaction, timestamp: str | None = None):
        parsed_timestamp: datetime | None = None

        if timestamp:
            try:
                parsed_timestamp = parse_datetime(timestamp)
            except ParserError:
                await respond(inter, TextPieceID.ERROR_CANT_PARSE_TIMESTAMP, substitutions=dict(raw=timestamp), ephemeral=True)
                return

        await LogPaginationView(parsed_timestamp).respond_with_view(inter, True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_LIST_FILTERS.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def list_filters(self, inter: discord.Interaction):
        filters = list_filters()
        if filters:
            await respond(inter, list_values(list_filters()), ephemeral=True)
        else:
            await respond(inter, TextPieceID.LOG_NO_FILTERS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_SELECT_FILTER.as_locale_str())
    @app_commands.describe(name=TextPieceID.COMMAND_OPTION_LOG_SELECT_FILTER_NAME.as_locale_str())
    @requires_permission(PermissionFlagID.LOG_VIEWER, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def select_filter(self, inter: discord.Interaction, name: str):
        try:
            select_filter(inter.user, name)
        except NotExistsError:
            await respond(inter, TextPieceID.ERROR_FILTER_DOESNT_EXIST, substitutions=dict(name=name), ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_SAVE_FILTER.as_locale_str())
    @app_commands.describe(name=TextPieceID.COMMAND_OPTION_LOG_SAVE_FILTER_NAME.as_locale_str())
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
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

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_LOG_DELETE_FILTER.as_locale_str())
    @app_commands.describe(name=TextPieceID.COMMAND_OPTION_LOG_DELETE_FILTER_NAME.as_locale_str())
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
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
    async def name_autocomplete(self, _: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=option, value=option)
            for option in find_filters_by_prefix(current)[:25]
            if option.lower().startswith(current.lower())
        ]


async def setup(bot):
    await bot.add_cog(LogCog(bot))