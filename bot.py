import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import config_loader as cl

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
            print(f"Carregando cog: {cog}")
        except Exception as e:
            print(f"Falha ao carregar cog {cog}: {e}")


@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")


async def main():
    await load_extensions(bot)
    TOKEN = os.getenv("TOKEN")
    await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot foi interrompido pelo usuário (Ctrl+C). Desconectando...")
        asyncio.run(bot.close())
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")