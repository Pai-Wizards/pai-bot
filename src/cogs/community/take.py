from datetime import datetime

from discord.ext.commands import command, Bot

from clients.generic.http import xingar
from cogs import AutoCog
from config.take_helper import load_takes_json, days_since_last_take, save_takes_json
from logger import get_logger

log = get_logger(__name__)

async def generic_take(ctx, take_type: str):
    data = load_takes_json()

    if take_type not in data:
        data[take_type] = {
            "last_take": None,
            "record": 0,
            "total": 0
        }

    take_data = data[take_type]
    last_take = take_data["last_take"]
    current_days = days_since_last_take(last_take) if last_take else 0

    if current_days > take_data["record"]:
        take_data["record"] = current_days

    take_data["last_take"] = datetime.now().isoformat()
    take_data["total"] += 1
    save_takes_json(data)

    await ctx.send(
        f"ESTAMOS HÁ 0 DIAS SEM {take_type.upper()}. \n"
        f"NOSSO RECORDE É DE {take_data['record']} DIAS! \n"
        f"TOTAL DE {take_type.upper()}: {take_data['total']} \n"
        f"🚜 COLABORE PARA MELHORAR ESSE ÍNDICE!"
    )


class Take(AutoCog):

    def __init__(self, bot):
        self.bot = bot

    @command(name="take")
    async def take(self, ctx):
        """Mostra o status dos takes"""
        data = load_takes_json()
        response = "STATUS DOS TAKES:\n"

        for take_type, take_data in data.items():
            log.info(f"Processando take: {take_type} com dados: {take_data}")
            if not isinstance(take_data, dict):
                continue

            days = days_since_last_take(take_data["last_take"]) if take_data["last_take"] else "N/A"
            record = take_data["record"]
            total = take_data["total"]

            response += (
                f"\n{take_type.upper()}:\n"
                f" - Dias sem: {days}\n"
                f" - Recorde: {record} dias\n"
                f" - Total: {total}\n"
            )

        await ctx.send(response)

    @command(name="takemerda")
    async def takemerda(self, ctx):
        """Registra um take merda"""
        if ctx.message.reference:
            referenced_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if referenced_message.author.bot:
                await ctx.invoke(self.bot.get_command("javascript"))
                return
            palavrao = await xingar()
            await ctx.send(f" {referenced_message.author.mention} {palavrao}")
        await generic_take(ctx, "take merda")

    @command(name="pillfoda")
    async def pillfoda(self, ctx):
        """Registra um pillfoda"""
        await generic_take(ctx, "pillfoda")


async def setup(bot: Bot) -> None:
    await bot.add_cog(Take(bot))