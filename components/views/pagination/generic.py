from __future__ import annotations

import traceback
import discord
import typing as tp

from abc import ABC, abstractmethod
from services.disc import member_language, respond
from facades.texts import render_text
from util.format import as_code_block
from util.identifiers import TextPieceID


# No pagination persists after the bot's restart either. They are assumed to be single-use views
class GenericPaginationView(ABC, discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=300)

        self.interaction: discord.Interaction | None = None
        self.user: discord.Member | None = None
        self.message: discord.Message | None = None
        self.message_text: str | None = None
        self.offset = 0
        self.limit = 10

    async def shutdown(self) -> None:
        if self.message:
            await self.message.edit(content='-', view=None)
        self.message = None

    async def on_timeout(self) -> None:
        await self.shutdown()

    async def on_error(self, inter: discord.Interaction[discord.Client], error: Exception, item: discord.ui.Item[tp.Any]) -> None:
        error_traceback = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        formatted_traceback = as_code_block(error_traceback, "py")
        await respond(inter, TextPieceID.ERROR_COMPONENT_ERROR, substitutions=dict(error_traceback=formatted_traceback), ephemeral=True)

        await self.shutdown()

    @abstractmethod
    async def get_current_page_blocks(self) -> list[str]:
        ...

    async def respond_with_view(self, inter: discord.Interaction, ephemeral: bool) -> None:
        self.interaction = inter
        self.user = inter.user

        self.prev.disabled = True

        blocks = await self.get_current_page_blocks()

        if blocks:
            self.message_text = "\n".join(blocks)
            if len(blocks) < self.limit:
                self.next.disabled = True
        else:
            self.message_text = render_text(TextPieceID.PAGINATION_NO_ENTRIES, member_language(inter.user, inter.locale).language)
            self.prev.disabled = True
            self.next.disabled = True

        if inter.response.is_done():
            await inter.edit_original_response(content=self.message_text, view=self)
        else:
            await inter.response.send_message(self.message_text, view=self, ephemeral=ephemeral)
        self.message = await inter.original_response()

        if not blocks:
            await self.message.edit(view=None)
            self.message = None

    @discord.ui.button(label="⏴", style=discord.ButtonStyle.gray)
    async def prev(self, inter: discord.Interaction, button: discord.ui.Button[GenericPaginationView]) -> None:
        if self.user.id != inter.user.id:
            return

        if self.offset > 0:
            self.next.disabled = False

        self.offset -= self.limit

        if self.offset < 0:
            self.offset = 0

        blocks = await self.get_current_page_blocks()
        self.message_text = "\n".join(blocks)
        if self.offset == 0:
            note = render_text(TextPieceID.PAGINATION_TOP_REACHED, member_language(inter.user, inter.locale).language)
            self.message_text = f"**{note}**\n" + self.message_text
            button.disabled = True

        await inter.response.edit_message(content=self.message_text, view=self)

    @discord.ui.button(label="⏵", style=discord.ButtonStyle.gray)
    async def next(self, inter: discord.Interaction, button: discord.ui.Button[GenericPaginationView]) -> None:
        if self.user.id != inter.user.id:
            return

        self.offset += self.limit

        blocks = await self.get_current_page_blocks()

        if blocks:
            self.message_text = "\n".join(blocks)
            self.prev.disabled = False
        else:
            self.offset -= self.limit

        if len(blocks) < self.limit:
            note = render_text(TextPieceID.PAGINATION_BOTTOM_REACHED, member_language(inter.user, inter.locale).language)
            self.message_text += f"\n**{note}**"
            button.disabled = True

        await inter.response.edit_message(content=self.message_text, view=self)
