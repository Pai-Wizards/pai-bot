import json
import os
import random
import logging

from discord.ext import commands, tasks
import config.settings

logger = logging.getLogger("bot_logger")

STATE_FILE = "daily_citation_state.json"


def load_last_citation():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("last_message_id")
    except Exception as e:
        logger.error("Erro ao carregar estado: %s", e)
        return None


def save_last_citation(message_id: int):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_message_id": message_id}, f)
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

        last_id = load_last_citation()

        chosen = None
        count = 0

        async for msg in source_channel.history(limit=None):
            if not msg.author.bot:
                continue
            if not msg.content or not msg.content.strip():
                continue
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
        save_last_citation(chosen.id)

        logger.info(
            "Citação enviada (msg_id=%s, total_validas=%d)",
            chosen.id,
            count
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
