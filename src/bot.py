import asyncio
import locale
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv
from cogs import AutoCog
from logger import get_logger


src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

env_path = src_path.parent / '.env'
load_dotenv(env_path)

os.chdir(src_path.parent)

from config import loader as cl
from config.constants import settings
from server import NotificationServer


logger = get_logger(__name__)

locale.setlocale(locale.LC_TIME, "pt_BR.utf8")

config_file = cl.load_config()
configs_list = cl.get_configs(config_file)
almoco_frases_list = cl.create_almoco_config(config_file)


intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

bot.configs_list = configs_list
bot.almoco_list = almoco_frases_list

notification_server = NotificationServer(
    bot=bot,
    host=settings.http_server_host,
    port=settings.http_server_port,
    channel_id=settings.notification_channel_id
)

async def load_extensions(bot_instance):
    for cog_class in AutoCog.get_registry():
        try:
            await bot_instance.add_cog(cog_class(bot_instance))
            logger.info("COG: %s carregado com sucesso", cog_class.__name__)
        except Exception as e:
            logger.error("Erro COG: %s: %s", cog_class.__name__, e, exc_info=True)

@bot.event
async def on_ready():
    logger.info("Bot online como %s", bot.user)


async def main():
    await load_extensions(bot)

    logger.info("Iniciando HTTP server para notificações...")
    http_runner = await notification_server.start()

    try:
        logger.info("Iniciando bot...")
        await bot.start(settings.token)
    except Exception as e:
        logger.error("Erro ao iniciar bot: %s", e, exc_info=True)
        await http_runner.cleanup()
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Bot foi interrompido pelo usuário (Ctrl+C). Desconectando...")
        asyncio.run(bot.close())

    except Exception as e:
        logger.critical("Ocorreu um erro inesperado: %s", e, exc_info=True)
