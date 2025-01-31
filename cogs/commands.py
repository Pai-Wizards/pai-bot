from datetime import datetime
from random import choice

import discord
from discord.ext import commands

from utils.http import fetch_mdn_description, fetch_http_dog_image
from utils.takes import load_takes_json, days_since_last_take, save_takes_json


async def generic_take(ctx, take_type: str):
    data = load_takes_json()

    if take_type not in data:
        data[take_type] = {
            "last_take": None,
            "record": 0,
            "total": 0
        }

    take_data = data[take_type]
    last_take = take_data["last_take"]
    current_days = days_since_last_take(last_take) if last_take else 0

    if current_days > take_data["record"]:
        take_data["record"] = current_days

    take_data["last_take"] = datetime.now().isoformat()
    take_data["total"] += 1
    save_takes_json(data)

    await ctx.send(
        f"ESTAMOS A 0 DIAS SEM {take_type.upper()}. \n"
        f"NOSSO RECORDE É DE {take_data['record']} DIAS! \n"
        f"TOTAL DE {take_type.upper()}: {take_data['total']}"
    )


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def citar(self, ctx):
        if not ctx.message.reference:
            await ctx.send("Nao consigo", delete_after=10)
            return

        try:
            referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            if referenced_message.author.bot:
                await ctx.send("Nao sei", delete_after=10)
                return

            if not referenced_message.content.strip():
                await ctx.send("Nao consigo", delete_after=10)
                return

            conteudo = referenced_message.content
            canal_nome = ctx.channel.name
            servidor_nome = ctx.guild.name
            data_formatada = datetime.now().strftime("%Y")
            mensagem_url = referenced_message.jump_url

            citacao = (
                f"{conteudo} (@{ctx.message.author.mention}, 2025)\n\n"
                f"{ctx.message.author.mention}. **Mensagem em [{canal_nome}]**, 2025.\n"
                f"*{servidor_nome}*. Discord, {data_formatada}. Disponível em: [{mensagem_url}]\n"
                f"Acesso em: {data_formatada}."
            )

            await ctx.send(citacao)

        except discord.NotFound:
            return
            # await ctx.send("Não foi possível encontrar a mensagem referenciada.", delete_after=10)
        except discord.Forbidden:
            return
            # await ctx.send("Não tenho permissão para acessar essa mensagem.", delete_after=10)
        except discord.HTTPException:
            return
            # await ctx.send("Ocorreu um erro ao recuperar a mensagem.", delete_after=10)


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
    async def dog(self, ctx, dog):
        description, url, image_url = await fetch_http_dog_image(dog, True)
        if not url or not description:
            await ctx.send("ih rapaz, deu ruim")
        embed = discord.Embed(description=description)

        embed.set_image(url=image_url)
        await ctx.message.reply(embed=embed)

    @commands.command()
    async def http(self, ctx, http):
        description, url = await fetch_mdn_description(http)
        if not description:
            description, url, image_url = await fetch_http_dog_image(http, False)
            if not url or not description:
                await ctx.send("ih rapaz, deu ruim")
            embed = discord.Embed(description=description)

            embed.set_image(url=image_url)
            await ctx.message.reply(embed=embed)
        else:
            await ctx.send(f"{description}\n{url}")

    @commands.command()
    async def ping(self, ctx):
        time = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! {time}ms")

    @commands.command()
    async def take(self, ctx):
        data = load_takes_json()

        response = "STATUS DOS TAKES:\n"

        for take_type, take_data in data.items():
            if not isinstance(take_data, dict):
                continue

            days = days_since_last_take(take_data["last_take"]) if take_data["last_take"] else "N/A"
            record = take_data["record"]
            total = take_data["total"]

            response += (
                f"\n{take_type.upper()}:\n"
                f" - Dias sem: {days}\n"
                f" - Recorde: {record} dias\n"
                f" - Total: {total}\n"
            )

        await ctx.send(response)

    @commands.command()
    async def takemerda(self, ctx):
        await generic_take(ctx, "take merda")

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
        await generic_take(ctx, "pillfoda")

    @commands.command(name="taxado")
    async def taxado(self, ctx):
        await generic_take(ctx, "taxado")


async def setup(bot):
    await bot.add_cog(Commands(bot))
