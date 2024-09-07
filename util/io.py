import json
from pathlib import Path


def load_data_json(node_name: str) -> dict:
    return json.loads(Path(f'data/{node_name}.json').read_text(encoding='utf-8'))