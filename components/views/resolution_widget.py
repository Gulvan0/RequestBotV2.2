from discord import ButtonStyle, Interaction
from discord.ui import View, button


class ResolutionWidgetView(View):  # TODO: Fill the gaps
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @button(label="Starrate", style=ButtonStyle.green, row=0)
    async def starrate(self, inter: Interaction, _) -> None:
        ...

    @button(label="Feature", style=ButtonStyle.green, row=0)
    async def feature(self, inter: Interaction, _) -> None:
        ...

    @button(label="Epic", style=ButtonStyle.green, row=0)
    async def epic(self, inter: Interaction, _) -> None:
        ...

    @button(label="Mythic", style=ButtonStyle.green, row=0)
    async def mythic(self, inter: Interaction, _) -> None:
        ...

    @button(label="Legendary", style=ButtonStyle.green, row=0)
    async def legendary(self, inter: Interaction, _) -> None:
        ...

    @button(label="Reject", style=ButtonStyle.red, row=1)
    async def reject(self, inter: Interaction, _) -> None:
        ...