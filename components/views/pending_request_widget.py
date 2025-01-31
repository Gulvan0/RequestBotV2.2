from discord import ButtonStyle, Interaction
from discord.ui import View, button

from facades.requests import add_opinion
from services.disc import respond
from util.datatypes import Opinion
from util.identifiers import TextPieceID


class PendingRequestWidgetView(View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @button(label="Approve and Review", style=ButtonStyle.green)
    async def approve_and_review(self, inter: Interaction, _) -> None:
        ...  # TODO: Show modal to provide a review, then call add_opinion

    @button(label="Reject and Review", style=ButtonStyle.red)
    async def reject_and_review(self, inter: Interaction, _) -> None:
        ...  # TODO: Show a modal to provide a review and an optional reason, then call add_opinion

    @button(label="Just Approve", style=ButtonStyle.green)
    async def just_approve(self, inter: Interaction, _) -> None:
        await add_opinion(inter.user, inter.message, Opinion.APPROVED)
        await respond(inter, TextPieceID.COMMON_SUCCESS)

    @button(label="Just Reject", style=ButtonStyle.red)
    async def just_reject(self, inter: Interaction, _) -> None:
        ...  # TODO: Show a modal to provide an optional reason, then call add_opinion