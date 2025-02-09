from discord import Interaction

import facades.texts
from components.modals.common_items import get_reason_text_input, get_review_text_input
from components.modals.generic import GenericModal
from services.disc import respond
from util.datatypes import Language, Opinion
from util.identifiers import TextPieceID


class PreRejectionModal(GenericModal):
    def __init__(self, request_id: int, language: Language) -> None:
        super().__init__(
            title=facades.texts.render_text(TextPieceID.REQUEST_OPINION_MODAL_TITLE, language),
            timeout=None,
            custom_id=f'prm:{request_id}'
        )

        self.add_item(get_review_text_input("prm:rti", language))
        self.add_item(get_reason_text_input("prm:ri", language, False))

    @classmethod
    async def process_submission(cls, interaction: Interaction, custom_id_fields: list[str], text_input_values: dict[str, str]) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        request_id = int(custom_id_fields[0])
        review_text = text_input_values.get("prm:rti")
        reason = text_input_values.get("prm:ri")

        import facades.requests
        await facades.requests.add_opinion(interaction.user, request_id, Opinion.REJECTED, review_text=review_text, reason=reason)
        await respond(interaction, TextPieceID.COMMON_SUCCESS, ephemeral=True)