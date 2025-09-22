import asyncio
import re
from datetime import datetime
from random import choice

import discord
import requests
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands

import config.settings
from config.config_loader import register_media_commands
from utils.http import fetch_mdn_description, fetch_http_dog_image, logger, xingar
from utils.takes import load_takes_json, days_since_last_take, save_takes_json


def limpar_citar(texto: str) -> str:
    return re.sub(r"!citar(?:\s*\d+)?", "", texto, flags=re.IGNORECASE).strip()


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
        f"ESTAMOS HÁ 0 DIAS SEM {take_type.upper()}. \n"
        f"NOSSO RECORDE É DE {take_data['record']} DIAS! \n"
        f"TOTAL DE {take_type.upper()}: {take_data['total']} \n"
        f"🚜 COLABORE PARA MELHORAR ESSE ÍNDICE!"
    )


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        register_media_commands(self)

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Você não está em um canal de voz.", delete_after=10)
            return

        voice_channel = ctx.author.voice.channel

        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(voice_channel)
            await self.bot.change_presence(
                activity=discord.Activity(name="With Arms Wide Open", type=discord.ActivityType.listening))
        else:
            await voice_channel.connect()
            await self.bot.change_presence(
                activity=discord.Activity(name="With Arms Wide Open", type=discord.ActivityType.listening))

        await ctx.send(f'Conectado ao canal de voz: {voice_channel.name}', delete_after=10)

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("Não estou conectado a um canal de voz.", delete_after=1)
            return
        await ctx.voice_client.disconnect()

    @commands.command()
    async def love(self, ctx):
        # se o autor esta em um canal de voz efetuar o join
        if ctx.author.voice and not ctx.voice_client:
            await self.join(ctx)

        if ctx.voice_client is None:
            await ctx.send("Eu não estou conectado a um canal de voz.", delete_after=10)
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
                    logger.info(f'Erro: {error}')
                else:
                    logger.info('Reprodução finalizada corretamente.', delete_after=10)

            ctx.voice_client.play(source, after=after_playback)
            await ctx.send(f'Love {ctx.author.mention}!', delete_after=4)
            return
        except Exception as e:
            await ctx.send(f'Ocorreu um erro ao tentar tocar o áudio: {e}', delete_after=4)

    @commands.command(name="agro")
    async def agro(self, ctx):
        # se o autor esta em um canal de voz efetuar o join
        if ctx.author.voice and not ctx.voice_client:
            await self.join(ctx)

        if ctx.voice_client is None:
            await ctx.send("Eu não estou conectado a um canal de voz.", delete_after=10)
            return

        mp3_path = f"{config.settings.IMG_PATH}agrochan-love.mp3"

        try:
            source = FFmpegPCMAudio(mp3_path)
            source = PCMVolumeTransformer(source)
            source.volume = 0.4

            def after_playback(error):
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()
                if error:
                    ctx.send(f'deu esse erro aqui: {error}', delete_after=10)
                else:
                    ctx.send('Reprodução finalizada corretamente.', delete_after=10)

            ctx.voice_client.play(source, after=after_playback)
            await ctx.send(f'🚜 {ctx.author.mention}!', delete_after=4)
            return
        except Exception as e:
            await ctx.send(f'Ocorreu um erro ao tentar tocar o áudio: {e}', delete_after=4)

    @commands.command()
    async def citar(self, ctx, qtd: int = 1):
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

            conteudo_total = []

            # Limpar e adicionar a primeira mensagem
            conteudo_limpo = limpar_citar(referenced_message.content)
            if conteudo_limpo:
                conteudo_total.append(conteudo_limpo)

            # Buscar subsequentes apenas do mesmo autor
            if qtd > 1:
                after_id = referenced_message.id
                async for msg in ctx.channel.history(
                        after=discord.Object(id=after_id),
                        limit=50,
                        oldest_first=True
                ):
                    if msg.author.bot:
                        continue
                    if msg.author.id != referenced_message.author.id:
                        continue
                    if not msg.content.strip():
                        continue

                    conteudo_limpo = limpar_citar(msg.content)
                    if not conteudo_limpo:
                        continue

                    conteudo_total.append(conteudo_limpo)

                    if len(conteudo_total) >= qtd:
                        break

            # Concatenar todas as mensagens
            texto_citacao = " ".join(conteudo_total)

            if not texto_citacao:
                await ctx.send("Nao encontrei conteúdo válido para citar.", delete_after=10)
                return

            msg_date_year = referenced_message.created_at.strftime("%Y")
            autor_id = referenced_message.author.mention
            canal_nome = ctx.channel.name
            servidor_nome = ctx.guild.name
            data_formatada = datetime.now().strftime("%d %b. %Y")
            mensagem_url = referenced_message.jump_url

            citacao = (
                f"{texto_citacao} ({autor_id}, {msg_date_year})\n\n"
                f"{autor_id}. **Mensagem em [{canal_nome}]**, {msg_date_year}.\n"
                f"*{servidor_nome}*. Discord, {msg_date_year}. Disponível em: [{mensagem_url}]\n"
                f"Acesso em: {data_formatada}."
            )

            canal_destino = self.bot.get_channel(config.settings.CITATION)
            if not canal_destino:
                await ctx.send("Não consegui encontrar o canal de citação.", delete_after=1)
                return

            await canal_destino.send(citacao)

        except discord.NotFound:
            return
        except discord.Forbidden:
            return
        except discord.HTTPException:
            return

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
                await ctx.invoke(self.bot.get_command("javascript"))
                return
            palavrao = await xingar()
            await ctx.send(f" {referenced_message.author.mention} {palavrao}")
        await generic_take(ctx, "take merda")

    @commands.command()
    async def jahpodmussar(self, ctx):
        logger.info("jahpodmussar commando")
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
        if not mensagem:
            logger.info("Mensagem vazia")
            await ctx.send("Dizer o que?")
            return

        logger.info("Esperando 5 segundos")
        await asyncio.sleep(5)
        logger.info("Dizendo mensagem")
        await ctx.send(mensagem)
        return

    @commands.command(name="sound")
    async def sound(self, ctx):
        embed = discord.Embed(title="love", description="Escolhe ai:")

        button1 = discord.ui.Button(label="❤️", style=discord.ButtonStyle.primary)
        button2 = discord.ui.Button(label="🚜", style=discord.ButtonStyle.success)

        async def button1_callback(interaction: discord.Interaction):
            await interaction.response.send_message("Você clicou no botão ❤️!", ephemeral=True)
            await self.love(ctx)

        async def button2_callback(interaction: discord.Interaction):
            await interaction.response.send_message("Você clicou no botão 🚜!", ephemeral=True)
            await self.agro(ctx)

        button1.callback = button1_callback
        button2.callback = button2_callback

        view = discord.ui.View()
        view.add_item(button1)
        view.add_item(button2)

        await ctx.send(embed=embed, view=view, delete_after=300)


async def setup(bot):
    await bot.add_cog(Commands(bot))
