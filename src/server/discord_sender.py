import asyncio

import discord

from clients.generic.http import get_timestamp
from clients.twitch.twitch_client import TwitchClient
from logger import get_logger
from .embed_builder import build_embed

log = get_logger(__name__)


async def send_to_discord(
    bot: discord.Client,
    channel_id: int,
    streamer: str,
    status: bool,
    timestamp: str,
) -> None:
    """Send a notification to Discord.

    Args:
        bot: Discord bot instance
        channel_id: Target Discord channel ID
        streamer: Streamer name
        status: True if online, False if offline
        timestamp: ISO format timestamp
    """
    if not channel_id:
        log.warning("Canal Discord não configurado - evento não será enviado")
        log.info("Configure NOTIFICATION_CHANNEL_ID no arquivo .env")
        return

    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            log.error(f"❌ Canal {channel_id} não encontrado")
            return

        status_text = "está ONLINE" if status else "ficou OFFLINE"

        try:
            time_str = get_timestamp()
        except Exception:
            time_str = timestamp

        # Fetch Twitch user images
        images = None
        try:
            twitch_client = TwitchClient()
            loop = asyncio.get_running_loop()
            images = await loop.run_in_executor(None, twitch_client.get_user, streamer)
        except Exception as e:
            log.warning(f"Não foi possível obter imagens do Twitch para '{streamer}': {e}")

        profile_img = None
        offline_img = None
        if images:
            profile_img = images.get("profile_image_url")
            offline_img = images.get("offline_image_url")

        # Build embed
        embed = build_embed(streamer, status, timestamp, profile_img, offline_img)
        embed.set_footer(text=f"Notificação automática • {time_str}")

        await channel.send(embed=embed)
        log.info(f"✅ Notificação enviada ao Discord: {streamer} - {status_text}")

    except Exception as e:
        log.error(f"Erro ao enviar para Discord: {e}", exc_info=True)

