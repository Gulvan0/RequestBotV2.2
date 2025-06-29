from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from discord import Guild, Member

if TYPE_CHECKING:
    from main import RequestBot
from util.datatypes import Stage


@dataclass
class GlobalConfiguration:
    bot: Optional["RequestBot"] = None
    guild: Guild | None = None
    admin: Member | None = None
    stage: Stage = Stage.TEST


CONFIG = GlobalConfiguration()
