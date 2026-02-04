import json
import os
import random
import logging
from datetime import date

from discord.ext import commands, tasks
import config.settings

logger = logging.getLogger("bot_logger")

STATE_FILE = "daily_citation_state.json"


def load_state():
    """Retorna dict com keys: last_message_id (int|None) e last_date (YYYY-MM-DD|None)."""
    if not os.path.exists(STATE_FILE):
        return {"last_message_id": None, "last_date": None}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "last_message_id": data.get("last_message_id"),
                "last_date": data.get("last_date"),
            }
    except Exception as e:
        logger.error("Erro ao carregar estado: %s", e)
        return {"last_message_id": None, "last_date": None}


def save_state(message_id: int, date_str: str):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_message_id": message_id, "last_date": date_str}, f)
    except Exception as e:
        logger.error("Erro ao salvar estado: %s", e)


class DailyCitation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._task_started = False

    @commands.Cog.listener()
    async def on_ready(self):
        """Inicia a task quando o bot estiver pronto e conectado."""
        if not self._task_started:
            logger.info("Bot pronto! Iniciando task daily_citation...")
            self.daily_citation.start()
            self._task_started = True

    @tasks.loop(hours=24)
    async def daily_citation(self):
        logger.info("Executando daily_citation")

        source_channel = self.bot.get_channel(
            int(config.settings.CITATION)
        )
        target_channel = self.bot.get_channel(
            int(config.settings.ANNOUNCE_CHANNEL_ID)
        )

        if source_channel is None:
            logger.error("Canal de citações (CITATION) não encontrado")
            return

        if target_channel is None:
            logger.error("Canal de anúncio (ANNOUNCE_CHANNEL_ID) não encontrado")
            return

        state = load_state()
        today_str = date.today().isoformat()

        # Se já houver citação hoje, ignora
        if state.get("last_date") == today_str:
            logger.info("Já enviada citação hoje (%s). Ignorando execução.", today_str)
            return

        last_id = state.get("last_message_id")

        chosen = None
        count = 0

        async for msg in source_channel.history(limit=None):
            if not msg.author.bot:
                continue
            if not msg.content or not msg.content.strip():
                continue
            # evita reenviar a mensagem que foi usada anteriormente (se existir)
            if last_id is not None and msg.id == last_id:
                continue

            count += 1
            if chosen is None or random.randint(1, count) == 1:
                chosen = msg

        if chosen is None:
            logger.warning("Nenhuma citação válida encontrada")
            return

        prefix_text = (
            "━━━━━━━━━━━━━━━━━━━\n"
            "📜 **CITAÇÃO DO DIA** 📜\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
        )

        await target_channel.send(f"{prefix_text}{chosen.content}")
        save_state(chosen.id, today_str)

        logger.info(
            "Citação enviada (msg_id=%s, total_validas=%d, date=%s)",
            chosen.id,
            count,
            today_str
        )

    @daily_citation.before_loop
    async def before_daily_citation(self):
        logger.info("Aguardando bot ficar pronto antes de iniciar daily_citation...")
        await self.bot.wait_until_ready()
        logger.info("Bot pronto! Iniciando daily_citation loop...")

    def cog_unload(self):
        self.daily_citation.cancel()


async def setup(bot):
    cog = DailyCitation(bot)
    await bot.add_cog(cog)
    logger.info("Cog DailyCitation carregado (task será iniciada quando bot estiver pronto)")
