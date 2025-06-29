from __future__ import annotations

import traceback
import typing
from collections.abc import Coroutine

import discord
from discord import NotFound

from services.disc import member_language, respond, safe_defer
from facades.texts import render_text
from util.format import as_code_block
from util.identifiers import TextPieceID

import typing as tp


# This view won't persist after restart. It is assumed to be short-lived due to its purpose
class ConfirmationView(discord.ui.View):
    user: discord.Member
    message: discord.Message | None = None
    callback: tp.Callable[[discord.Interaction], tp.Any]

    def __init__(self) -> None:
        super().__init__(timeout=300)

    async def destroy_self(self) -> None:
        if self.message:
            await self.message.edit(content="-", view=None)
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
        callback: tp.Callable[[discord.Interaction], tp.Any],
        question_text: TextPieceID,
        question_substitutions: dict[str, str] | None = None
    ) -> None:
        self.user = inter.user
        self.callback = callback

        message_text = render_text(question_text, member_language(inter.user, inter.locale).language, question_substitutions)
        try:
            await inter.response.send_message(message_text, view=self, ephemeral=ephemeral)
        except NotFound:
            pass
        else:
            self.message = await inter.original_response()

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.red)
    async def yes(self, inter: discord.Interaction, _) -> None:
        if self.user.id != inter.user.id:
            return

        returned = self.callback(inter)
        if isinstance(returned, Coroutine):
            await returned

        if not inter.response.is_done():
            success_text = render_text(TextPieceID.COMMON_SUCCESS, member_language(inter.user, inter.locale).language)
            try:
                await inter.response.edit_message(content=success_text, view=None)
            except NotFound:
                pass
        else:
            await self.destroy_self()

    @discord.ui.button(label="No", style=discord.ButtonStyle.gray)
    async def no(self, inter: discord.Interaction, _) -> None:
        if self.user.id != inter.user.id:
            return

        await self.destroy_self()
        await safe_defer(inter, ephemeral=False, thinking=False)