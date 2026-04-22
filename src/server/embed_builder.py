from datetime import datetime

import discord

from config.constants import settings


def build_embed(
    streamer: str,
    status: bool,
    timestamp: str,
    profile_img: str | None = None,
    offline_img: str | None = None,
) -> discord.Embed:
    """Build a Discord embed for the streamer notification.

    Args:
        streamer: Streamer name
        status: True if online, False if offline
        timestamp: ISO format timestamp
        profile_img: Profile image URL
        offline_img: Offline image URL

    Returns:
        discord.Embed object
    """
    status_emoji = "🟢" if status else "🔴"
    status_text = "está ONLINE" if status else "ficou OFFLINE"

    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except Exception:
        dt = None

    streamer_url = f"https://twitch.tv/{streamer}"

    embed = discord.Embed(
        title=f"{status_emoji} {streamer} {status_text}",
        color=discord.Color.green() if status else discord.Color.red(),
        timestamp=dt,
        url=streamer_url,
    )
    embed.add_field(name="Streamer", value=streamer, inline=True)
    embed.add_field(name="Status", value="Online 🟢" if status else "Offline 🔴", inline=True)
    embed.add_field(name="Link", value=streamer_url, inline=False)

    if profile_img:
        embed.set_thumbnail(url=profile_img)

    if not status:
        image_to_use = offline_img or profile_img
        if image_to_use:
            try:
                embed.set_image(url=image_to_use)
            except Exception:
                pass

        embed.description = f"<@{settings.user_id}> もう寝ていいよ、レップ！"

    return embed

