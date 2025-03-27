from __future__ import annotations

from discord import Member

from components.views.pagination.generic import GenericPaginationView
from facades.reviews import get_user_reviews, UserReviewData
from services.disc import find_message
from util.format import as_link


class ReviewsPaginationView(GenericPaginationView):
    def __init__(self, author: Member) -> None:
        super().__init__()

        self.author = author

        self.limit = 10

    @staticmethod
    async def _render_block(review: UserReviewData) -> str:
        review_message = await find_message(review.message_channel_id, review.message_id)
        if review_message:
            return as_link(review_message.jump_url, review.level_name)
        return f"_{review.level_name} (deleted)_"

    async def get_current_page_blocks(self) -> list[str]:
        reviews = await get_user_reviews(self.author, self.limit, self.offset)
        return [await self._render_block(review) for review in reviews]
