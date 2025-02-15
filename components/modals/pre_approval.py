from discord import Interaction

import facades.texts
from components.modals.common_items import get_review_text_input
from components.modals.generic import GenericModal
from facades.permissions import has_permission
from services.disc import respond
from util.datatypes import Language, Opinion
from util.identifiers import PermissionFlagID, TextPieceID


class PreApprovalModal(GenericModal):
    def __init__(self, request_id: int, language: Language) -> None:
        super().__init__(
            title=facades.texts.render_text(TextPieceID.REQUEST_OPINION_MODAL_TITLE, language),
            timeout=None,
            custom_id=f'pam:{request_id}'
        )

        self.add_item(get_review_text_input("pam:rti", language))

    @classmethod
    async def process_submission(cls, interaction: Interaction, custom_id_fields: list[str], text_input_values: dict[str, str]) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        request_id = int(custom_id_fields[0])
        review_text = text_input_values.get("pam:rti")

        import facades.requests
        if has_permission(interaction.user, PermissionFlagID.TRAINEE, allow_admin=False):
            await facades.requests.add_trainee_review(interaction.user, request_id, Opinion.APPROVED, review_text)
        else:
            await facades.requests.add_opinion(interaction.user, request_id, Opinion.APPROVED, review_text=review_text)
        await respond(interaction, TextPieceID.COMMON_SUCCESS, ephemeral=True)