import json
import os

import config.settings


def load_config():
    if os.path.exists("pai_config.json"):
        with open(config.settings.CONFIG_FILE, "r") as file:
            print("Arquivo de configuração 'pai_config.json' encontrado.")
            return json.load(file)
    else:
        print("Arquivo de configuração 'pai_config.json' não encontrado.")
        raise FileNotFoundError("Arquivo de configuração 'pai_config.json' não encontrado.")



def create_almoco_config(config):
    almoco_frases = config.get("almoco_frases", {})
    return {
        "frases_almoco": almoco_frases.get("frases_almoco", []),
        "frases_almoco_no_jantar": almoco_frases.get("frases_almoco_no_jantar", []),
        "frases_almoco_madrugada": almoco_frases.get("frases_almoco_madrugada", []),
        "frases_padrao": almoco_frases.get("frases_padrao", [])
    }


def get_configs(config):
    configurations = config.get("configs", [])
    cooldown = config.get("cooldown", 0)
    return {
        "configs_list": [
            {
                "name": cfg.get("name", ""),
                "enabled": cfg.get("enabled", False),
                "keywords": cfg.get("keywords", []),
                "image_name": cfg.get("image_name", ""),
                "custom_message": cfg.get("custom_message", ""),
            }
            for cfg in configurations
        ],
        "cooldown": cooldown
    }
