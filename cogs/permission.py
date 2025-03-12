import discord

from discord import app_commands
from discord.ext import commands

from config.permission_flags import enlist
from config.stage_parameters import get_value as get_stage_parameter_value
from facades.permissions import bind, unbind, clear, list_bound_roles, has_permission, is_permission_assigned
from services.disc import CheckDeferringBehaviour, requires_permission, respond, respond_forbidden
from util.datatypes import CommandChoiceOption
from util.exceptions import AlreadySatisfiesError
from util.format import as_code, as_role, list_described_values
from util.identifiers import PermissionFlagID, StageParameterID, TextPieceID


class PermissionCog(commands.GroupCog, name="permission", description="Utilities for working with permissions"):
    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_PERMISSION_LIST_FLAGS.as_locale_str())
    async def list_flags(self, inter: discord.Interaction) -> None:
        await respond(inter, list_described_values(enlist()), ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_PERMISSION_BIND.as_locale_str())
    @app_commands.describe(
        permission=TextPieceID.COMMAND_OPTION_PERMISSION_BIND_PERMISSION.as_locale_str(),
        role=TextPieceID.COMMAND_OPTION_PERMISSION_BIND_ROLE.as_locale_str()
    )
    @app_commands.choices(permission=CommandChoiceOption.from_enum(PermissionFlagID))
    async def bind(self, inter: discord.Interaction, permission: PermissionFlagID, role: discord.Role):
        # Because, to obtain an admin permission, KazVixX needs to bind it to a role first
        if is_permission_assigned(PermissionFlagID.ADMIN) and not has_permission(inter.user, PermissionFlagID.ADMIN) or inter.user.id != get_stage_parameter_value(StageParameterID.ADMIN_USER_ID):
            await respond_forbidden(inter)
            return

        try:
            await bind(role, permission, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_PERMISSION_UNBIND.as_locale_str())
    @app_commands.describe(
        permission=TextPieceID.COMMAND_OPTION_PERMISSION_UNBIND_PERMISSION.as_locale_str(),
        role=TextPieceID.COMMAND_OPTION_PERMISSION_UNBIND_ROLE.as_locale_str()
    )
    @app_commands.choices(permission=CommandChoiceOption.from_enum(PermissionFlagID))
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def unbind(self, inter: discord.Interaction, permission: PermissionFlagID, role: discord.Role):
        try:
            await unbind(role, permission, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
            return

        if permission == PermissionFlagID.ADMIN and not has_permission(inter.user, PermissionFlagID.ADMIN):
            await bind(role, permission)
            await respond(inter, TextPieceID.ERROR_CANT_REMOVE_ADMIN_PERMISSION, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_PERMISSION_CLEAR.as_locale_str())
    @app_commands.describe(role=TextPieceID.COMMAND_OPTION_PERMISSION_CLEAR_ROLE.as_locale_str())
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def clear(self, inter: discord.Interaction, role: discord.Role):
        try:
            await clear(role, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_PERMISSION_LIST_ROLES.as_locale_str())
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def list_roles(self, inter: discord.Interaction):
        lines = []

        for role_id, permissions in list_bound_roles().items():
            enlisted_permissions = ', '.join(map(lambda perm: as_code(perm.value), permissions))
            lines.append(f'{as_role(role_id)}: {enlisted_permissions}')

        await respond(inter, lines or TextPieceID.PERMISSION_NO_ASSIGNED_ROLES, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_PERMISSION_DESCRIBE_MEMBER.as_locale_str())
    @app_commands.describe(member=TextPieceID.COMMAND_OPTION_PERMISSION_DESCRIBE_MEMBER_MEMBER.as_locale_str())
    @requires_permission(PermissionFlagID.ADMIN, CheckDeferringBehaviour.DEFER_EPHEMERAL)
    async def describe_member(self, inter: discord.Interaction, member: discord.Member):
        lines = []

        for role_id, permissions in list_bound_roles(member).items():
            enlisted_permissions = ', '.join(map(lambda perm: as_code(perm.value), permissions))
            lines.append(f'За счет {as_role(role_id)}: {enlisted_permissions}')

        if lines:
            await respond(inter, lines, ephemeral=True)
        else:
            await respond(inter, TextPieceID.PERMISSION_MEMBER_HAS_NO_PERMISSIONS, substitutions=dict(member_mention=member.mention), ephemeral=True)


async def setup(bot):
    await bot.add_cog(PermissionCog(bot))