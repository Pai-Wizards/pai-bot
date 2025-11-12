import datetime
import random
import re
import logging
from collections import defaultdict
from io import BytesIO

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
        # Cache for compiled regex patterns
        self.keyword_regex_cache = {}
        # Cache for images to avoid repeated disk I/O
        self.image_cache = {}
        # Preload commonly used images
        self._preload_images()
        # Precompile regex patterns
        self._precompile_regex_patterns()

    def _preload_images(self):
        """Preload images into memory to avoid disk I/O in hot paths."""
        images_to_preload = ["delete.jpg"]
        
        # Add images from configs
        for config_instance in self.bot.configs_list.get("configs_list", []):
            if config_instance["enabled"] and config_instance["image_name"]:
                images_to_preload.append(config_instance["image_name"])
        
        for image_name in set(images_to_preload):
            img_path = config.settings.IMG_PATH + image_name
            try:
                with open(img_path, "rb") as f:
                    self.image_cache[image_name] = BytesIO(f.read())
                logger.info(f"Preloaded image: {image_name}")
            except Exception as e:
                logger.warning(f"Failed to preload image {image_name}: {e}")

    def _precompile_regex_patterns(self):
        """Precompile regex patterns to avoid recompilation on every message."""
        for config_instance in self.bot.configs_list.get("configs_list", []):
            if config_instance["enabled"]:
                keywords_regex = r"\b(?:{})\b".format("|".join(config_instance["keywords"]))
                self.keyword_regex_cache[config_instance["name"]] = re.compile(keywords_regex, re.IGNORECASE)
                logger.info(f"Precompiled regex for: {config_instance['name']}")

    def _get_cached_image(self, image_name):
        """Get image from cache or load from disk as fallback."""
        if image_name in self.image_cache:
            # Reset position to beginning for reuse
            self.image_cache[image_name].seek(0)
            return self.image_cache[image_name]
        
        # Fallback to loading from disk
        img_path = config.settings.IMG_PATH + image_name
        try:
            with open(img_path, "rb") as f:
                data = BytesIO(f.read())
                self.image_cache[image_name] = data
                return data
        except Exception as e:
            logger.error(f"Failed to load image {image_name}: {e}")
            return None

    @commands.Cog.listener()
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
                image_data = self._get_cached_image("delete.jpg")
                if image_data:
                    logger.info(f"Enviando imagem delete.jpg devido a deleção excessiva de mensagens por {message.author} no canal {message.channel.name}")
                    self.deleted_messages[user_id].clear()
                    alert_channel = message.channel
                    await alert_channel.send(f"{message.author.mention}  Começou com deletepill", file=discord.File(image_data, filename="delete.jpg"), delete_after=10)
                else:
                    logger.error("Erro ao carregar imagem de alerta do cache")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or message.content.startswith("!"):
            return

        if "@everyone" in message.content or "@here" in message.content:
            logger.warning(f"Menção inválida por {message.author} em {message.guild}")
            return

        for config_instance in self.bot.configs_list.get("configs_list", []):
            if config_instance["enabled"]:
                # Use precompiled regex from cache
                pattern = self.keyword_regex_cache.get(config_instance["name"])
                if pattern and pattern.search(message.content.lower()) and not on_cooldown(message.author.id, self.bot.configs_list["cooldown"]):
                    image_data = self._get_cached_image(config_instance["image_name"])
                    if image_data:
                        logger.info(f"Palavra-chave detectada: {config_instance['name']} no canal {message.channel.name}")
                        await message.reply(config_instance["custom_message"], file=discord.File(image_data, filename=config_instance["image_name"]))
                    else:
                        logger.error(f"Erro ao carregar imagem associada à palavra-chave: {config_instance['image_name']}")
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
