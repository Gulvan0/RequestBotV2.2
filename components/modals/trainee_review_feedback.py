from discord import Interaction, TextStyle
from discord.ui import TextInput

from components.modals.generic import GenericModal
from facades.parameters import get_value as get_parameter_value
from services.disc import respond
from util.datatypes import Language
from util.identifiers import ParameterID, TextPieceID

import facades.texts


class TraineeReviewFeedbackModal(GenericModal):
    def __init__(self, review_id: int, accept: bool, language: Language) -> None:
        super().__init__(
            title=facades.texts.render_text(TextPieceID.TRAINEE_REVIEW_MODAL_TITLE, language),
            timeout=None,
            custom_id=f'trf:{review_id}:{int(accept)}'
        )

        self.add_item(TextInput(
            label=facades.texts.render_text(TextPieceID.TRAINEE_REVIEW_MODAL_FEEDBACK_LABEL, language)[:100],
            placeholder=facades.texts.render_text(TextPieceID.TRAINEE_REVIEW_MODAL_FEEDBACK_PLACEHOLDER, language)[:100],
            required=False,
            min_length=40,
            max_length=4000,
            style=TextStyle.long,
            custom_id="trf:f"
        ))

    @classmethod
    async def process_submission(cls, interaction: Interaction, custom_id_fields: list[str], text_input_values: dict[str, str]) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        review_id = int(custom_id_fields[0])
        accept = bool(int(custom_id_fields[1]))
        feedback = text_input_values.get("trf:f")

        import facades.trainee
        trainee_stats = await facades.trainee.resolve_trainee_review(interaction.user, review_id, accept, feedback)

        threshold = get_parameter_value(ParameterID.TRAINEE_RESOLVED_REVIEWS_FOR_PROMOTION_DECISION, int)
        if trainee_stats.resolved_review_cnt < threshold:
            await respond(
                interaction,
                TextPieceID.TRAINEE_REVIEW_RESOLUTION_RESPONSE_FEW_REVIEWS,
                substitutions=dict(
                    resolved_review_cnt=str(trainee_stats.resolved_review_cnt),
                    pending_review_cnt=str(trainee_stats.review_cnt - trainee_stats.resolved_review_cnt),
                    reviews_left_until_threshold_cnt=str(threshold - trainee_stats.resolved_review_cnt),
                    acceptance_percent=str(round(trainee_stats.acceptance_ratio * 100))
                ),
                ephemeral=True
            )
        else:
            await respond(
                interaction,
                TextPieceID.TRAINEE_REVIEW_RESOLUTION_RESPONSE_PROMOTION_READY,
                substitutions=dict(
                    resolved_review_cnt=str(trainee_stats.resolved_review_cnt),
                    acceptance_percent=str(round(trainee_stats.acceptance_ratio * 100))
                ),
                ephemeral=True
            )
            # TODO: Respond with promotion view (+ add widget btns to dynamic items)