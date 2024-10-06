import jsonschema
import re

from util.datatypes import UserProvidedValueType
from util.identifiers import ParameterID
from util.io import load_data_json


CONTENT = load_data_json('parameters')


def get_default_raw(parameter: ParameterID) -> str:
    return CONTENT[parameter.value]["default"]


def get_description(parameter: ParameterID) -> str:
    return CONTENT[parameter.value]["description"]


def _get_value_type(parameter: ParameterID) -> UserProvidedValueType:
    return UserProvidedValueType(CONTENT[parameter.value]["value_type"])


def get_displayed_type(parameter: ParameterID) -> str:
    return _get_value_type(parameter).get_displayed_name()


def normalize_raw_value(parameter: ParameterID, raw_value: str) -> str:
    match _get_value_type(parameter):
        case UserProvidedValueType.FLOAT:
            if re.fullmatch(r'-?([1-9]\d*|0)(\.\d+)?', raw_value) is None or raw_value == "-0":
                raise ValueError()
        case UserProvidedValueType.BOOLEAN:
            if raw_value in ("t", "true", "y", "yes"):
                return 'true'
            elif raw_value in ("f", "false", "n", "no"):
                return 'false'
            else:
                raise ValueError()
        case UserProvidedValueType.INTEGER:
            if re.fullmatch(r'(-?[1-9]\d*|0)', raw_value) is None:
                raise ValueError()
        case UserProvidedValueType.NATURAL:
            if re.fullmatch(r'[1-9]\d*', raw_value) is None:
                raise ValueError()
        case UserProvidedValueType.NON_EMPTY_STRING:
            if raw_value == '':
                raise ValueError()
        case UserProvidedValueType.NON_NEGATIVE_FLOAT:
            if re.fullmatch(r'([1-9]\d*|0)(\.\d+)?', raw_value) is None:
                raise ValueError()
        case UserProvidedValueType.POSITIVE_FLOAT:
            if re.fullmatch(r'([1-9]\d*(\.\d+)?|0\.\d+)', raw_value) is None:
                raise ValueError()
        case UserProvidedValueType.NON_NEGATIVE_INTEGER:
            if re.fullmatch(r'[1-9]\d*|0', raw_value) is None:
                raise ValueError()

    return raw_value


def enlist() -> dict[str, str]:
    return {key: data["description"] for key, data in CONTENT.items()}


def validate() -> None:
    schema = load_data_json('schemas/parameters')
    jsonschema.validate(CONTENT, schema)

    for parameter_id in ParameterID:
        assert parameter_id.value in CONTENT, f"Parameter ID {parameter_id.value} is present in the code, but missing in config"

    for key, value in CONTENT.items():
        assert key in ParameterID, f"Parameter ID {key} is present in the config, but missing in code"
        assert value["value_type"] in UserProvidedValueType, f"Unknown value type {value["value_type"]} is assigned to the parameter {key} in the config"
