from enum import auto, Enum, StrEnum, unique

import discord
from discord import app_commands


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
    TEMPORARY = "List temporary cooldowns"
    ENDLESS = "List lifetime bans"


@unique
class CooldownEntity(StrEnum):
    USER = auto()
    LEVEL = auto()
