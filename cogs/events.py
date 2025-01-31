import datetime
import random
import re
import logging
from collections import defaultdict

import discord
from discord.ext import commands

import config.settings
from utils.cooldown import on_cooldown
from utils.http import xingar

logger = logging.getLogger("bot_logger")

def flood_msg_check():
    return random.randint(1, 11) == 1


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deleted_messages = defaultdict(list)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if isinstance(message.channel, discord.TextChannel):
            user_id = message.author.id
            now = datetime.datetime.now()

            self.deleted_messages[user_id].append(now)

            self.deleted_messages[user_id] = [
                timestamp for timestamp in self.deleted_messages[user_id] if now - timestamp < datetime.timedelta(minutes=1)
            ]

            if len(self.deleted_messages[user_id]) >= 3:
                img_path = config.settings.IMG_PATH + "delete.jpg"
                try:
                    with open(img_path, "rb") as image_file:
                        logger.info(f"Enviando imagem {img_path} devido a deleção excessiva de mensagens por {message.author} no canal {message.channel.name}")
                        self.deleted_messages[user_id].clear()
                        alert_channel = message.channel
                        await alert_channel.send(f"{message.author.mention}  Começou com deletepill", file=discord.File(image_file), delete_after=10)
                except Exception as e:
                    logger.error(f"Erro ao enviar imagem de alerta: {e}")

            logger.info(f"Mensagem apagada no canal {message.channel.name} por {message.author}: {message.content}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or message.content.startswith("!"):
            return

        if "@everyone" in message.content or "@here" in message.content:
            logger.warning(f"Menção inválida por {message.author} em {message.guild}")
            return

        for config_instance in self.bot.configs_list.get("configs_list", []):
            if config_instance["enabled"]:
                keywords_regex = r"\b(?:{})\b".format("|".join(config_instance["keywords"]))
                if re.search(keywords_regex, message.content.lower()) and not on_cooldown(message.author.id, self.bot.configs_list["cooldown"]):
                    img_path = config.settings.IMG_PATH + config_instance["image_name"]
                    try:
                        with open(img_path, "rb") as image_file:
                            logger.info(f"Palavra-chave detectada: {config_instance['name']} no canal {message.channel.name}")
                            await message.reply(config_instance["custom_message"], file=discord.File(image_file))
                    except Exception as e:
                        logger.error(f"Erro ao enviar imagem associada à palavra-chave: {e}")
                    return

        if self.bot.user.mentioned_in(message):
            logger.info(f"Bot mencionado por {message.author} no canal {message.channel.name}")

            if not on_cooldown(message.author.id, self.bot.configs_list["cooldown"]):
                xingamento = await xingar()
                if xingamento:
                    await message.reply(xingamento)
                    return

                responses = [
                    "marca teu cu seu arrombado",
                    "*fui comprar cigarro, deixe seu recado*",
                    "pede pra tua mãe, to jogando truco",
                ]
                await message.reply(random.choice(responses))
            elif flood_msg_check():
                await message.reply("para de floodar seu desgraçado")

        await self.bot.process_commands(message)


async def setup(bot):
    await bot.add_cog(Events(bot))
