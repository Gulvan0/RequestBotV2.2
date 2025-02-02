from __future__ import annotations

import traceback

from discord import Interaction, TextStyle
from discord.ui import Modal, TextInput

import facades.texts  # Avoiding circular imports
import facades.requests
from facades.requests import InvalidYtLinkException
from services.disc import respond, send_developers
from util.datatypes import Language
from util.identifiers import TextPieceID


class RequestSubmissionModal(Modal):
    def __init__(self, request_id: int = 0, language: Language = Language.EN) -> None:
        super().__init__(
            title=facades.texts.render_text(TextPieceID.REQUEST_MODAL_TITLE, language),
            timeout=None,
            custom_id=f'rsm:{request_id}'
        )

        self.yt_link_input = TextInput(
            label=facades.texts.render_text(TextPieceID.REQUEST_MODAL_YT_LINK_LABEL, language),
            placeholder="https://www.youtube.com/watch?v=...",
            required=True,
            min_length=8,
            max_length=100,
            style=TextStyle.short,
            custom_id="rsm:yli"
        )
        self.additional_comment_input = TextInput(
            label=facades.texts.render_text(TextPieceID.REQUEST_MODAL_ADDITIONAL_COMMENT_LABEL, language),
            placeholder=facades.texts.render_text(TextPieceID.REQUEST_MODAL_ADDITIONAL_COMMENT_PLACEHOLDER, language),
            required=False,
            min_length=5,
            max_length=400,
            style=TextStyle.long,
            custom_id="rsm:aci"
        )

        self.add_item(self.yt_link_input)
        self.add_item(self.additional_comment_input)


    @classmethod
    async def handle_interaction(cls, interaction: Interaction) -> None:
        request_id = int(interaction.data.get("custom_id").split(":", 1)[1])
        yt_link = ''
        additional_comment = None
        for component_row in interaction.data.get("components", []):
            for comp in component_row.get("components", []):
                match comp.get("custom_id"):
                    case 'rsm:yli':
                        yt_link = comp.get("value")
                    case 'rsm:aci':
                        additional_comment = comp.get("value")

        try:
            await facades.requests.complete_request(request_id, yt_link, additional_comment, interaction.user)
        except InvalidYtLinkException:
            await respond(interaction, TextPieceID.REQUEST_MODAL_INVALID_YT_LINK, ephemeral=True)
        else:
            await respond(interaction, TextPieceID.COMMON_SUCCESS, ephemeral=True)


    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        error_details = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        await send_developers(error_details, "py")
        self.stop()