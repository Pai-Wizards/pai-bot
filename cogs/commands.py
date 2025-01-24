from datetime import datetime

import discord
from discord.ext import commands
from numpy.random import choice

from utils.http import fetch_mdn_description, fetch_http_dog_image
from utils.takes import load_takes_json, days_since_last_take, save_takes_json


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def trigger(self, ctx):
        response = "Triggers disponíveis:\n"
        for config_instance in self.bot.configs_list:
            response += f"{config_instance['name']}\n"
        await ctx.send(response)

    @commands.command()
    async def words(self, ctx, trigger_name):
        response = "Triggers words disponíveis:\n"
        for config_instance in self.bot.configs_list:
            if config_instance["name"] == trigger_name:
                response += f"Nome do trigger: {config_instance['name']}\n"
                response += f"Palavras-chave: {', '.join(config_instance['keywords'])}\n"
                response += f"Imagem: {config_instance['image_name']}\n"
                response += f"Mensagem: {config_instance['custom_message']}\n"
        await ctx.send(response)

    @commands.command()
    async def http(self, ctx, http):
        description, url = await fetch_mdn_description(http)
        if not description:
            description, url, image_url = await fetch_http_dog_image(http)
            embed = discord.Embed(description=description)

            embed.set_image(url=image_url)
            await ctx.message.reply(embed=embed)
        else:
            if not url or not description:
                await ctx.send("ih rapaz, deu ruim")
            await ctx.send(f"{description}\n{url}")

    @commands.command()
    async def ping(self, ctx):
        time = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! {time}ms")

    @commands.command()
    async def take(self, ctx):
        data = load_takes_json()
        days = days_since_last_take(data["last_take"])
        record = data["record"]

        if days > record:
            record = days

        await ctx.send(
            f"ESTAMOS A {days} DIAS SEM TAKE MERDA. \nNOSSO RECORDE É DE {record} DIAS \nTOTAL DE TAKES: {data['total']}"
        )

    @commands.command()
    async def takemerda(self, ctx):
        data = load_takes_json()
        last_take = data["last_take"]
        current_days = days_since_last_take(last_take)

        if current_days > data["record"]:
            data["record"] = current_days

        data["last_take"] = datetime.now().isoformat()
        data["total"] += 1
        save_takes_json(data)

        await ctx.send(
            f"ESTAMOS A 0 DIAS SEM TAKE MERDA. \nNOSSO RECORDE É DE {data['record']} DIAS! \nTOTAL DE TAKES: {data['total']}"
        )

    @commands.command()
    async def jahpodmussar(self, ctx):
        print("jahpodmussar commando")
        current_date = datetime.now()
        hora_atual = current_date.strftime("%H:%M")

        horario_map = {
            (11, 14): self.bot.almoco_list["frases_almoco"],
            (18, 22): self.bot.almoco_list["frases_almoco_no_jantar"],
            (23, 5): self.bot.almoco_list["frases_almoco_madrugada"],
        }
        frases_selecionadas = self.bot.almoco_list["frases_padrao"]
        for (inicio, fim), frases in horario_map.items():
            if inicio <= current_date.hour <= fim or (
                    inicio > fim and (current_date.hour >= inicio or current_date.hour <= fim)):
                frases_selecionadas = frases
                break

        frase = choice(frases_selecionadas).format(hora_atual=hora_atual)
        await ctx.send(frase)

    @commands.command(name="pillfoda")
    async def pillfoda(self, ctx):
        await ctx.send("TODO: pillfoda ta pronto nao meu patrao")

    @commands.command(name="taxado")
    async def taxado(self, ctx):
        await ctx.send("TODO: taxado ta pronto nao meu patrao")


async def setup(bot):
    await bot.add_cog(Commands(bot))
