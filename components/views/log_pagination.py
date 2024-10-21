from __future__ import annotations

import json
import traceback
import typing
from datetime import datetime

import discord
import yaml

from database.models import LoggedEvent, StoredLogFilter
from eventlog import get_current_filter, get_entries, get_offset_at_datetime
from services.disc import member_language, respond
from texts import render_text
from util.format import as_code_block, as_user
from util.identifiers import TextPieceID


def _stringify_logged_events(inter: discord.Interaction, events: list[LoggedEvent]) -> str:
    yaml_events = []
    for event in events:
        event_info = dict(
            id=event.id,
            event=event.event_type.name,
            user=as_user(event.user_id) if event.user_id else inter.client.user.mention,
            timestamp=event.timestamp.isoformat()
        )
        event_info.update(json.loads(event.custom_data))
        yaml_events.append(yaml.safe_dump(event_info))
    code_text = "\n---\n".join(yaml_events)
    return as_code_block(code_text, "yaml")


class LogPaginationView(discord.ui.View):
    user: discord.Member
    log_filter: StoredLogFilter
    message: discord.Message | None = None
    message_text: str | None = None
    offset = 0
    limit = 5

    def __init__(self) -> None:
        super().__init__(timeout=300)

    async def on_timeout(self) -> None:
        await self.message.edit(content=None, view=None)
        self.message = None

    async def on_error(self, inter: discord.Interaction[discord.Client], error: Exception, item: discord.ui.Item[typing.Any]) -> None:
        error_traceback = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        formatted_traceback = as_code_block(error_traceback, "py")
        await respond(inter, TextPieceID.ERROR_COMPONENT_ERROR, substitutions=dict(error_traceback=formatted_traceback), ephemeral=True)

        if self.message:
            await self.message.edit(content=None, view=None)
            self.message = None

    def get_current_page_entries(self) -> list[LoggedEvent]:
        return get_entries(self.limit, self.offset, self.log_filter)

    async def respond_with_view(self, inter: discord.Interaction, ephemeral: bool, start_datetime: datetime | None = None) -> None:
        self.user = inter.user
        self.log_filter = get_current_filter(inter.user)

        if start_datetime:
            self.offset = get_offset_at_datetime(start_datetime, self.log_filter)

        if self.offset == 0:
            self.prev.disabled = True

        entries = self.get_current_page_entries()

        # Processing the case when the datetime exceeds the timestamp of the last matching event
        if not entries and start_datetime and self.offset > 0:
            self.offset = max(self.offset - self.limit, 0)
            entries = self.get_current_page_entries()

        if entries:
            self.message_text = _stringify_logged_events(inter, entries)
        else:
            self.message_text = render_text(TextPieceID.LOG_NO_ENTRIES, member_language(inter.user, inter.locale).language)
            self.prev.disabled = True
            self.next.disabled = True

        await inter.response.send_message(self.message_text, view=self, ephemeral=ephemeral)
        self.message = await inter.original_response()

    @discord.ui.button(label="⏴", style=discord.ButtonStyle.gray)
    async def prev(self, inter: discord.Interaction, button: discord.ui.Button[LogPaginationView]) -> None:
        if self.user.id != inter.user.id:
            return

        self.offset -= self.limit

        if self.offset < 0:
            self.offset = 0

        entries = self.get_current_page_entries()
        self.message_text = _stringify_logged_events(inter, entries)
        if self.offset == 0:
            note = render_text(TextPieceID.LOG_TOP_REACHED, member_language(inter.user, inter.locale).language)
            self.message_text = f"**{note}**\n" + self.message_text
            button.disabled = True

        await inter.response.edit_message(content=self.message_text, view=self)

    @discord.ui.button(label="⏵", style=discord.ButtonStyle.gray)
    async def next(self, inter: discord.Interaction, button: discord.ui.Button[LogPaginationView]) -> None:
        if self.user.id != inter.user.id:
            return

        self.offset += self.limit

        entries = get_entries(self.limit, self.offset, self.log_filter)
        if entries:
            self.message_text = _stringify_logged_events(inter, entries)
        else:
            note = render_text(TextPieceID.LOG_BOTTOM_REACHED, member_language(inter.user, inter.locale).language)
            self.message_text += f"\n**{note}**"
            button.disabled = True

        await inter.response.edit_message(content=self.message_text, view=self)
