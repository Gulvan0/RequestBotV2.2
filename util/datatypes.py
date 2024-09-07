from enum import StrEnum, unique


@unique
class Language(StrEnum):
    EN = "eng"
    RU = "rus"


@unique
class Stage(StrEnum):
    TEST = "test"
    PROD = "prod"
