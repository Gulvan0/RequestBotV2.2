import jsonschema
import logging
import re
import typing as tp

from util.datatypes import Language
from util.identifiers import TextPieceID
from util.io import load_data_json, load_long_text


def __load_texts() -> dict[str, dict[str, tp.Any]]:
    content: dict[str, dict[str, tp.Any]] = load_data_json('texts')
    for text_piece in content.values():
        for lang in Language:
            template: str = text_piece[lang.value]
            if template.startswith("ext::"):
                text_piece[lang.value] = load_long_text(template.removeprefix("ext::"))
    return content


CONTENT = __load_texts()


def get_default_template(piece_id: TextPieceID, lang: Language) -> str:
    return CONTENT[piece_id.value][lang.value]  # noqa


def get_description(piece_id: TextPieceID) -> str:
    return CONTENT[piece_id.value]["description"]


def get_param_descriptions(piece_id: TextPieceID) -> dict[str, str]:
    return CONTENT[piece_id.value].get("param_descriptions", {})


def enlist() -> dict[str, str]:
    return {key: data["description"] for key, data in CONTENT.items()}


def validate() -> None:
    schema = load_data_json('schemas/texts')
    jsonschema.validate(CONTENT, schema)

    for piece_id in TextPieceID:
        assert piece_id.value in CONTENT, f"Text piece ID {piece_id.value} is present in the code, but missing in config"

    for key, value in CONTENT.items():
        assert key in TextPieceID, f"Text piece ID {key} is present in the config, but missing in code"
        described_params = set(value.get("param_descriptions", {}).keys())

        for lang in Language:
            template = value[lang.value]
            used_params = set(re.findall(r'\{([^}]+)}', template))

            not_described_params = used_params - described_params
            assert not not_described_params, f"Several params used in {lang.value} template of text piece {key} are not described in the docs: {not_described_params}"

            unused_params = described_params - used_params
            if unused_params:
                logging.warning(f'Several params of text piece {key} are unused in its {lang.value} template: {unused_params}')  # Those are tolerable, unlike non-described
