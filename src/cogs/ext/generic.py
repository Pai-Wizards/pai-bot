import discord
import requests
from discord.ext.commands import command

from clients.generic.http import fetch_http_dog_image
from clients.generic.mdn_client import fetch_mdn_description
from cogs import AutoCog
from logger import get_logger

log = get_logger(__name__)


class Generic(AutoCog):

    def __init__(self, bot):
        self.bot = bot

    @command(name="dog")
    async def dog(self, ctx, dog):
        """Mostra a imagem de um código HTTP em formato de perro"""
        description, url, image_url = await fetch_http_dog_image(dog, True)
        if not url or not description:
            await ctx.send("ih rapaz, deu ruim 😿")
        embed = discord.Embed(description=description)

        embed.set_image(url=image_url)
        await ctx.message.reply(embed=embed)

    @command(name="cat")
    async def cat(self, ctx, http_code):
        """Mostra a imagem de um código HTTP em formato de gato"""
        image_url = f'https://http.cat/{http_code}.jpg'

        try:
            if requests.get(image_url).status_code != 200:
                await ctx.send("nao tem gatiho pra esse codigo 😿")
                return
            embed = discord.Embed(description=f"HTTP Cat {http_code}")
            embed.set_image(url=image_url)
            await ctx.message.reply(embed=embed)
        except Exception as e:
            log.info(f"Erro ao buscar dados: {e}")
            await ctx.send("ih rapaz, deu ruim 😿")

    @command(name="http")
    async def http(self, ctx, http):
        """Busca descrição de códigos HTTP na MDN"""
        description, url = await fetch_mdn_description(http)
        if not description:
            description, url, image_url = await fetch_http_dog_image(http, False)
            if not url or not description:
                await ctx.send("ih rapaz, deu ruim 😿")
            embed = discord.Embed(description=description)

            embed.set_image(url=image_url)
            await ctx.message.reply(embed=embed)
        else:
            await ctx.send(f"{description}\n{url}")
