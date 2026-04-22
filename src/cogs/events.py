import datetime
import random
import re
from collections import defaultdict

import discord
from discord.ext.commands import Cog

from clients.generic.http import xingar
from cogs import AutoCog
from config.constants import settings
from logger import get_logger
from utils.cooldown import on_cooldown

logger = get_logger(__name__)


def flood_msg_check():
    return random.randint(1, 11) == 1


class Events(AutoCog):
    def __init__(self, bot):
        self.bot = bot
        self.deleted_messages = defaultdict(list)

    @Cog.listener()
    async def on_message_delete(self, message):
        if isinstance(message.channel, discord.TextChannel):
            user_id = message.author.id
            now = datetime.datetime.now()

            if message.author == self.bot.user:
                return

            self.deleted_messages[user_id].append(now)

            self.deleted_messages[user_id] = [
                timestamp for timestamp in self.deleted_messages[user_id] if now - timestamp < datetime.timedelta(minutes=1)
            ]

            if len(self.deleted_messages[user_id]) >= 3:
                img_path = settings.img_path + "delete.jpg"
                try:
                    with open(img_path, "rb") as image_file:
                        logger.info("Enviando imagem %s devido a deleção excessiva de mensagens por %s no canal %s", img_path, message.author, message.channel.name)
                        self.deleted_messages[user_id].clear()
                        alert_channel = message.channel
                        await alert_channel.send(f"{message.author.mention}  Começou com deletepill", file=discord.File(image_file), delete_after=10)
                except Exception as e:
                    logger.error("Erro ao enviar imagem de alerta: %s", e)

    @Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or message.content.startswith("!"):
            return

        if "@everyone" in message.content or "@here" in message.content:
            logger.warning("Menção inválida por %s em %s", message.author, message.guild)
            return

        for config_instance in self.bot.configs_list.get("configs_list", []):
            if config_instance["enabled"]:
                keywords_regex = r"\b(?:{})\b".format("|".join(config_instance["keywords"]))
                if re.search(keywords_regex, message.content.lower()) and not on_cooldown(message.author.id, self.bot.configs_list["cooldown"]):
                    img_path = settings.img_path + config_instance["image_name"]
                    try:
                        with open(img_path, "rb") as image_file:
                            logger.info("Palavra-chave detectada: %s no canal %s", config_instance['name'], message.channel.name)
                            await message.reply(config_instance["custom_message"], file=discord.File(image_file))
                    except Exception as e:
                        logger.error("Erro ao enviar imagem associada à palavra-chave: %s", e)
                    return

        if self.bot.user.mentioned_in(message):
            logger.info("Bot mencionado por %s no canal %s", message.author, message.channel.name)

            if random.random() < 0.9:
                return

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
