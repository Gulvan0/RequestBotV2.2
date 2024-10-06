from enum import StrEnum, unique


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
