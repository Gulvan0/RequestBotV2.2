from dataclasses import dataclass

from discord import Colour, Embed, Member, Object
from sqlalchemy import func
from sqlmodel import col, select, Session

from components.views.trainee_review_widget import TraineeReviewWidgetView
from database.db import engine
from database.models import Request, RequestReview, TraineeReviewOpinion
from facades.eventlog import add_entry
from facades.permissions import get_permission_role_ids, has_permission
from facades.texts import render_text
from services.disc import find_message, find_member, get_default_role, post_raw_text
from util.datatypes import Opinion
from util.format import as_code, as_link, as_user
from util.identifiers import LoggedEventTypeID, PermissionFlagID, RouteID, TextPieceID


@dataclass
class RoleNotAssociatedException(Exception):
    """
    Raised during promoting/expelling a trainee when a permission to be assigned to or taken from the ex-trainee is not associated with any role, hence making it impossible to change ex-trainee's permissions
    """
    permission: PermissionFlagID


class NotATraineeException(Exception):
    """
    Raised when trying to promote/expel a member who isn't a trainee
    """
    pass


@dataclass
class TraineeStats:
    user_id: int
    review_cnt: int
    resolved_review_cnt: int
    acceptance_ratio: float


@dataclass
class RandomPickedRequest:
    request_id: int
    embed: Embed


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
        request_id=str(request_id),
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
        trainee_user_id=str(trainee_user_id),
        accepted=str(accept),
        feedback=feedback or "NO_FEEDBACK",
        review_cnt=str(review_cnt),
        resolved_review_cnt=str(resolved_review_cnt),
        accepted_review_cnt=str(accepted_review_cnt),
    ))

    return TraineeStats(trainee_user_id, review_cnt, resolved_review_cnt, accepted_review_cnt / resolved_review_cnt if resolved_review_cnt else 0)


async def promote_trainee(trainee_or_user_id: int | Member, supervisor: Member) -> None:
    if isinstance(trainee_or_user_id, int):
        trainee = await find_member(trainee_or_user_id)
        assert trainee
    else:
        trainee = trainee_or_user_id

    if not has_permission(trainee, PermissionFlagID.TRAINEE, False):
        raise NotATraineeException

    default_role = get_default_role()

    trainee_role_ids = await get_permission_role_ids(PermissionFlagID.TRAINEE)
    trainee_role_ids.discard(default_role.id)
    if not trainee_role_ids:
        raise RoleNotAssociatedException(PermissionFlagID.TRAINEE)

    reviewer_role_ids = await get_permission_role_ids(PermissionFlagID.REVIEWER)
    reviewer_role_ids.discard(default_role.id)
    if not reviewer_role_ids:
        raise RoleNotAssociatedException(PermissionFlagID.REVIEWER)

    trainee_roles = [Object(id=role_id) for role_id in trainee_role_ids]
    reviewer_role = Object(id=reviewer_role_ids.pop())

    await trainee.remove_roles(*trainee_roles)
    await trainee.add_roles(reviewer_role)

    await add_entry(LoggedEventTypeID.TRAINEE_PROMOTED, supervisor, dict(
        trainee_user_id=str(trainee.id)
    ))


async def expel_trainee(trainee_or_user_id: int | Member, supervisor: Member) -> None:
    if isinstance(trainee_or_user_id, int):
        trainee = await find_member(trainee_or_user_id)
        assert trainee
    else:
        trainee = trainee_or_user_id

    if not has_permission(trainee, PermissionFlagID.TRAINEE, False):
        raise NotATraineeException

    default_role = get_default_role()

    trainee_role_ids = await get_permission_role_ids(PermissionFlagID.TRAINEE)
    trainee_role_ids.discard(default_role.id)
    if not trainee_role_ids:
        raise RoleNotAssociatedException(PermissionFlagID.TRAINEE)

    trainee_roles = [Object(id=role_id) for role_id in trainee_role_ids]

    await trainee.remove_roles(*trainee_roles)

    await add_entry(LoggedEventTypeID.TRAINEE_EXPELLED, supervisor, dict(
        trainee_user_id=str(trainee.id)
    ))


async def pick_random_request(invoking_trainee: Member) -> RandomPickedRequest | None:
    with Session(engine) as session:
        request: Request | None = session.exec(
            select(  # noqa
                Request
            ).where(
                ~col(Request.id).in_(
                    select(RequestReview.request_id).where(RequestReview.author_user_id == invoking_trainee.id)
                ),
                Request.details_message_id != None,  # noqa
                Request.details_message_channel_id != None  # noqa
            ).order_by(
                func.random()
            )
        ).first()

    if not request:
        return None

    details_message = await find_message(request.details_message_channel_id, request.details_message_id)
    if not details_message or not details_message.embeds:
        return None

    embed = details_message.embeds[0]

    embed.colour = Colour.from_str("#0000aa")

    removed_fields = set()
    for field_index, field in enumerate(embed.fields):
        if field.name in ("Consensus", "Opinions and Resolutions"):
            removed_fields.add(field_index)
    for field_index in sorted(removed_fields, reverse=True):  # After each removal, indexes of the fields following the removed one get updated, so we need to go backwards
        embed.remove_field(field_index)

    return RandomPickedRequest(request.id, embed)