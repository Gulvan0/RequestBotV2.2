from functools import cache

import jsonschema
import typing as tp

from globalconf import CONFIG
from util.identifiers import StageParameterID
from util.io import load_data_json


CONTENT = load_data_json('stage_parameters')


@cache
def get_value(parameter: StageParameterID) -> tp.Any:
    return CONTENT[parameter.value][CONFIG.stage]


def validate() -> None:
    schema = load_data_json('schemas/stage_parameters')
    jsonschema.validate(CONTENT, schema)

    for parameter_id in StageParameterID:
        assert parameter_id.value in CONTENT, f"Stage parameter ID {parameter_id.value} is present in the code, but missing in config"

    for key, value in CONTENT.items():
        assert key in StageParameterID, f"Stage parameter ID {key} is present in the config, but missing in code"