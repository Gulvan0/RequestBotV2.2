import traceback
from abc import ABC, abstractmethod

from discord import Interaction
from discord.ui import Modal

from services.disc import send_developers


class GenericModal(Modal, ABC):
    @classmethod
    @abstractmethod
    async def process_submission(cls, interaction: Interaction, custom_id_fields: list[str], text_input_values: dict[str, str]) -> None:
        pass

    @classmethod
    async def handle_interaction(cls, interaction: Interaction) -> None:
        text_input_values = {}
        for component_row in interaction.data.get("components", []):
            for comp in component_row.get("components", []):
                text_input_values[comp.get("custom_id")] = comp.get("value")

        await cls.process_submission(
            interaction=interaction,
            custom_id_fields=interaction.data.get("custom_id").split(":")[1:],
            text_input_values=text_input_values
        )

    async def on_error(self, interaction: Interaction, error: Exception) -> None:
        error_details = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        await send_developers(error_details, "py")
        self.stop()