import json
import os
from pathlib import Path

import discord

import config.constants
from logger import get_logger

log = get_logger(__name__)

# Diretório de configurações (config/ está no mesmo nível de src/)
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def load_config():
    config_path = CONFIG_DIR / config.constants.CONFIG_FILE
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as file:
            log.info("Arquivo de configuração encontrado em '%s'", config_path)
            return json.load(file)
    else:
        log.error("Arquivo de configuração não encontrado em '%s'", config_path)
        raise FileNotFoundError(f"Arquivo de configuração não encontrado em '{config_path}'")


def create_almoco_config(config):
    almoco_frases = config.get("almoco_frases", {})
    return {
        "frases_almoco": almoco_frases.get("frases_almoco", []),
        "frases_almoco_no_jantar": almoco_frases.get("frases_almoco_no_jantar", []),
        "frases_almoco_madrugada": almoco_frases.get("frases_almoco_madrugada", []),
        "frases_padrao": almoco_frases.get("frases_padrao", [])
    }


media_commands_path = CONFIG_DIR / "media_commands.json"
with open(media_commands_path, "r", encoding="utf-8") as f:
    MEDIA_COMMANDS = json.load(f)


def register_media_commands(self):
    for cmd_name, cmd_data in MEDIA_COMMANDS.items():
        log.info("Registrando comando de mídia: %s -> %s", cmd_name, cmd_data['file'])

        async def _command_template(ctx, file_name=cmd_data["file"]):
            img_path = os.path.join(config.constants.settings.img_path, file_name)
            try:
                with open(img_path, "rb") as f:
                    await ctx.send(file=discord.File(f))
            except Exception as e:
                log.error("Erro ao enviar arquivo (%s): %s", file_name, e)
                await ctx.send(f"Não consegui enviar {cmd_name}")

        self.bot.command(name=cmd_name)(_command_template)


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
