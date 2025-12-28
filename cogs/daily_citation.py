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
            return json.load(f).get("last_message_id")
    except Exception:
        return None


def save_last_citation(message_id: int):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_message_id": message_id}, f)

    f.close()


class DailyCitation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.daily_citation.start()

    @tasks.loop(hours=24)
    async def daily_citation(self):
        logger.info("Executando daily_citation")

        source_channel = self.bot.get_channel(int(config.settings.CITATION))
        target_channel = self.bot.get_channel(int(config.settings.ANNOUNCE_CHANNEL_ID))

        if not source_channel:
            logger.error("Canal de citações (CITATION) não encontrado")
            return

        if not target_channel:
            logger.error("Canal de anúncio (ANNOUNCE_CHANNEL_ID) não encontrado")
            return

        last_id = load_last_citation()
        messages = []

        async for msg in source_channel.history(limit=None):
            if not msg.author.bot:
                continue
            if not msg.content.strip():
                continue
            if msg.id == last_id:
                continue
            messages.append(msg)

        if not messages:
            logger.warning("Nenhuma citação válida encontrada")
            return

        chosen = random.choice(messages)
        prefix_text = (
            "━━━━━━━━━━━━━━━━━━━\n"
            "📜 **CITAÇÃO DO DIA** 📜\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
        )
        await target_channel.send(f"{prefix_text}\n{chosen.content}")
        save_last_citation(chosen.id)

    @daily_citation.before_loop
    async def before_daily_citation(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(DailyCitation(bot))
