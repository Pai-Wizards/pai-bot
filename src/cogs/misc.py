import asyncio
from datetime import datetime
from random import choice

from discord.ext.commands import command, Context

from cogs import AutoCog
from config.loader import register_media_commands
from logger import get_logger

logger = get_logger(__name__)


class Misc(AutoCog):
    def __init__(self, bot):
        self.bot = bot
        register_media_commands(self)

    @command(name="git", aliases=["github", "repo"])
    async def git (self, ctx):
        """Mostra o link do repositório GitHub do bot."""
        git_url = "https://github.com/Pai-Wizards/pai-bot"
        await ctx.send(f"**Faz um pull request aí:** {git_url}")

    @command(name="trigger", aliases=["triggers", "words"])
    async def trigger(self, ctx):
        """Mostra os triggers disponíveis"""
        response = "Triggers disponíveis:\n"
        for config_instance in self.bot.configs_list.get("configs_list", []):
            response += f"Nome do trigger: {config_instance['name']}\n"
            response += f"Palavras-chave: {', '.join(config_instance['keywords'])}\n"
            response += f"Imagem: {config_instance['image_name']}\n"
            response += f"Mensagem: {config_instance['custom_message']}\n\n"
        await ctx.send(response)

    @command(name="ping")
    async def ping(self, ctx: Context):
        """Ping Pong!"""
        time = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! {time}ms")

    @command(name="jahpodmussar", aliases=["almoco", "japodecomer"])
    async def jahpodmussar(self, ctx):
        """Responde se já pode almoçar/jantar"""
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

    @command(name="dizer")
    async def dizer(self, ctx, *, mensagem: str = None):
        """Diz a mensagem após 120 segundos"""
        if not mensagem:
            logger.info("Mensagem vazia")
            await ctx.send("Dizer o que?")
            return

        logger.info("Esperando 120 segundos para dizer a mensagem")
        await asyncio.sleep(120)
        logger.info("Dizendo mensagem")
        await ctx.send(mensagem)
        return

async def setup(bot):
    await bot.add_cog(Misc(bot))
