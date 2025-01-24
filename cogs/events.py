import os
import re

import aiohttp
import discord
import numpy as np
from discord.ext import commands

from utils.cooldown import on_cooldown


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def flood_msg_check(self):
        return np.random.randint(1, 11) == 1

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.content.startswith("!"):
            return
        if "@everyone" in message.content or "@here" in message.content:
            print("@everyone ou @here")
            return

        for config_instance in self.bot.configs_list.get("configs_list", []):
            if config_instance["enabled"]:
                keywords_regex = r"\b(?:{})\b".format("|".join(config_instance["keywords"]))
                if re.search(keywords_regex, message.content.lower()) and not on_cooldown(message.author.id,
                                                                                          self.bot.configs_list[
                                                                                              "cooldown"]):
                    img_path = os.getenv("IMG_PATH", "") + config_instance["image_name"]
                    print("Palavra-chave encontrada: {config_instance['name']}")
                    with open(img_path, "rb") as image_file:
                        print(f"Enviando imagem {img_path}")
                        await message.reply(config_instance["custom_message"], file=discord.File(image_file))
                    return

        if self.bot.user.mentioned_in(message):
            print("Bot mencionado")
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
                await message.reply(np.random.choice(responses))
            elif self.flood_msg_check():
                await message.reply("para de floodar seu desgraçado")

        await self.bot.process_commands(message)


async def setup(bot):
    await bot.add_cog(Events(bot))


async def xingar():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://xinga-me.appspot.com/api") as response:
            return (await response.json())["xingamento"]
