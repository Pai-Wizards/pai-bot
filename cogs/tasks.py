from discord.ext import tasks, commands
import logging
import config.settings
from utils.takes import load_takes_json, days_since_last_take, save_takes_json

logger = logging.getLogger("bot_logger")

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not self.check_record.is_running():
            self.check_record.start()

    @tasks.loop(hours=4)
    async def check_record(self):
        logger.info("Executando task check_record")
        channel_id = int(config.settings.ANNOUNCE_CHANNEL_ID)
        if channel_id == 0:
            return

        await self.handle_record(
            channel_id=channel_id,
            take_type="take merda",
            message_template=(
                "🎉 NOVO RECORDE DE {days} DIAS SEM TAKE MERDA! 🎉\n"
                "COLABORE PARA MELHORAR ESSE ÍNDICE!"
            ),
        )

    async def handle_record(self, channel_id: int, take_type: str, message_template: str):
        data = load_takes_json()

        if take_type not in data:
            return

        take_data = data[take_type]
        days = days_since_last_take(take_data["last_take"]) if take_data["last_take"] else 0
        record = take_data["record"]

        if days > record:
            take_data["record"] = days
            save_takes_json(data)

            channel = self.bot.get_channel(channel_id)
            if channel:
                message = message_template.format(days=days)
                await channel.send(message)

    @check_record.before_loop
    async def before_check_record(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Tasks(bot))
