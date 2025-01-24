import html
import re
from datetime import datetime

import requests
from discord.ext import commands
from numpy.random import choice

from utils.takes import load_takes_json, days_since_last_take, save_takes_json


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def trigger(self, ctx):
        # Verifica se o comando já foi processado
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
        response = requests.get('https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Status/' + http)

        if response.status_code == 200:
            match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']\s*/?>',
                              response.content.decode('utf-8', errors='ignore'))

            if match:
                description = match.group(1)
                decoded_description = html.unescape(description)
                await ctx.send(decoded_description + "\n\n" + response.url)
            else:
                await ctx.send("Ihh rapaz, deu ruim aqui")
        else:
            await ctx.send('Achei nada vai se tratar')

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
        current_date = datetime.now()
        hora_atual = current_date.strftime("%H:%M")

        frases_almoco = [
            "FUI AO MOSSAR",
            "Vai comer criatura 🍲",
            "Lógico que pode, vai comer! 🍲",
            "Vai logo meoooo",
            "Hoje é dia de comer cu de curioso",
        ]

        frases_almoco_no_jantar = [
            f"Almoço às {hora_atual}? Organiza essa vida! 🍴",
            f"Almoço às {hora_atual}? Depois reclama 🌙",
            f"Pensando em almoço às {hora_atual}? Tá tudo errado aí, hein! 😤",
            f"Horário de janta ({hora_atual}), e você ainda falando de almoço? Vai comer algo decente agora! 🙄",
            f"Almoço às {hora_atual}? Tá com fome é? 🍴",
        ]

        frases_almoco_madrugada = [
            f"Almoço às {hora_atual}? Vai dormir, criatura! Quem pensa nisso a essa hora? 😴",
            f"Almoço às {hora_atual}? Depois reclama que tá comendo mal! 🌌",
            f"Madrugada ({hora_atual}) é pra dormir, não pra ficar sonhando com almoço! 🛌",
            f"Você tá falando de almoço às {hora_atual}? Tá tudo bem aí? Precisa de ajuda? 🤔",
            f"Sai do Discord e vai dormir, almoço às {hora_atual} é coisa de quem não tem o que fazer! 😴",
            "Não compensa não, vai dormir! 🌙",
        ]

        frases_padrao = [
            f"Ainda não está liberado, mas tá preocupado com o almoço às {hora_atual}? Vai se organizar! 🙄",
            "Pode não, meo.",
            f"Almoço às {hora_atual}? Organize sua vida! 🕰️",
        ]

        # Determinar a resposta com base no horário
        if 11 <= current_date.hour <= 14:
            await ctx.send(choice(frases_almoco))
        elif 18 <= current_date.hour <= 22:
            await ctx.send(choice(frases_almoco_no_jantar))
        elif 23 <= current_date.hour or current_date.hour <= 5:
            await ctx.send(choice(frases_almoco_madrugada))
        else:
            await ctx.send(choice(frases_padrao))

    @commands.command(name="pillfoda")
    async def pillfoda(self, ctx):
        await ctx.send("TODO: pillfoda ta pronto nao meu patrao")

    @commands.command(name="taxado")
    async def taxado(self, ctx):
        await ctx.send("TODO: taxado ta pronto nao meu patrao")


async def setup(bot):
    await bot.add_cog(Commands(bot))
