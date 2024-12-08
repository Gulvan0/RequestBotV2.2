from __future__ import annotations

from components.views.pagination.generic import GenericPaginationView
from facades.cooldowns import list_temporary_cooldowns, CooldownInfo
from util.datatypes import CooldownEntity
from util.format import as_code, as_timestamp, as_user


class TemporaryCooldownPaginationView(GenericPaginationView):
    def __init__(self, entity: CooldownEntity) -> None:
        super().__init__()

        self.entity: CooldownEntity = entity

        self.limit = 10

    def _render_cooldown_line(self, info: CooldownInfo) -> str:
        entity_reference = as_user(info.entity_id) if self.entity == CooldownEntity.USER else as_code(info.entity_id)
        line = f"{entity_reference} {as_timestamp(info.ends_at)}"
        if info.reason:
            line += f" ({as_code(info.reason)})"
        return line

    async def get_current_page_blocks(self) -> list[str]:
        return list(map(self._render_cooldown_line, list_temporary_cooldowns(self.entity, self.limit, self.offset)))
