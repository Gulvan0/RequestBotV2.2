import jsonschema

from globalconf import CONFIG
from util.identifiers import RouteID
from util.io import load_data_json


CONTENT = load_data_json('routes')


def get_default_channel_id(route_id: RouteID) -> int:
    return CONTENT[route_id.value][CONFIG.stage.value]


def get_description(route_id: RouteID) -> str:
    return CONTENT[route_id.value]["description"]


def enlist() -> dict[str, str]:
    return {key: data["description"] for key, data in CONTENT.items()}


def validate() -> None:
    schema = load_data_json('schemas/routes')
    jsonschema.validate(CONTENT, schema)

    for route_id in RouteID:
        assert route_id.value in CONTENT, f"Route ID {route_id.value} is present in the code, but missing in config"

    for key, value in CONTENT.items():
        assert key in RouteID, f"Route ID {key} is present in the config, but missing in code"
