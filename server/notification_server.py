import asyncio
import json
import logging
from datetime import datetime
from aiohttp import web
import discord
import config.settings
from client.twitch_client import TwitchClient

logger = logging.getLogger("bot_logger")


class NotificationServer:

    def __init__(self, bot, host: str, port: int, channel_id: int):
        self.bot = bot
        self.host = host
        self.port = port
        self.channel_id = channel_id
        self.app = web.Application()
        self._setup_routes()

        # instancia TwitchClient com credenciais do settings (se existirem)
        self.twitch = TwitchClient(
            getattr(config.settings, "TWITCH_CLIENT_ID", None),
            getattr(config.settings, "TWITCH_CLIENT_SECRET", None),
        )

    def _setup_routes(self):
        self.app.router.add_post("/event", self.handle_event)
        self.app.router.add_get("/health", self.health_check)

    async def handle_event(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()

            streamer = data.get("streamer")
            status_raw = data.get("status")
            timestamp = data.get("timestamp")

            if streamer is None or status_raw is None or timestamp is None:
                logger.warning(f"Evento inválido: campos faltando - {data}")
                return web.json_response(
                    {"error": "Campos obrigatórios: streamer, status, timestamp"},
                    status=400
                )

            if not isinstance(streamer, str):
                logger.warning(f"Evento inválido: streamer deve ser string - {data}")
                return web.json_response(
                    {"error": "Tipo inválido: streamer deve ser string"},
                    status=400
                )

            if isinstance(status_raw, bool):
                status = status_raw
            elif isinstance(status_raw, str):
                status_lower = status_raw.lower()
                if status_lower == "online":
                    status = True
                elif status_lower == "offline":
                    status = False
                else:
                    logger.warning(f"Evento inválido: status deve ser 'online'/'offline' ou true/false - {data}")
                    return web.json_response(
                        {"error": "Tipo inválido: status deve ser boolean (true/false) ou string ('online'/'offline')"},
                        status=400
                    )
            else:
                logger.warning(f"Evento inválido: tipo de status não suportado - {data}")
                return web.json_response(
                    {"error": "Tipo inválido: status deve ser boolean ou string"},
                    status=400
                )

            status_text = "ONLINE" if status else "OFFLINE"
            logger.info(f"[NOTIF] Streamer: {streamer} | Status: {status_text} | TS: {timestamp}")

            asyncio.create_task(self._send_to_discord(streamer, status, timestamp))

            return web.json_response({"success": True}, status=200)

        except json.JSONDecodeError:
            logger.warning("Payload não é JSON válido")
            return web.json_response({"error": "JSON inválido"}, status=400)
        except Exception as e:
            logger.error(f"Erro ao processar evento: {e}", exc_info=True)
            return web.json_response({"error": "Erro interno"}, status=500)

    async def _send_to_discord(self, streamer: str, status: bool, timestamp: str):
        if not self.channel_id:
            logger.warning("Canal Discord não configurado - evento não será enviado")
            logger.info("Configure NOTIFICATION_CHANNEL_ID no arquivo .env")
            return

        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"❌ Canal {self.channel_id} não encontrado")
                return

            status_emoji = "🟢" if status else "🔴"
            status_text = "está ONLINE" if status else "ficou OFFLINE"

            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%d/%m/%Y %H:%M:%S UTC")
            except Exception:
                time_str = timestamp
                dt = None

            images = None
            try:
                loop = asyncio.get_running_loop()
                images = await loop.run_in_executor(None, self.twitch.get_user_images, streamer)
            except Exception as e:
                logger.warning(f"Não foi possível obter imagens do Twitch para '{streamer}': {e}")

            profile_img = None
            offline_img = None
            if images:
                profile_img = images.get("profile_image_url")
                offline_img = images.get("offline_image_url")

            embed = discord.Embed(
                title=f"{status_emoji} {streamer} {status_text}",
                color=discord.Color.green() if status else discord.Color.red(),
                timestamp=dt,
            )
            embed.add_field(name="Streamer", value=streamer, inline=True)
            embed.add_field(name="Status", value="Online 🟢" if status else "Offline 🔴", inline=True)
            embed.set_footer(text=f"Notificação automática • {time_str}")

            if profile_img:
                embed.set_thumbnail(url=profile_img)

            if not status:
                image_to_use = offline_img or profile_img
                if image_to_use:
                    try:
                        embed.set_image(url=image_to_use)
                    except Exception as e:
                        logger.warning(f"Falha ao definir imagem no embed para '{streamer}': {e}")

                embed.description = f"<@{config.settings.USER_ID}> pode ir dormir agora"

            await channel.send(embed=embed)
            logger.info(f"✅ Notificação enviada ao Discord: {streamer} - {status_text}")

        except Exception as e:
            logger.error(f"Erro ao enviar para Discord: {e}", exc_info=True)

    async def health_check(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"}, status=200)

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"HTTP Server rodando em http://{self.host}:{self.port}")
        return runner
