from dataclasses import dataclass

from discord import Member
from sqlmodel import select, Session

from database.db import engine
from database.models import Request, RequestReview


@dataclass
class UserReviewData:
    level_name: str
    message_channel_id: int
    message_id: int


async def get_level_reviews(level_id: int) -> list[RequestReview]:
    with Session(engine) as session:
        query = select(RequestReview).join(Request).where(Request.level_id == level_id, RequestReview.is_trainee == False).order_by(RequestReview.created_at)  # noqa
        return [x for x in session.exec(query)]  # noqa


async def get_user_reviews(author: Member, limit: int, offset: int) -> list[UserReviewData]:
    reviews = []
    with Session(engine) as session:
        query = select(RequestReview).where(RequestReview.author_user_id == author.id).order_by(RequestReview.created_at).limit(limit).offset(offset)
        for review in session.exec(query):  # noqa
            reviews.append(UserReviewData(
                level_name=review.request.level_name,
                message_channel_id=review.message_channel_id,
                message_id=review.message_id
            ))
    return reviews