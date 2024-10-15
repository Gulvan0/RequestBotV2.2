import discord

from discord import app_commands
from discord.ext import commands

from config.texts import enlist
from services.disc import requires_permission, respond
from texts import explain, reset_template, update_template
from util.datatypes import CommandChoiceOption, Language
from util.exceptions import AlreadySatisfiesError
from util.format import as_code, as_code_block, list_described_values
from util.identifiers import PermissionFlagID, TextPieceID


class TextCog(commands.GroupCog, name="text", description="Utilities for working with message templates"):
    @app_commands.command(description="View details about a message template")
    @app_commands.describe(template_name="Template name (aka. text piece ID)")
    @app_commands.choices(template_name=CommandChoiceOption.from_enum(TextPieceID))
    @requires_permission(PermissionFlagID.ADMIN)
    async def describe(self, inter: discord.Interaction, template_name: TextPieceID) -> None:
        text_piece_details = explain(template_name)

        lines = [
            f"**Template `{template_name.value}`**",
            f"_{text_piece_details.description}_",
            "",
            "**Параметры:**",
        ]

        if text_piece_details.parameter_descriptions:
            for param_name, param_description in text_piece_details.parameter_descriptions.items():
                lines.append(f"`{param_name}` - {param_description}")
        else:
            lines.append("Данный шаблон не принимает параметров")

        lines.append("")

        for lang, current_template in text_piece_details.current_templates.items():
            lines.append(f"**Текущий шаблон ({as_code(lang)}):**")
            lines.append(as_code_block(current_template))

        await respond(inter, lines, ephemeral=True)

    @app_commands.command(description="Edit a message template")
    @app_commands.describe(
        template_name="Template name (aka. text piece ID)",
        language="Template language",
        new_value="Updated template text"
    )
    @app_commands.choices(
        template_name=CommandChoiceOption.from_enum(TextPieceID),
        language=CommandChoiceOption.from_str_enum(Language)
    )
    @requires_permission(PermissionFlagID.ADMIN)
    async def edit(self, inter: discord.Interaction, template_name: TextPieceID, language: Language, new_value: str) -> None:
        try:
            update_template(template_name, language, new_value, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="Reset a message template to its default value")
    @app_commands.describe(
        template_name="Template name (aka. text piece ID)",
        language="Template language"
    )
    @app_commands.choices(
        template_name=CommandChoiceOption.from_enum(TextPieceID),
        language=CommandChoiceOption.from_str_enum(Language)
    )
    @requires_permission(PermissionFlagID.ADMIN)
    async def reset(self, inter: discord.Interaction, template_name: TextPieceID, language: Language) -> None:
        try:
            reset_template(template_name, language, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description="List all available message templates")
    @requires_permission(PermissionFlagID.ADMIN)
    async def list(self, inter: discord.Interaction) -> None:
        await respond(inter, list_described_values(enlist()), ephemeral=True)


async def setup(bot):
    await bot.add_cog(TextCog(bot))