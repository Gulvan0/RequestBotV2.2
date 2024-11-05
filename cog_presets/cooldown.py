from dataclasses import dataclass
from datetime import datetime, UTC

import discord
import typing as tp

from components.views.confirmation import ConfirmationView
from components.views.pagination.endless_cooldown import EndlessCooldownPaginationView
from components.views.pagination.temporary_cooldown import TemporaryCooldownPaginationView
from facades.cooldowns import AlreadyOnCooldownError, CooldownEndIsInPast, CooldownEndlessError, get_current_cooldown, manually_amend, manually_modify, manually_set
from services.disc import respond
from util.datatypes import CooldownEntity, CooldownListingOption
from util.exceptions import AlreadySatisfiesError
from util.format import as_code, as_timestamp, as_user, TimestampStyle
from util.identifiers import TextPieceID
from util.parsers import CantParseError, DurationType, get_duration_type, is_infinite_duration, is_null_duration, normalize_duration, parse_abs_duration, parse_rel_duration


@dataclass
class CooldownPreset:
    entity: CooldownEntity

    async def list(self, inter: discord.Interaction, cooldown_listing_type: CooldownListingOption) -> None:
        match cooldown_listing_type:
            case CooldownListingOption.TEMPORARY:
                view = TemporaryCooldownPaginationView(self.entity)
            case CooldownListingOption.ENDLESS:
                view = EndlessCooldownPaginationView(self.entity)
            case _:
                tp.assert_never(cooldown_listing_type)
        await view.respond_with_view(inter, ephemeral=True)

    async def describe(self, inter: discord.Interaction, entity_id: int) -> None:
        cooldown = get_current_cooldown(self.entity, entity_id)

        if cooldown:
            if cooldown.ends_at:
                absolute = as_timestamp(cooldown.ends_at, TimestampStyle.LONG_DATETIME)
                relative = as_timestamp(cooldown.ends_at, TimestampStyle.RELATIVE)
                ends_at_str = f"{absolute} ({relative})"
            else:
                ends_at_str = as_code("-")

            if cooldown.casted_at:
                absolute = as_timestamp(cooldown.casted_at, TimestampStyle.LONG_DATETIME)
                relative = as_timestamp(cooldown.casted_at, TimestampStyle.RELATIVE)
                casted_at_str = f"{absolute} ({relative})"
            else:
                casted_at_str = as_code("-")

            await respond(
                inter,
                TextPieceID.COOLDOWN_INFO,
                substitutions=dict(
                    ends_at=ends_at_str,
                    casted_at=casted_at_str,
                    caster_mention=as_user(cooldown.caster_user_id),
                    reason=cooldown.reason or as_code("-")
                ),
                ephemeral=True
            )
        else:
            await respond(inter, TextPieceID.COOLDOWN_NOT_ON_COOLDOWN, ephemeral=True)

    async def amend(self, inter: discord.Interaction, entity_id: int, reason: str | None = None) -> None:
        try:
            await manually_amend(self.entity, entity_id, inter.user, reason)
        except AlreadySatisfiesError:
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
        else:
            await respond(inter, TextPieceID.COMMON_SUCCESS, ephemeral=True)

    async def update(self, inter: discord.Interaction, entity_id: int, duration: str, reason: str | None = None) -> None:
        try:
            normalized_duration = normalize_duration(duration, {DurationType.ABSOLUTE, DurationType.RELATIVE})
        except CantParseError:
            await respond(inter, TextPieceID.ERROR_BAD_DURATION_FORMAT, substitutions=dict(duration=as_code(duration)), ephemeral=True)
            return

        if is_null_duration(normalized_duration):
            await respond(inter, TextPieceID.WARNING_NO_EFFECT, ephemeral=True)
            return

        if is_infinite_duration(normalized_duration):
            try:
                await manually_set(self.entity, entity_id, inter.user, None, reason)
            except AlreadyOnCooldownError as e:
                async def callback(callback_inter):
                    await manually_set(self.entity, entity_id, callback_inter.user, None, reason, force=True)

                await ConfirmationView().respond_with_view(
                    inter,
                    ephemeral=True,
                    callback=callback,
                    question_text=TextPieceID.COOLDOWN_OVERWRITE_CONFIRMATION,
                    question_substitutions=dict(
                        old=as_timestamp(e.current.ends_at) if e.current.ends_at else as_code("∞"),
                        old_caster_mention=as_user(e.current.caster_user_id),
                        old_reason=as_code(e.current.reason or "-"),
                        new=as_code("∞")
                    )
                )
            return

        match get_duration_type(normalized_duration):
            case DurationType.ABSOLUTE:
                delta = parse_abs_duration(normalized_duration)
                try:
                    await manually_set(self.entity, entity_id, inter.user, delta, reason)
                except CooldownEndIsInPast as e:
                    await respond(
                        inter,
                        TextPieceID.ERROR_COOLDOWN_END_IN_PAST,
                        substitutions=dict(new_ends_at=as_timestamp(e.ends_at, TimestampStyle.LONG_DATETIME)),
                        ephemeral=True
                    )
                except AlreadyOnCooldownError as e:
                    async def callback(callback_inter):
                        await manually_set(self.entity, entity_id, callback_inter.user, delta, reason, force=True)

                    await ConfirmationView().respond_with_view(
                        inter,
                        ephemeral=True,
                        callback=callback,
                        question_text=TextPieceID.COOLDOWN_OVERWRITE_CONFIRMATION,
                        question_substitutions=dict(
                            old=as_timestamp(e.current.ends_at.timestamp()) if e.current.ends_at else as_code("∞"),
                            old_caster_mention=as_user(e.current.caster_user_id),
                            old_reason=as_code(e.current.reason or "-"),
                            new=as_timestamp(datetime.now(UTC) + delta)
                        )
                    )
            case DurationType.RELATIVE:
                delta = parse_rel_duration(normalized_duration)
                try:
                    await manually_modify(self.entity, entity_id, inter.user, delta, reason)
                except CooldownEndlessError:
                    await respond(inter, TextPieceID.ERROR_ORIGIN_COOLDOWN_ENDLESS, ephemeral=True)
                except CooldownEndIsInPast as e:
                    await respond(
                        inter,
                        TextPieceID.ERROR_COOLDOWN_END_IN_PAST,
                        substitutions=dict(new_ends_at=as_timestamp(e.ends_at, TimestampStyle.LONG_DATETIME)),
                        ephemeral=True
                    )
            case _:
                tp.assert_never(normalized_duration)