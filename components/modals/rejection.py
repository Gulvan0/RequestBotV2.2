from discord import Interaction

import facades.texts
from components.modals.common_items import get_reason_text_input, get_review_text_input
from components.modals.generic import GenericModal
from services.disc import respond
from util.datatypes import CooldownEntity, Language
from util.identifiers import TextPieceID


class RejectionModal(GenericModal):
    def __init__(self, request_id: int, language: Language) -> None:
        super().__init__(
            title=facades.texts.render_text(TextPieceID.REQUEST_OPINION_MODAL_TITLE, language),
            timeout=None,
            custom_id=f'rm:{request_id}'
        )

        self.add_item(get_review_text_input("rm:rti", language, False))
        self.add_item(get_reason_text_input("rm:ri", language, False))

    @classmethod
    async def process_submission(cls, interaction: Interaction, custom_id_fields: list[str], text_input_values: dict[str, str]) -> None:
        request_id = int(custom_id_fields[0])
        review_text = text_input_values.get("rm:rti")
        reason = text_input_values.get("rm:ri")

        import facades.requests
        import facades.cooldowns
        
        await facades.requests.resolve(
            resolving_mod=interaction.user,
            request_id=request_id,
            sent_for=None,
            review_text=review_text,
            reason=reason
        )

        request = await facades.requests.get_request_by_id(request_id)
        await facades.cooldowns.cast_after_request(CooldownEntity.LEVEL, request.level_id, request_id)

        await respond(interaction, TextPieceID.COMMON_SUCCESS, ephemeral=True)