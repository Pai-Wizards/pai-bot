from discord.ext.commands import command

from clients.image_search.duck_client import search_images as search_images_duck
from clients.image_search.google_client import search_images
from cogs import AutoCog
from logger import get_logger
from ui.image_paginator import ImagePaginator

log = get_logger(__name__)


class Image(AutoCog):

    def __init__(self, bot):
        self.bot = bot

    @command(name="google", aliases=["img", "image"])
    async def google_images(self, ctx, *, query: str = None):
        """Busca imagens na internet"""
        if not query and not ctx.message.reference:
            await ctx.invoke(self.bot.get_command("javascript"))
            return

        if ctx.message.reference:
            query = ctx.message.reference.resolved.content.strip()


        local_search_engine = "Google"

        try:
            async with ctx.typing():
                results = await search_images(query, max_results=10)
                log.info(f"Resultados obtidos do Google para '{query}'")
        except Exception as e:
            log.error(f"Erro na busca de imagens: {e}")
            await ctx.send("Nao deu")
            return

        if not results:
            try:
                log.info("Utilizando fallback DuckDuckGo para busca de imagens")
                local_search_engine = "DuckDuckGo (fallback)"
                results = await search_images_duck(query, max_results=20)
            except Exception as e:
                log.error(f"Erro na busca DuckDuckGo: {e}")
                await ctx.send("To naum 😿 reclama com o google")
                return

            if not results:
                await ctx.send("To naum 😿 reclama com o google")
                return

        view = ImagePaginator(results, query, ctx, timeout=300, search_engine=local_search_engine)
        view.update_button_states()

        embed = view.build_embed()
        sent = await ctx.send(embed=embed, view=view)
        view.message = sent

    @command(name="duck")
    async def duck_images(self, ctx, *, query: str = None):
        """Busca imagens usando DuckDuckGo"""
        if not query and not ctx.message.reference:
            await ctx.invoke(self.bot.get_command("javascript"))
            return

        if ctx.message.reference:
            query = ctx.message.reference.resolved.content.strip()

        try:
            async with ctx.typing():
                results = await search_images_duck(query, max_results=20)
        except Exception as e:
            log.error(f"Erro na busca DuckDuckGo: {e}")
            await ctx.send("Nao deu")
            return

        if not results:
            await ctx.send("To naum 😿 reclama com o duckduckgo")
            return

        view = ImagePaginator(
            results,
            query,
            ctx,
            search_engine="DuckDuckGo"
        )
        view.update_button_states()

        embed = view.build_embed()
        sent = await ctx.send(embed=embed, view=view)
        view.message = sent