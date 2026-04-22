import asyncio
import os

import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext.commands import command

from cogs import AutoCog
from config.constants import settings
from logger import get_logger

log = get_logger(__name__)


class Voice(AutoCog):

    def __init__(self, bot):
        self.bot = bot

    @command(name="join", description="Bot conecta ao canal de voz do usuário")
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Você não está em um canal de voz. 😿", delete_after=10)
            return

        voice_channel = ctx.author.voice.channel

        try:
            if ctx.voice_client is not None:
                await ctx.voice_client.disconnect(force=True)

            await ctx.guild.change_voice_state(channel=None)
            await asyncio.sleep(1.5)

            vc = await voice_channel.connect(timeout=20.0, reconnect=False)

            await self.bot.change_presence(
                activity=discord.Activity(
                    name="Creed - With Arms Wide Open",
                    type=discord.ActivityType.listening
                )
            )
            await ctx.send(f'Conectado ao canal de voz: {voice_channel.name}', delete_after=10)

        except discord.errors.ConnectionClosed as e:
            if e.code == 4006:
                await ctx.send("Sessão de voz inválida 😿", delete_after=15)
                if ctx.voice_client:
                    await ctx.voice_client.disconnect(force=True)
            else:
                await ctx.send(f"Erro de conexão (código {e.code}). 😿", delete_after=10)

        except asyncio.TimeoutError:
            await ctx.send("Timeout 😿", delete_after=10)

        except Exception as e:
            log.error(f"Erro ao conectar ao canal de voz: {e}", exc_info=True)
            await ctx.send("Erro inesperado. 😿", delete_after=10)

    @command(name="leave", description="Bot sai do canal de voz")
    async def leave(self, ctx):
        """Faz o bot sair do canal de voz."""
        if ctx.voice_client is None:
            await ctx.send("Não estou conectado a um canal de voz. 😿", delete_after=1)
            return
        await ctx.voice_client.disconnect()

    @command(name="love")
    async def love(self, ctx):
        """Toca o som do love"""
        if ctx.author.voice and not ctx.voice_client:
            await self.join(ctx)

        if ctx.voice_client is None:
            await ctx.send("Não estou conectado a um canal de voz. 😿", delete_after=10)
            return

        mp3_path = f"{settings.img_path}audio.mp3"

        try:
            if not os.path.exists(mp3_path):
                log.error(f"Arquivo de áudio não encontrado: {mp3_path}")
                await ctx.send(f'Arquivo de áudio não encontrado! 😿', delete_after=4)
                return

            ffmpeg_options = {
                'options': '-vn -ar 48000 -ac 2 -f s16le'
            }

            source = FFmpegPCMAudio(mp3_path, **ffmpeg_options)
            source = PCMVolumeTransformer(source, volume=0.2)

            def after_playback(error):
                if error:
                    log.error(f'Erro ao reproduzir áudio: {error}')
                else:
                    log.info('Reprodução de love finalizada corretamente.')

            ctx.voice_client.play(source, after=after_playback)
            await ctx.send(f'Love {ctx.author.mention}!', delete_after=4)
            return
        except Exception as e:
            log.error(f'Erro ao reproduzir áudio love: {e}', exc_info=True)
            await ctx.send(f'Ocorreu um erro ao tentar tocar o áudio: {e}', delete_after=4)

    @command(name="agro")
    async def agro(self, ctx):
        """Toca o som do agrochan love"""
        if ctx.author.voice and not ctx.voice_client:
            await self.join(ctx)

        if ctx.voice_client is None:
            await ctx.send("Não estou conectado a um canal de voz. 😿", delete_after=10)
            return

        mp3_path = f"{settings.img_path}agrochan-love.mp3"

        try:
            if not os.path.exists(mp3_path):
                log.error(f"Arquivo de áudio não encontrado: {mp3_path}")
                await ctx.send(f'Arquivo de áudio não encontrado! 😿', delete_after=4)
                return

            ffmpeg_options = {
                'options': '-vn -ar 48000 -ac 2 -f s16le'
            }

            source = FFmpegPCMAudio(mp3_path, **ffmpeg_options)
            source = PCMVolumeTransformer(source, volume=0.2)

            def after_playback(error):
                if error:
                    log.error(f'Erro ao reproduzir áudio agro: {error}')
                else:
                    log.info('Reprodução de agro finalizada corretamente.')

            ctx.voice_client.play(source, after=after_playback)
            await ctx.send(f'🚜 {ctx.author.mention}!', delete_after=4)
            return
        except Exception as e:
            log.error(f'Erro ao reproduzir áudio agro: {e}', exc_info=True)
            await ctx.send(f'Ocorreu um erro ao tentar tocar o áudio: {e}', delete_after=4)

    @command(name="sound")
    async def sound(self, ctx):
        """Mostra os botões de sound"""
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