from aiohttp import web

from logger import get_logger
from .handlers import health_check, handle_event

log = get_logger(__name__)


class NotificationServer:
    """HTTP server for handling stream notifications and sending them to Discord."""

    def __init__(self, bot, host: str, port: int, channel_id: int):
        """Initialize the notification server.

        Args:
            bot: Discord bot instance
            host: Server host
            port: Server port
            channel_id: Discord channel ID for notifications
        """
        self.bot = bot
        self.host = host
        self.port = port
        self.channel_id = channel_id
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """Setup HTTP routes."""
        # Create a wrapper for handle_event that includes the bot and channel_id
        async def event_handler(request: web.Request) -> web.Response:
            return await handle_event(request, self.bot, self.channel_id)

        self.app.router.add_post("/event", event_handler)
        self.app.router.add_get("/health", health_check)

    async def start(self):
        """Start the HTTP server.

        Returns:
            web.AppRunner instance for later cleanup
        """
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        log.info(f"Servidor HTTP rodando em %s:%s" % (self.host, self.port))
        return runner

