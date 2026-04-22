import json
from datetime import datetime
from pathlib import Path
from typing import Any

from config.constants import settings

# Diretório de configurações (config/ está no mesmo nível de src/)
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"

def load_takes_json():
    """Carrega dados de takes do arquivo JSON."""
    with open(CONFIG_DIR / settings.takes_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_takes_json(data: dict[str, Any]) -> None:
    """Salva dados de takes no arquivo JSON."""
    with open(CONFIG_DIR / settings.takes_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def days_since_last_take(last_take):
    if last_take is None:
        return 0
    last_take = datetime.fromisoformat(last_take)
    return (datetime.now() - last_take).days

