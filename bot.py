import asyncio
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import config_loader as cl, settings

bot_logger = logging.getLogger("bot_logger")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

config_file = cl.load_config()
configs_list = cl.get_configs(config_file)
almoco_frases_list = cl.create_almoco_config(config_file)

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot.configs_list = configs_list
bot.almoco_list = almoco_frases_list

COGS = ["cogs.commands", "cogs.events", "cogs.tasks"]


async def load_extensions(bot):
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            bot_logger.info(f"Carregado cog: {cog}")
        except Exception as e:
            bot_logger.error(f"Falha ao carregar cog {cog}: {e}", exc_info=True)


@bot.event
async def on_ready():
    bot_logger.info(f"Bot online como {bot.user}")


async def main():
    await load_extensions(bot)
    bot_logger.info("Iniciando bot...")
    await bot.start(settings.TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        bot_logger.warning("Bot foi interrompido pelo usuário (Ctrl+C). Desconectando...")
        asyncio.run(bot.close())
    except Exception as e:
        bot_logger.critical(f"Ocorreu um erro inesperado: {e}", exc_info=True)