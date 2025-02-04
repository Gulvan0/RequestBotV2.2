from discord import Interaction

import facades.texts  # Avoiding circular imports
from components.modals.common_items import get_review_text_input
from components.modals.generic import GenericModal
from services.disc import respond
from util.datatypes import Language, SendType
from util.identifiers import TextPieceID


class ApprovalModal(GenericModal):
    def __init__(self, request_id: int, send_type: SendType, language: Language) -> None:
        super().__init__(
            title=facades.texts.render_text(TextPieceID.REQUEST_OPINION_MODAL_TITLE, language),
            timeout=None,
            custom_id=f'am:{request_id}:{send_type.value}'
        )

        self.add_item(get_review_text_input("am:rti", language, False))

    @classmethod
    async def process_submission(cls, interaction: Interaction, custom_id_fields: list[str], text_input_values: dict[str, str]) -> None:
        request_id = int(custom_id_fields[0])
        send_type = SendType(custom_id_fields[1])
        review_text = text_input_values.get("am:rti")

        import facades.requests
        await facades.requests.resolve(
            resolving_mod=interaction.user,
            request_id=request_id,
            sent_for=send_type,
            review_text=review_text
        )
        await respond(interaction, TextPieceID.COMMON_SUCCESS, ephemeral=True)