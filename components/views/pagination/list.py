from __future__ import annotations

from components.views.pagination.generic import GenericPaginationView


class ListPaginationView(GenericPaginationView):
    def __init__(self, paginated_list: list[str], limit: int = 10) -> None:
        super().__init__()

        self.paginated_list = paginated_list

        self.limit = limit

    async def get_current_page_blocks(self) -> list[str]:
        return self.paginated_list[self.offset:self.offset + self.limit]
