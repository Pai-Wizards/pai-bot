import json
import logging
import os

import discord

import config.settings

logger = logging.getLogger("bot_logger")


def load_config():
    if os.path.exists("pai_config.json"):
        with open(config.settings.CONFIG_FILE, "r") as file:
            logger.info("Arquivo de configuração 'pai_config.json' encontrado.")
            return json.load(file)
    else:
        logger.error("Arquivo de configuração 'pai_config.json' não encontrado.")
        raise FileNotFoundError("Arquivo de configuração 'pai_config.json' não encontrado.")


def create_almoco_config(config):
    almoco_frases = config.get("almoco_frases", {})
    return {
        "frases_almoco": almoco_frases.get("frases_almoco", []),
        "frases_almoco_no_jantar": almoco_frases.get("frases_almoco_no_jantar", []),
        "frases_almoco_madrugada": almoco_frases.get("frases_almoco_madrugada", []),
        "frases_padrao": almoco_frases.get("frases_padrao", [])
    }


with open("media_commands.json", "r", encoding="utf-8") as f:
    MEDIA_COMMANDS = json.load(f)


def register_media_commands(self):
    for cmd_name, cmd_data in MEDIA_COMMANDS.items():
        logger.info(f"Carregando Comando: ({cmd_name})")

        async def _command_template(ctx, file_name=cmd_data["file"], description=cmd_data.get("description", "")):
            img_path = os.path.join(config.settings.IMG_PATH, file_name)
            try:
                with open(img_path, "rb") as f:
                    await ctx.send(file=discord.File(f))
            except Exception as e:
                logger.error(f"Erro ao enviar arquivo ({file_name}): {e}")
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
