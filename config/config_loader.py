import json
import os


def load_config():
    if os.path.exists("pai_config.json"):
        with open("pai_config.json", "r") as file:
            print("Arquivo de configuração 'pai_config.json' encontrado.")
            return json.load(file)
    else:
        print("Arquivo de configuração 'pai_config.json' não encontrado.")
        raise FileNotFoundError("Arquivo de configuração 'pai_config.json' não encontrado.")


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
