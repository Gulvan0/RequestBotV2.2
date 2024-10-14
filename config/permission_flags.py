import jsonschema

from util.identifiers import PermissionFlagID
from util.io import load_data_json


CONTENT = load_data_json('permission_flags')


def get_description(flag_id: PermissionFlagID) -> str:
    return CONTENT[flag_id.value]["description"]


def enlist() -> dict[str, str]:
    return {key: data["description"] for key, data in CONTENT.items()}


def validate() -> None:
    schema = load_data_json('schemas/permission_flags')
    jsonschema.validate(CONTENT, schema)

    for flag_id in PermissionFlagID:
        assert flag_id.value in CONTENT, f"User flag ID {flag_id.value} is present in the code, but missing in config"

    for key, value in CONTENT.items():
        assert key in PermissionFlagID, f"User flag ID {key} is present in the config, but missing in code"