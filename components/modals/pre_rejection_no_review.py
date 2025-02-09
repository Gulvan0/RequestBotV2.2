from discord import Interaction

import facades.texts
from components.modals.common_items import get_reason_text_input
from components.modals.generic import GenericModal
from services.disc import respond
from util.datatypes import Language, Opinion
from util.identifiers import TextPieceID


class PreRejectionNoReviewModal(GenericModal):
    def __init__(self, request_id: int, language: Language) -> None:
        super().__init__(
            title=facades.texts.render_text(TextPieceID.REQUEST_OPINION_MODAL_TITLE, language),
            timeout=None,
            custom_id=f'prnrm:{request_id}'
        )

        self.add_item(get_reason_text_input("prnrm:ri", language, True))

    @classmethod
    async def process_submission(cls, interaction: Interaction, custom_id_fields: list[str], text_input_values: dict[str, str]) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        request_id = int(custom_id_fields[0])
        reason = text_input_values.get("prnrm:ri")

        import facades.requests
        await facades.requests.add_opinion(interaction.user, request_id, Opinion.REJECTED, reason=reason)
        await respond(interaction, TextPieceID.COMMON_SUCCESS, ephemeral=True)