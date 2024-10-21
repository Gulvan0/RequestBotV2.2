from __future__ import annotations

import traceback
import typing

import discord

from services.disc import member_language, respond
from texts import render_text
from util.format import as_code_block
from util.identifiers import TextPieceID

import typing as tp


class ConfirmationView(discord.ui.View):
    user: discord.Member
    message: discord.Message | None = None
    callback: tp.Callable[[], tp.Any]

    def __init__(self) -> None:
        super().__init__(timeout=300)

    async def destroy_self(self) -> None:
        await self.message.edit(content=None, view=None)
        self.message = None

    async def on_timeout(self) -> None:
        await self.destroy_self()

    async def on_error(self, inter: discord.Interaction[discord.Client], error: Exception, item: discord.ui.Item[typing.Any]) -> None:
        error_traceback = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        formatted_traceback = as_code_block(error_traceback, "py")
        await respond(inter, TextPieceID.ERROR_COMPONENT_ERROR, substitutions=dict(error_traceback=formatted_traceback), ephemeral=True)

        await self.destroy_self()

    async def respond_with_view(
        self,
        inter: discord.Interaction,
        ephemeral: bool,
        callback: tp.Callable[[], tp.Any],
        question_text: TextPieceID,
        question_substitutions: dict[str, str] | None = None
    ) -> None:
        self.callback = callback

        message_text = render_text(question_text, member_language(inter.user, inter.locale).language, question_substitutions)
        await inter.response.send_message(message_text, view=self, ephemeral=ephemeral)
        self.message = await inter.original_response()

    @discord.ui.button(emoji=":white_check_mark:", style=discord.ButtonStyle.red)
    async def yes(self, inter: discord.Interaction, _) -> None:
        if self.user.id != inter.user.id:
            return

        self.callback()

        success_text = render_text(TextPieceID.COMMON_SUCCESS, member_language(inter.user, inter.locale).language)
        await inter.response.edit_message(content=success_text, view=None)

    @discord.ui.button(label=":no_entry:", style=discord.ButtonStyle.gray)
    async def no(self, inter: discord.Interaction, _) -> None:
        if self.user.id != inter.user.id:
            return

        await self.destroy_self()
        await inter.response.defer()
