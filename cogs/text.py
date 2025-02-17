import discord

from discord import app_commands
from discord.ext import commands

from components.views.pagination.list import ListPaginationView
from config.texts import enlist
from services.disc import requires_permission, respond
from facades.texts import explain, reset_template, update_template
from util.datatypes import CommandChoiceOption, Language
from util.exceptions import AlreadySatisfiesError
from util.format import as_code, as_code_block, list_described_values
from util.identifiers import PermissionFlagID, TextPieceID


class TextCog(commands.GroupCog, name="text", description="Utilities for working with message templates"):
    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_TEXT_DESCRIBE.as_locale_str())
    @app_commands.describe(template_name=TextPieceID.COMMAND_OPTION_TEXT_DESCRIBE_TEMPLATE_NAME.as_locale_str())
    @app_commands.choices(template_name=[])
    @app_commands.autocomplete(template_name=CommandChoiceOption.autocomplete_from_enum(TextPieceID))
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

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_TEXT_EDIT.as_locale_str())
    @app_commands.describe(
        template_name=TextPieceID.COMMAND_OPTION_TEXT_EDIT_TEMPLATE_NAME.as_locale_str(),
        language=TextPieceID.COMMAND_OPTION_TEXT_EDIT_LANGUAGE.as_locale_str(),
        new_value=TextPieceID.COMMAND_OPTION_TEXT_EDIT_NEW_VALUE.as_locale_str()
    )
    @app_commands.autocomplete(template_name=CommandChoiceOption.autocomplete_from_enum(TextPieceID))
    @app_commands.choices(language=CommandChoiceOption.from_str_enum(Language), template_name=[])
    @requires_permission(PermissionFlagID.ADMIN)
    async def edit(self, inter: discord.Interaction, template_name: TextPieceID, language: Language, new_value: str) -> None:
        try:
            await update_template(template_name, language, new_value, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_TEXT_RESET.as_locale_str())
    @app_commands.describe(
        template_name=TextPieceID.COMMAND_OPTION_TEXT_RESET_TEMPLATE_NAME.as_locale_str(),
        language=TextPieceID.COMMAND_OPTION_TEXT_RESET_LANGUAGE.as_locale_str()
    )
    @app_commands.autocomplete(template_name=CommandChoiceOption.autocomplete_from_enum(TextPieceID))
    @app_commands.choices(language=CommandChoiceOption.from_str_enum(Language), template_name=[])
    @requires_permission(PermissionFlagID.ADMIN)
    async def reset(self, inter: discord.Interaction, template_name: TextPieceID, language: Language) -> None:
        try:
            await reset_template(template_name, language, inter.user)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    @app_commands.command(description=TextPieceID.COMMAND_DESCRIPTION_TEXT_LIST.as_locale_str())
    @requires_permission(PermissionFlagID.ADMIN)
    async def list(self, inter: discord.Interaction) -> None:
        await ListPaginationView(list_described_values(enlist())).respond_with_view(inter, ephemeral=True)


async def setup(bot):
    await bot.add_cog(TextCog(bot))