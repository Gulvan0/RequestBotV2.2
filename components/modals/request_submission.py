from discord import Interaction, TextStyle
from discord.ui import TextInput

import facades.texts
import facades.requests
import facades.cooldowns
from components.modals.generic import GenericModal
from facades.permissions import has_permission
from facades.requests import InvalidYtLinkException
from services.disc import respond
from util.datatypes import CooldownEntity, Language
from util.identifiers import PermissionFlagID, TextPieceID


class RequestSubmissionModal(GenericModal):
    def __init__(self, request_id: int, language: Language) -> None:
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
    async def process_submission(cls, interaction: Interaction, custom_id_fields: list[str], text_input_values: dict[str, str]) -> None:
        request_id = int(custom_id_fields[0])
        yt_link = text_input_values.get("rsm:yli") or ''
        additional_comment = text_input_values.get("rsm:aci")

        try:
            await facades.requests.complete_request(request_id, yt_link, additional_comment, interaction.user)
        except InvalidYtLinkException:
            await respond(interaction, TextPieceID.REQUEST_MODAL_INVALID_YT_LINK, ephemeral=True)
        else:
            if not has_permission(interaction.user, PermissionFlagID.NO_REQUEST_COOLDOWN):
                await facades.cooldowns.cast_after_request(CooldownEntity.USER, interaction.user.id, request_id)
            await respond(interaction, TextPieceID.REQUEST_COMMAND_SUBMITTED, ephemeral=True)
