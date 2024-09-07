from dataclasses import dataclass

from util.datatypes import Stage


@dataclass
class GlobalConfiguration:
    stage: Stage = Stage.TEST


CONFIG = GlobalConfiguration()
