import asyncio
import json
import logging
from datetime import datetime
from aiohttp import web

logger = logging.getLogger("bot_logger")


class NotificationServer:
    """Servidor HTTP para receber notificações e enviar para Discord."""

    def __init__(self, bot, host: str, port: int, channel_id: int):
        self.bot = bot  # Instância do bot Discord
        self.host = host
        self.port = port
        self.channel_id = channel_id  # ID do canal onde enviar notificações
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """Configura rotas do servidor."""
        self.app.router.add_post("/event", self.handle_event)
        self.app.router.add_get("/health", self.health_check)

    async def handle_event(self, request: web.Request) -> web.Response:
        """
        Processa notificação de evento e envia para Discord.

        Payload:
        {
            "streamer": "nome_streamer",
            "status": online/offline (string) ou true/false (boolean),
            "timestamp": "2026-02-01T12:00:00Z"
        }
        """
        try:
            # Parse e valida JSON
            data = await request.json()

            streamer = data.get("streamer")
            status_raw = data.get("status")
            timestamp = data.get("timestamp")

            # Validação de campos obrigatórios
            if streamer is None or status_raw is None or timestamp is None:
                logger.warning(f"Evento inválido: campos faltando - {data}")
                return web.json_response(
                    {"error": "Campos obrigatórios: streamer, status, timestamp"},
                    status=400
                )

            # Validação de tipo do streamer
            if not isinstance(streamer, str):
                logger.warning(f"Evento inválido: streamer deve ser string - {data}")
                return web.json_response(
                    {"error": "Tipo inválido: streamer deve ser string"},
                    status=400
                )

            # Normaliza status para boolean (aceita boolean ou string "online"/"offline")
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

            # Log do evento
            status_text = "ONLINE" if status else "OFFLINE"
            logger.info(f"[NOTIF] Streamer: {streamer} | Status: {status_text} | TS: {timestamp}")

            # Envia para Discord
            asyncio.create_task(self._send_to_discord(streamer, status, timestamp))

            # Resposta rápida
            return web.json_response({"success": True}, status=200)

        except json.JSONDecodeError:
            logger.warning("Payload não é JSON válido")
            return web.json_response({"error": "JSON inválido"}, status=400)
        except Exception as e:
            logger.error(f"Erro ao processar evento: {e}", exc_info=True)
            return web.json_response({"error": "Erro interno"}, status=500)

    async def _send_to_discord(self, streamer: str, status: bool, timestamp: str):
        """Envia notificação para canal Discord usando o bot."""
        if not self.channel_id:
            logger.warning("Canal Discord não configurado - evento não será enviado")
            logger.info("Configure NOTIFICATION_CHANNEL_ID no arquivo .env")
            return

        try:
            # Busca o canal
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"❌ Canal {self.channel_id} não encontrado")
                return

            # Formata mensagem
            status_emoji = "🟢" if status else "🔴"
            status_text = "está ONLINE" if status else "ficou OFFLINE"

            # Converte timestamp ISO 8601 para formato legível
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%d/%m/%Y %H:%M:%S UTC")
            except:
                time_str = timestamp

            # Cria embed para mensagem visual
            import discord
            embed = discord.Embed(
                title=f"{status_emoji} {streamer} {status_text}",
                color=discord.Color.green() if status else discord.Color.red(),
                timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            )
            embed.add_field(name="Streamer", value=streamer, inline=True)
            embed.add_field(name="Status", value="Online 🟢" if status else "Offline 🔴", inline=True)
            embed.set_footer(text="Notificação automática")

            # se status offline, adiciona adicionar texto apos o embed e marcar um usuário
            if not status:
                embed.description = f"<@481275285132673044> pode ir dormir agora"

            # Envia mensagem para o canal
            await channel.send(embed=embed)
            logger.info(f"✅ Notificação enviada ao Discord: {streamer} - {status_text}")

        except Exception as e:
            logger.error(f"Erro ao enviar para Discord: {e}", exc_info=True)

    async def health_check(self, request: web.Request) -> web.Response:
        """Endpoint de health check."""
        return web.json_response({"status": "ok"}, status=200)

    async def start(self):
        """Inicia o servidor HTTP."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"HTTP Server rodando em http://{self.host}:{self.port}")
        logger.info(f"Endpoint: POST http://{self.host}:{self.port}/event")
        return runner
