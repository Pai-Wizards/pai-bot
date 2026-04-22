import re
from datetime import datetime

import discord
from discord.ext.commands import command, Bot

from cogs import AutoCog
from config.constants import settings
from logger import get_logger

log = get_logger(__name__)


class Quotations(AutoCog):

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def _limpar_citar(texto: str) -> str:
        return re.sub(r"!citar(?:\s*\d+)?", "", texto, flags=re.IGNORECASE).strip()

    @command(name="citar", aliases=["quote"])
    async def citar(self, ctx, qtd: int = 1):
        """Cita a mensagem referenciada no canal de citações."""
        if not ctx.message.reference:
            await ctx.send("Nao consigo 😿", delete_after=10)
            return

        try:
            referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            if referenced_message.author.bot:
                await ctx.send("Nao sei 😿", delete_after=10)
                return

            if not referenced_message.content.strip():
                await ctx.send("Nao consigo 😿", delete_after=10)
                return

            conteudo_total = []

            conteudo_limpo = self._limpar_citar(referenced_message.content)  # ← fix 2a
            if conteudo_limpo:
                conteudo_total.append(conteudo_limpo)

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
                        break
                    if not msg.content.strip():
                        continue

                    conteudo_limpo = self._limpar_citar(msg.content)  # ← fix 2b
                    if not conteudo_limpo:
                        continue

                    conteudo_total.append(conteudo_limpo)

                    if len(conteudo_total) >= qtd:
                        break

            texto_citacao = " ".join(conteudo_total)

            if not texto_citacao:
                await ctx.send("Nao encontrei conteúdo válido para citar. 😿", delete_after=10)
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

            canal_destino = self.bot.get_channel(settings.citation)
            if not canal_destino:
                await ctx.send("Não consegui encontrar o canal de citação. 😿", delete_after=1)
                return

            await canal_destino.send(citacao)

        except discord.NotFound:
            return
        except discord.Forbidden:
            return
        except discord.HTTPException:
            return


async def setup(bot: Bot) -> None:
    await bot.add_cog(Quotations(bot))
