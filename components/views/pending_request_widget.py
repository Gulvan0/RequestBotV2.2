from discord import ButtonStyle, Interaction
from discord.ui import View, button


class PendingRequestWidgetView(View):  # TODO: Fill the gaps
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @button(label="Approve and Review", style=ButtonStyle.red)
    async def approve_and_review(self, inter: Interaction, _) -> None:
        ...

    @button(label="Reject and Review", style=ButtonStyle.red)
    async def reject_and_review(self, inter: Interaction, _) -> None:
        ...

    @button(label="Just Approve", style=ButtonStyle.red)
    async def just_approve(self, inter: Interaction, _) -> None:
        ...

    @button(label="Just Reject", style=ButtonStyle.red)
    async def just_reject(self, inter: Interaction, _) -> None:
        ...