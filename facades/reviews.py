from discord import Member
from sqlmodel import select, Session

from database.db import engine
from database.models import Request, RequestReview


async def get_level_reviews(level_id: int) -> list[RequestReview]:
    with Session(engine) as session:
        query = select(RequestReview).join(Request).where(Request.level_id == level_id, RequestReview.is_trainee == False).order_by(RequestReview.created_at)  # noqa
        return [x for x in session.exec(query)]  # noqa


async def get_user_reviews(author: Member) -> list[RequestReview]:
    with Session(engine) as session:
        query = select(RequestReview).where(RequestReview.author_user_id == author.id).order_by(RequestReview.created_at)
        return [x for x in session.exec(query)]  # noqa