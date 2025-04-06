import asyncio
from datetime import datetime
from random import choice

import discord
import requests
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands

from utils.http import fetch_mdn_description, fetch_http_dog_image, logger, xingar
from utils.takes import load_takes_json, days_since_last_take, save_takes_json
import config.settings

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
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Você não está em um canal de voz.")
            return

        voice_channel = ctx.author.voice.channel

        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(voice_channel)
        else:
            await voice_channel.connect()

        await ctx.send(f'Conectado ao canal de voz: {voice_channel.name}')

    @commands.command()
    async def love(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("Eu não estou conectado a um canal de voz.")
            return

        if ctx.author.voice is None or ctx.author.voice.channel != ctx.voice_client.channel:
            await ctx.send("Você precisa estar no mesmo canal de voz que eu.")
            return

        mp3_path = f"{config.settings.IMG_PATH}audio.mp3"

        try:
            source = FFmpegPCMAudio(mp3_path)
            source = PCMVolumeTransformer(source)
            source.volume = 0.4

            def after_playback(error):
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()
                if error:
                    print(f'Erro: {error}')
                else:
                    print('Reprodução finalizada corretamente.')

            ctx.voice_client.play(source, after=after_playback)
            await ctx.send(f'Love {ctx.author.mention}!')
        except Exception as e:
            await ctx.send(f'Ocorreu um erro ao tentar tocar o áudio: {e}')

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

            #data mensagem
            msg_date_year = referenced_message.created_at.strftime("%Y")
            conteudo = referenced_message.content
            autor_id = referenced_message.author.mention
            canal_nome = ctx.channel.name
            servidor_nome = ctx.guild.name
            #data no formato 25 set. 2019.
            data_formatada = datetime.now().strftime("%d %b. %Y")
            mensagem_url = referenced_message.jump_url

            citacao = (
                f"{conteudo} ({autor_id}, 2025)\n\n"
                f"{autor_id}. **Mensagem em [{canal_nome}]**, 2025.\n"
                f"*{servidor_nome}*. Discord, {msg_date_year}. Disponível em: [{mensagem_url}]\n"
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
    async def javascript(self, ctx):
        img_path = config.settings.IMG_PATH + "javascript.png"
        try:
            with open(img_path, "rb") as image_file:
                await ctx.send(file=discord.File(image_file))
        except Exception as e:
            logger.error(f"Erro ao enviar imagem de alerta: {e}")


    @commands.command()
    async def trigger(self, ctx):
        response = "Triggers disponíveis:\n"
        for config_instance in self.bot.configs_list:
            response += f"{config_instance['name']}\n"
        await ctx.send(response)

    @commands.command()
    async def words(self, ctx, trigger_name):
        response = "Triggers words disponíveis:\n"
        for config_instance in self.bot.configs_list.get("configs_list", []):
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
    
    @commands.command(description="HTTP Cat")
    async def cat(self, ctx, http_code):
        image_url = f'https://http.cat/{http_code}.jpg'

        try:
            if requests.get(image_url).status_code != 200:
                await ctx.send("nao tem gatiho pra esse codigo")
                return
            embed = discord.Embed(description=f"HTTP Cat {http_code}")
            embed.set_image(url=image_url)
            await ctx.message.reply(embed=embed)
        except Exception as e:
            logger.info(f"Erro ao buscar dados: {e}")
            await ctx.send("ih rapaz, deu ruim")

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
        if ctx.message.reference:
            referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if referenced_message.author.bot:
                await ctx.invoke(self.javascript)
                return
            palavrao = await xingar()
            await ctx.send(f" {referenced_message.author.mention} { palavrao}")
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

    @commands.command(name="dizer")
    async def dizer(self, ctx, *, mensagem: str = None):
        if not mensagem and not ctx.message.reference:
            await ctx.send("Dizer o que?")
            return

        if not mensagem and ctx.message.reference:
            try:
                mensagem_marcada = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                mensagem = mensagem_marcada.content
            except:
                await ctx.send("Dizer o que?")
                return

        await asyncio.sleep(5)
        await ctx.send(mensagem)



async def setup(bot):
    await bot.add_cog(Commands(bot))
