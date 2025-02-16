from dataclasses import dataclass

from discord import Member
from sqlalchemy import func
from sqlmodel import select, Session

from components.views.trainee_review_widget import TraineeReviewWidgetView
from database.db import engine
from database.models import Request, RequestReview, TraineeReviewOpinion
from facades.eventlog import add_entry
from facades.texts import render_text
from services.disc import find_message, post_raw_text
from util.datatypes import Opinion
from util.format import as_code, as_link, as_user
from util.identifiers import LoggedEventTypeID, RouteID, TextPieceID


@dataclass
class TraineeStats:
    review_cnt: int
    resolved_review_cnt: int
    acceptance_ratio: float


async def add_trainee_review(trainee: Member, request_id: int, opinion: Opinion, review_text: str, rejection_reason: str | None = None) -> None:
    with Session(engine) as session:
        request: Request = session.get(Request, request_id)  # noqa

        assert request

        level_id = str(request.level_id)
        level_name = request.level_name

    details_widget = None
    if request.details_message_id and request.details_message_channel_id:
        details_widget = await find_message(request.details_message_channel_id, request.details_message_id)

    message_lines = [
        f"Review by {trainee.mention}",
        f"Level: {request.level_name} (ID: {request.level_id})",
    ]

    if details_widget:
        message_lines.append(as_link(details_widget.jump_url, "Info Widget"))

    message_lines += [
        "Review:",
        review_text,
        render_text(TextPieceID.REQUEST_SUMMARY_GOOD if opinion == Opinion.APPROVED else TextPieceID.REQUEST_SUMMARY_BAD, request.language)
    ]

    if rejection_reason:
        message_lines.append(f"**Rejection reason**: {as_code(rejection_reason)}")

    review_message = await post_raw_text(
        RouteID.TRAINEE_REVIEW_TEXT,
        "\n".join(message_lines)
    )

    with Session(engine) as session:
        review = RequestReview(
            author_user_id=trainee.id,
            text=review_text,
            message_id=review_message.id,
            message_channel_id=review_message.channel.id,
            opinion=opinion,
            request=request,
            is_trainee=True
        )
        session.add(review)
        session.commit()
        await review_message.edit(view=TraineeReviewWidgetView(review.id))

    await add_entry(LoggedEventTypeID.TRAINEE_REVIEW_ADDED, trainee, dict(
        request_id=request_id,
        level_id=level_id,
        level_name=level_name,
        review_link=review_message.jump_url,
        opinion=opinion.value
    ))


async def resolve_trainee_review(supervisor: Member, review_id: int, accept: bool, feedback: str | None = None) -> TraineeStats:
    with Session(engine) as session:
        review = session.get(RequestReview, review_id)
        trainee_user_id = review.author_user_id

        opinion = TraineeReviewOpinion(
            opinion_author_user_id=supervisor.id,
            accept=accept,
            feedback=feedback,
            review_id=review_id
        )
        session.add(opinion)
        session.commit()

        review_message = await find_message(review.message_channel_id, review.message_id)

    review_reference = str(review_id)
    if review_message:
        review_reference = review_message.jump_url

        await review_message.edit(view=None)

        if feedback:
            thread = await review_message.create_thread(name="Feedback", auto_archive_duration=60)
            await thread.send(as_user(trainee_user_id) + "\n" + feedback)

    with Session(engine) as session:
        review_cnt = session.exec(
            select(func.count(RequestReview.id)).where(RequestReview.is_trainee == True, RequestReview.author_user_id == trainee_user_id)  # noqa
        ).first() or 0
        resolved_review_cnt = session.exec(
            select(func.count(TraineeReviewOpinion.review_id)).join(RequestReview).where(RequestReview.author_user_id == trainee_user_id)  # noqa
        ).first() or 0
        accepted_review_cnt = session.exec(
            select(func.count(TraineeReviewOpinion.review_id)).join(RequestReview).where(TraineeReviewOpinion.accept == True, RequestReview.author_user_id == trainee_user_id)  # noqa
        ).first() or 0

    await add_entry(LoggedEventTypeID.TRAINEE_REVIEW_RESOLVED, supervisor, dict(
        review=review_reference,
        trainee_user_id=trainee_user_id,
        accepted=str(accept),
        feedback=feedback or "NO_FEEDBACK",
        review_cnt=str(review_cnt),
        resolved_review_cnt=str(resolved_review_cnt),
        accepted_review_cnt=str(accepted_review_cnt),
    ))

    return TraineeStats(review_cnt, resolved_review_cnt, accepted_review_cnt / resolved_review_cnt if resolved_review_cnt else 0)


async def promote_trainee(trainee_user_id: int, supervisor: Member) -> None:
    ...  # TODO: Fill
    # TODO: Log event


async def expel_trainee(trainee_user_id: int, supervisor: Member) -> None:
    ...  # TODO: Fill
    # TODO: Log event