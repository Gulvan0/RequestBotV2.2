from datetime import date, datetime, timedelta
from enum import auto, Enum, StrEnum, unique

import discord
from attr import dataclass
from discord import app_commands

from util.identifiers import TextPieceID
from util.time import get_date, to_end_of_week, to_start_of_day, to_start_of_week


@unique
class Language(StrEnum):
    EN = "eng"
    RU = "rus"


@unique
class Stage(StrEnum):
    TEST = "test"
    PROD = "prod"


@unique
class UserProvidedValueType(StrEnum):
    BOOLEAN = "bool"
    NON_NEGATIVE_INTEGER = "uint"
    NATURAL = "natural"
    INTEGER = "int"
    FLOAT = "float"
    POSITIVE_FLOAT = "positive_float"
    NON_NEGATIVE_FLOAT = "positive_float_or_zero"
    STRING = "str"
    NON_EMPTY_STRING = "non_empty_str"
    DURATION = "duration"

    def get_displayed_name(self) -> str:
        match self:
            case UserProvidedValueType.BOOLEAN:
                return "Логический (true/false)"
            case UserProvidedValueType.NON_NEGATIVE_INTEGER:
                return "Неотрицательное целое число (0 или больше)"
            case UserProvidedValueType.NATURAL:
                return "Натуральное число (1 или больше)"
            case UserProvidedValueType.INTEGER:
                return "Целое число"
            case UserProvidedValueType.FLOAT:
                return "Число"
            case UserProvidedValueType.POSITIVE_FLOAT:
                return "Положительное число (строго больше 0)"
            case UserProvidedValueType.NON_NEGATIVE_FLOAT:
                return "Неотрицательное число (0 или больше)"
            case UserProvidedValueType.STRING:
                return "Строка текста"
            case UserProvidedValueType.NON_EMPTY_STRING:
                return "Непустая строка текста"
            case UserProvidedValueType.DURATION:
                return "Продолжительность (абсолютная; формат описан в /help duration)"


@unique
class CooldownListingOption(StrEnum):
    TEMPORARY = auto()
    ENDLESS = auto()


@unique
class CooldownEntity(StrEnum):
    USER = auto()
    LEVEL = auto()


@unique
class Opinion(StrEnum):
    APPROVED = auto()
    REJECTED = auto()


@unique
class SendType(StrEnum):
    STARRATE = 's'
    FEATURE = 'f'
    EPIC = 'e'
    MYTHIC = 'm'
    LEGENDARY = 'l'


class CommandChoiceOption:
    @classmethod
    def autocomplete_from_enum(cls, e: type[Enum]):
        async def callback(inter: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
            return [
                app_commands.Choice(name=option.value, value=option.value)
                for option in e
                if option.value.lower().startswith(current.lower())
            ][:25]
        return callback

    @classmethod
    def from_enum(cls, e: type[Enum]) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=option.value, value=option.value) for option in e]

    @classmethod
    def from_str_enum(cls, e: type[StrEnum]) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=option, value=option) for option in e]

    @classmethod
    def cooldown_listing_type(cls) -> list[app_commands.Choice[CooldownListingOption]]:
        return [
            app_commands.Choice(name=TextPieceID.COMMAND_CHOICE_COOLDOWN_LISTING_TEMPORARY.as_locale_str(), value=CooldownListingOption.TEMPORARY),
            app_commands.Choice(name=TextPieceID.COMMAND_CHOICE_COOLDOWN_LISTING_ENDLESS.as_locale_str(), value=CooldownListingOption.ENDLESS)
        ]


@dataclass(frozen=True)
class ReportBin:
    value: date
    name: str


@dataclass(frozen=True)
class SimpleReportRange:
    date_from: date | None
    date_to: date

    def get_inclusive_min_datetime(self) -> datetime | None:
        return to_start_of_day(self.date_from) if self.date_from else None

    def get_exclusive_max_datetime(self) -> datetime | None:
        return to_start_of_day(self.date_to + timedelta(days=1))

    def restrict_query(self, query, datetime_attribute):
        min_ts = self.get_inclusive_min_datetime()
        max_ts = self.get_exclusive_max_datetime()
        if min_ts:
            query = query.where(datetime_attribute >= min_ts)
        if max_ts:
            query = query.where(datetime_attribute < max_ts)
        return query

    def get_plot_subtitle(self) -> str:
        return f"From {self.date_from.isoformat()} to {self.date_to.isoformat()}" if self.date_from else f"Up until {self.date_to.isoformat()}"


@dataclass(frozen=True, kw_only=True)
class ReportRange(SimpleReportRange):
    weekly_granularity: bool

    def get_bin(self, timestamp: date | datetime) -> ReportBin:
        if self.weekly_granularity:
            start_of_week = to_start_of_week(timestamp)
            end_of_week = to_end_of_week(timestamp)
            return ReportBin(
                value=start_of_week,
                name=f"{start_of_week.isoformat()} - {end_of_week.isoformat()}"
            )
        else:
            day = get_date(timestamp)
            return ReportBin(
                value=day,
                name=day.isoformat()
            )

    def get_first_bin_value(self) -> date | None:
        return self.get_bin(self.date_from).value if self.date_from else None

    def get_last_bin_value(self) -> date | None:
        return self.get_bin(self.date_to).value

    def get_x_axis_name(self) -> str:
        return 'Week' if self.weekly_granularity else 'Date'

    def get_plot_subtitle(self) -> str:
        range_info = super().get_plot_subtitle()
        return f"{range_info} (per week)" if self.weekly_granularity else range_info
