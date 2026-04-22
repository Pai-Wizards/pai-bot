import asyncio

import discord
from discord.ext.commands import command

from clients.generic.http import get_timestamp
from clients.twitch.twitch_client import TwitchClient
from cogs import AutoCog
from config.constants import settings, NEGATIVE_REPLIES
from logger import get_logger
from ui.subscriptions_paginator import SubscriptionsPaginator

twitch_client = TwitchClient()

log = get_logger(__name__)


class Twitch(AutoCog):

    def __init__(self, bot):
        self.bot = bot

    @command(name="sub", aliases=["add"])
    async def subscribe(self, ctx, *, mensagem: str = None):
        """Subscribe em um canal Twitch para notificações de live online"""
        if not mensagem:
            await ctx.send("Kd o parametro 😿 !subscribe <nome>")
            await ctx.invoke(self.bot.get_command("javascript"))
            return

        loop = asyncio.get_running_loop()

        try:
            user = await loop.run_in_executor(None, twitch_client.get_user, mensagem)
        except Exception as e:
            await ctx.send(NEGATIVE_REPLIES, delete_after=10)
            return

        if not user:
            await ctx.send(f"Nao achei 😿", delete_after=10)
            return

        broadcaster_id = user.get("id")
        if not broadcaster_id:
            await ctx.send(f"Nao achei 😿", delete_after=10)
            return

        callback = settings.twitch_eventsub_callback
        if not callback:
            log.info("TWITCH_EVENTSUB_CALLBACK não está configurado no ambiente.")
            await ctx.send(f"Nao consigo, nao ta configurado direito 😿", delete_after=10)
            return

        secret = settings.twitch_client_secret or ""

        try:
            result = await loop.run_in_executor(
                None,
                twitch_client.subscribe_eventsub,
                broadcaster_id,
                callback,
                secret)
        except Exception as e:
            log.error(f"Erro ao criar subscription: {e}", exc_info=True)
            await ctx.send(f"Nao foi possivel criar a subscription 😿")
            return

        display = user.get("display_name") or user.get("login") or broadcaster_id
        description = (user.get("description") or "").strip()
        if len(description) > 80:
            description = description[:77] + "..."
        profile = user.get("profile_image_url") or ""
        streamer_url = f"https://twitch.tv/{mensagem}"

        embed = discord.Embed(title=display, description=description, url=streamer_url, )
        if profile:
            embed.set_thumbnail(url=profile)

        status = result.get("status")
        time_str = get_timestamp()
        if status == "exists":
            embed.set_footer(text=f" 👍 Subscription já cadastrada • {time_str}")
        else:
            embed.set_footer(text=f"👍 Subscription cadastrada com sucesso • {time_str}")

        await ctx.send(embed=embed)

    @command(name="list")
    async def list(self, ctx):
        """Lista todas as subscriptions EventSub e permite navegação com botões."""
        loop = asyncio.get_running_loop()
        try:
            async with ctx.typing():
                subs_resp = await loop.run_in_executor(None, twitch_client.list_eventsub_subscriptions)
        except Exception as e:
            log.error(f"Erro ao listar subscriptions: {e}", exc_info=True)
            await ctx.send("Erro ao buscar subscriptions do Twitch 😿")
            return

        data = subs_resp.get("data", []) or []

        if not data:
            await ctx.send("Nenhuma subscription encontrada.")
            return

        # Para cada subscription, buscar dados do streamer (get_user) baseado em broadcaster_user_id
        subs_with_users = []
        for sub in data:
            broadcaster_id = sub.get("condition", {}).get("broadcaster_user_id")
            user = None
            if broadcaster_id:
                try:
                    user = await loop.run_in_executor(None, twitch_client.get_user, broadcaster_id)
                except Exception:
                    user = None
            subs_with_users.append({"sub": sub, "user": user})

        view = SubscriptionsPaginator(subs_with_users, ctx.author.id)
        view.update_button_states()

        embed = view.build_embed_for_index(0)
        sent = await ctx.send(embed=embed, view=view)
        view.message = sent
