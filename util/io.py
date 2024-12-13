import json
from pathlib import Path


def load_data_json(node_name: str) -> dict:
    return json.loads(Path(f'data/{node_name}.json').read_text(encoding='utf-8'))


def load_long_text(name: str) -> str:
    return Path(f'data/long_texts/{name}.md').read_text(encoding='utf-8')