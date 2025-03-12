import discord

from discord import app_commands
from discord.ext import commands

from config.parameters import get_displayed_type, RestrictionNotSatisfiedError
from config.parameters import enlist
from services.disc import CheckDeferringBehaviour, requires_permission, respond
from facades.parameters import explain, update_value, reset_value
from util.datatypes import CommandChoiceOption
from util.exceptions import AlreadySatisfiesError
from util.format import as_code, list_described_values
from util.identifiers import PermissionFlagID, TextPieceID, ParameterID


class ParameterCog(commands.GroupCog, name="parameter", description="Utilities for working with global bot parameters"):
    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_PARAMETER_DESCRIBE.as_locale_str())
    @app_commands.describe(parameter=TextPieceID.COMMAND_OPTION_PARAMETER_DESCRIBE_PARAMETER.as_locale_str())
    @app_commands.choices(parameter=CommandChoiceOption.from_enum(ParameterID))
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def describe(self, inter: discord.Interaction, parameter: ParameterID) -> None:
        parameter_details = explain(parameter)

        lines = [
            f"**Parameter `{parameter.value}`**",
            f"_{parameter_details.description}_",
            "",
            f"**Тип:** {parameter_details.displayed_type}",
            f"**Значение по умолчанию:** {as_code(parameter_details.default_value)}",
            f"**Текущее значение:** {as_code(parameter_details.current_value)}",
        ]

        await respond(inter, lines, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_PARAMETER_SET.as_locale_str())
    @app_commands.describe(
        parameter=TextPieceID.COMMAND_OPTION_PARAMETER_SET_PARAMETER.as_locale_str(),
        new_value=TextPieceID.COMMAND_OPTION_PARAMETER_SET_NEW_VALUE.as_locale_str()
    )
    @app_commands.choices(parameter=CommandChoiceOption.from_enum(ParameterID))
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def set(self, inter: discord.Interaction, parameter: ParameterID, new_value: str) -> None:
        try:
            await update_value(parameter, new_value, inter.user)
        except RestrictionNotSatisfiedError:
            await respond(
                inter,
                TextPieceID.ERROR_WRONG_PARAMETER_VALUE_TYPE,
                substitutions=dict(
                    value=as_code(new_value),
                    param_type=as_code(get_displayed_type(parameter))
                ),
                ephemeral=True
            )
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_PARAMETER_RESET.as_locale_str())
    @app_commands.describe(parameter=TextPieceID.COMMAND_OPTION_PARAMETER_RESET_PARAMETER.as_locale_str())
    @app_commands.choices(parameter=CommandChoiceOption.from_enum(ParameterID))
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def reset(self, inter: discord.Interaction, parameter: ParameterID) -> None:
        try:
            await reset_value(parameter, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_PARAMETER_LIST.as_locale_str())
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def list(self, inter: discord.Interaction) -> None:
        await respond(inter, list_described_values(enlist()), ephemeral=True)


async def setup(bot):
    await bot.add_cog(ParameterCog(bot))