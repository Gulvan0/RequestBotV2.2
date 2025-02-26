import asyncio
from dataclasses import dataclass
from enum import StrEnum, IntEnum, Enum, auto

import requests
import typing as tp
from datetime import datetime, timedelta


class Endpoint(StrEnum):
    GET_LEVELS = "http://www.boomlings.com/database/getGJLevels21.php"


class LevelFieldKey(IntEnum):
    LEVEL_NAME = 2
    AUTHOR_PLAYER_ID = 6
    DIFFICULTY_NUMERATOR = 9
    GAME_VERSION = 13
    LENGTH = 15
    DEMON = 17
    STARS = 18
    FEATURE_SCORE = 19
    AUTO = 25
    COPIED_ID = 30
    REQUESTED_STARS = 39
    EPIC = 42
    DEMON_DIFFICULTY = 43


class LevelDifficulty(Enum):
    UNRATED = auto()
    AUTO = auto()
    EASY = auto()
    NORMAL = auto()
    HARD = auto()
    HARDER = auto()
    INSANE = auto()
    EASY_DEMON = auto()
    MEDIUM_DEMON = auto()
    HARD_DEMON = auto()
    INSANE_DEMON = auto()
    EXTREME_DEMON = auto()

    def to_str(self) -> str:
        match self:
            case LevelDifficulty.UNRATED:
                return "Unrated"
            case LevelDifficulty.AUTO:
                return "Auto"
            case LevelDifficulty.EASY:
                return "Easy"
            case LevelDifficulty.NORMAL:
                return "Normal"
            case LevelDifficulty.HARD:
                return "Hard"
            case LevelDifficulty.HARDER:
                return "Harder"
            case LevelDifficulty.INSANE:
                return "Insane"
            case LevelDifficulty.EASY_DEMON:
                return "Easy Demon"
            case LevelDifficulty.MEDIUM_DEMON:
                return "Medium Demon"
            case LevelDifficulty.HARD_DEMON:
                return "Hard Demon"
            case LevelDifficulty.INSANE_DEMON:
                return "Insane Demon"
            case LevelDifficulty.EXTREME_DEMON:
                return "Extreme Demon"
            case _:
                tp.assert_never(self)


class LevelLength(IntEnum):
    TINY = 0
    SHORT = 1
    MEDIUM = 2
    LONG = 3
    XL = 4
    PLATFORMER = 5

    def to_str(self) -> str:
        match self:
            case LevelLength.TINY:
                return "Tiny"
            case LevelLength.SHORT:
                return "Short"
            case LevelLength.MEDIUM:
                return "Medium"
            case LevelLength.LONG:
                return "Long"
            case LevelLength.XL:
                return "XL"
            case LevelLength.PLATFORMER:
                return "Platformer"
            case _:
                tp.assert_never(self)


class LevelGrade(Enum):
    UNRATED = auto()
    RATED = auto()
    FEATURED = auto()
    EPIC = auto()
    LEGENDARY = auto()
    MYTHIC = auto()

    def to_str(self) -> str:
        match self:
            case LevelGrade.UNRATED:
                return "unrated"
            case LevelGrade.RATED:
                return "rated"
            case LevelGrade.FEATURED:
                return "featured"
            case LevelGrade.EPIC:
                return "epic"
            case LevelGrade.LEGENDARY:
                return "legendary"
            case LevelGrade.MYTHIC:
                return "mythic"
            case _:
                tp.assert_never(self)


@dataclass
class Level:
    name: str
    author_name: str
    difficulty: LevelDifficulty
    stars: int | None
    stars_requested: int | None
    game_version: str
    length: LevelLength
    grade: LevelGrade
    copied_level_id: int | None


class ApiWrapper:
    def __init__(self):
        self.last_api_call: datetime | None = None
        self.api_call_lock = asyncio.Lock()
        self.api_call_interval = timedelta(seconds=0.6)

    async def perform_request(self, endpoint: Endpoint, data: dict) -> str | None:
        async with self.api_call_lock:
            if self.last_api_call:
                time_passed = datetime.now() - self.last_api_call
                remaining_seconds = (self.api_call_interval - time_passed).total_seconds()
                if remaining_seconds > 0:
                    await asyncio.sleep(remaining_seconds)

            data.update(secret="Wmfd2893gb7")

            response = requests.post(
                url=endpoint,
                data=data,
                headers={"User-Agent": ""}
            ).text

            self.last_api_call = datetime.now()

            if response == "-1":
                return None
            return response


API = ApiWrapper()


def _get_level_fields(api_response_parts: list[str]) -> dict[int, str]:
    splitted = api_response_parts[0].split(":")
    return dict(zip(map(int, splitted[::2]), splitted[1::2]))


def _get_level_author_name(api_response_parts: list[str]) -> str:
    creator_string = api_response_parts[1]
    if not creator_string or ":" not in creator_string:
        return 'Anonymous Creator'
    return creator_string.split(":")[1]


async def get_level(level_id: int) -> Level | None:
    raw_response = await API.perform_request(
        Endpoint.GET_LEVELS,
        dict(
            type=19,
            str=str(level_id)
        )
    )
    if not raw_response:
        return None

    response_parts = raw_response.split("#")
    level_fields = _get_level_fields(response_parts)
    author_name = _get_level_author_name(response_parts)

    if level_fields.get(LevelFieldKey.AUTO) == '1':
        difficulty = LevelDifficulty.AUTO
    elif level_fields.get(LevelFieldKey.DEMON) == '1':
        match level_fields.get(LevelFieldKey.DEMON_DIFFICULTY):
            case '3':
                difficulty = LevelDifficulty.EASY_DEMON
            case '4':
                difficulty = LevelDifficulty.MEDIUM_DEMON
            case '5':
                difficulty = LevelDifficulty.INSANE_DEMON
            case '6':
                difficulty = LevelDifficulty.EXTREME_DEMON
            case _:
                difficulty = LevelDifficulty.HARD_DEMON
    else:
        match level_fields.get(LevelFieldKey.DIFFICULTY_NUMERATOR):
            case '10':
                difficulty = LevelDifficulty.EASY
            case '20':
                difficulty = LevelDifficulty.NORMAL
            case '30':
                difficulty = LevelDifficulty.HARD
            case '40':
                difficulty = LevelDifficulty.HARDER
            case '50':
                difficulty = LevelDifficulty.INSANE
            case _:
                difficulty = LevelDifficulty.UNRATED

    game_version_number = int(level_fields[LevelFieldKey.GAME_VERSION])
    if game_version_number <= 7:
        game_version = f'1.{game_version_number - 1}'
    elif game_version_number == 10:
        game_version = '1.7'
    else:
        game_version = f'{game_version_number / 10:.1f}'

    stars = int(level_fields[LevelFieldKey.STARS]) or None
    stars_requested = int(level_fields[LevelFieldKey.REQUESTED_STARS]) or None

    if not stars:
        grade = LevelGrade.UNRATED
    elif level_fields[LevelFieldKey.FEATURE_SCORE] == '0':
        grade = LevelGrade.RATED
    else:
        match int(level_fields[LevelFieldKey.EPIC]):
            case 1:
                grade = LevelGrade.EPIC
            case 2:
                grade = LevelGrade.LEGENDARY
            case 3:
                grade = LevelGrade.MYTHIC
            case _:
                grade = LevelGrade.FEATURED

    return Level(
        name=level_fields[LevelFieldKey.LEVEL_NAME],
        author_name=author_name,
        difficulty=difficulty,
        stars=stars,
        stars_requested=stars_requested,
        game_version=game_version,
        length=LevelLength(int(level_fields[LevelFieldKey.LENGTH])),
        grade=grade,
        copied_level_id=int(level_fields[LevelFieldKey.COPIED_ID]) or None
    )
