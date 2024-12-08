from __future__ import annotations

from components.views.pagination.generic import GenericPaginationView
from facades.cooldowns import list_endless_cooldowns
from util.datatypes import CooldownEntity
from util.format import as_code, as_user


class EndlessCooldownPaginationView(GenericPaginationView):
    def __init__(self, entity: CooldownEntity) -> None:
        super().__init__()

        self.entity: CooldownEntity = entity

        self.limit = 10

    async def get_current_page_blocks(self) -> list[str]:
        lines = []

        id_to_reason_mapping = list_endless_cooldowns(self.entity, self.limit, self.offset)
        for entity_id, reason in id_to_reason_mapping.items():
            line = as_user(entity_id) if self.entity == CooldownEntity.USER else as_code(entity_id)
            if reason:
                line += f" ({as_code(reason)})"
            lines.append(line)

        return lines
