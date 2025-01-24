from discord.ext import tasks, commands
import os

from utils.takes import load_takes_json, days_since_last_take, save_takes_json


class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not self.check_record.is_running():
            self.check_record.start()

    @tasks.loop(hours=12)
    async def check_record(self):
        print("Executando task check_record")
        channel_id = int(os.getenv("ANNOUNCE_CHANNEL_ID", "0"))
        if channel_id == 0:
            return

        data = load_takes_json()
        days = days_since_last_take(data["last_take"])
        record = data["record"]

        if days > record:
            data["record"] = days
            save_takes_json(data)

            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(
                    f"🎉 NOVO RECORDE DE {days} DIAS SEM TAKE MERDA! 🎉\n"
                    f"COLABORE PARA MELHORAR ESSE INDICE!"
                )

    @check_record.before_loop
    async def before_check_record(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Tasks(bot))
