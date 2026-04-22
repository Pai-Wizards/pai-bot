import asyncio
import json

from aiohttp import web

from logger import get_logger
from .discord_sender import send_to_discord

log = get_logger(__name__)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "ok"}, status=200)


def _validate_event_data(data: dict) -> tuple[bool, dict, str | None, bool | None]:
    """Validate event data and return (is_valid, event_data, error_msg, status_value).

    Args:
        data: Event data from request

    Returns:
        Tuple of (is_valid, event_data, error_msg, status_value)
    """
    streamer = data.get("streamer")
    status_raw = data.get("status")
    timestamp = data.get("timestamp")

    if streamer is None or status_raw is None or timestamp is None:
        log.warning(f"Evento inválido: campos faltando - {data}")
        return False, None, "Campos obrigatórios: streamer, status, timestamp", None

    if not isinstance(streamer, str):
        log.warning(f"Evento inválido: streamer deve ser string - {data}")
        return False, None, "Tipo inválido: streamer deve ser string", None

    if isinstance(status_raw, bool):
        status = status_raw
    elif isinstance(status_raw, str):
        status_lower = status_raw.lower()
        if status_lower == "online":
            status = True
        elif status_lower == "offline":
            status = False
        else:
            log.warning(f"Evento inválido: status deve ser 'online'/'offline' ou true/false - {data}")
            return (
                False,
                None,
                "Tipo inválido: status deve ser boolean (true/false) ou string ('online'/'offline')",
                None,
            )
    else:
        log.warning(f"Evento inválido: tipo de status não suportado - {data}")
        return False, None, "Tipo inválido: status deve ser boolean ou string", None

    return True, {"streamer": streamer, "status": status, "timestamp": timestamp}, None, status


async def handle_event(request: web.Request, bot, channel_id: int) -> web.Response:
    """Handle incoming stream status events.

    Args:
        request: aiohttp Request object
        bot: Discord bot instance
        channel_id: Discord channel ID for notifications

    Returns:
        JSON response
    """
    try:
        data = await request.json()
        is_valid, event_data, error_msg, status = _validate_event_data(data)

        if not is_valid:
            return web.json_response({"error": error_msg}, status=400)

        streamer = event_data["streamer"]
        timestamp = event_data["timestamp"]
        status_text = "ONLINE" if status else "OFFLINE"
        log.info(f"[NOTIF] Streamer: {streamer} | Status: {status_text} | TS: {timestamp}")

        asyncio.create_task(send_to_discord(bot, channel_id, streamer, status, timestamp))

        return web.json_response({"success": True}, status=200)

    except json.JSONDecodeError:
        log.warning("Payload não é JSON válido")
        return web.json_response({"error": "JSON inválido"}, status=400)
    except Exception as e:
        log.error(f"Erro ao processar evento: {e}", exc_info=True)
        return web.json_response({"error": "Erro interno"}, status=500)

