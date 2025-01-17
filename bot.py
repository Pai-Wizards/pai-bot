import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import re
import time
import numpy as np
from datetime import datetime, timedelta

load_dotenv()

cooldowns = {}
adm_id = int(os.getenv("ADM_ID", "0"))
mod_id = []

if os.path.exists('pai_config.json'):
    with open('pai_config.json', 'r') as config_file:
        config = json.load(config_file)
else:
    print('Erro: Arquivo de configuração não encontrado.')
    exit(1)

COOLDOWN = config.get("cooldown", 120)
configurations = config.get("configs", [])
configs_list = [
    {
        "name": cfg.get("name", ""),
        "enabled": cfg.get("enabled", False),
        "keywords": cfg.get("keywords", []),
        "image_name": cfg.get("image_name", ""),
        "custom_message": cfg.get("custom_message", ""),
    }
    for cfg in configurations
]

# Função de cooldown
def on_cooldown(user_id):
    if user_id == adm_id:
        return False
    last_trigger = cooldowns.get(user_id, 0)
    if time.time() - last_trigger > COOLDOWN:
        cooldowns[user_id] = time.time()
        return False
    return True

def flood_msg_check():
    return np.random.randint(1, 11) == 1

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    try:
        await bot.tree.sync()  # Sincroniza comandos de barra
        print("Comandos slash sincronizados com sucesso!")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>Eventos: Mensagem recebida
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    if message.author.id == adm_id:
        if "modpai add" in message.content.lower():
            user_id = int(message.content.split()[-1])
            if user_id not in mod_id:
                mod_id.append(user_id)
                await message.reply(f"<@{user_id}> agora é um mod do papai")
            else:
                await message.reply("Ele já é mod seu zé ruela")
        elif "modpai remove" in message.content.lower():
            user_id = int(message.content.split()[-1])
            if user_id in mod_id:
                mod_id.remove(user_id)
                await message.reply(f"<@{user_id}> não é mais mod do papai")
            else:
                await message.reply("Ele já não era meu mod")
        elif "pai xp" in message.content.lower():
            await message.reply("+xp")

    for config_instance in configs_list:
        if config_instance["enabled"]:
            keywords_regex = r"\b(?:{})\b".format("|".join(config_instance["keywords"]))
            if re.search(keywords_regex, message.content.lower()) and not on_cooldown(message.author.id):
                img_path = os.getenv("IMG_PATH", "") + config_instance["image_name"]
                with open(img_path, "rb") as image_file:
                    await message.reply(config_instance["custom_message"], file=discord.File(image_file))
                return

    if bot.user.mentioned_in(message):
        if not on_cooldown(message.author.id):
            responses = [
                "marca teu cu seu arrombado",
                "*fui comprar cigarro, deixe seu recado*",
                "pede pra tua mãe, to jogando truco",
            ]
            await message.reply(np.random.choice(responses))
        elif flood_msg_check():
            await message.reply("para de floodar seu desgraçado")

    await bot.process_commands(message)

@bot.tree.command(name="paidocs", description="documentação do pai")
async def paidocs(interaction: discord.Interaction):
    documentation = """
**PAI BOT DOCUMENTAÇÃO**

**Comandos Prefixados (!):**
1. `trigger` - Lista todos os gatilhos disponíveis configurados no bot.
2. `words [nome_do_trigger]` - Exibe informações sobre um trigger específico, como palavras-chave e imagem associada.
3. `ping` - Retorna a latência atual do bot.
"""
    await interaction.response.send_message(documentation)

@bot.command()
async def trigger(ctx):
    response = "Triggers disponíveis:\n"
    for config_instance in configs_list:
        response += f"{config_instance['name']}\n"
    await ctx.send(response)

@bot.command()
async def words(ctx, trigger_name):
    response = "Triggers words disponíveis:\n"
    print(trigger_name)
    for config_instance in configs_list:
        if config_instance["name"] == trigger_name:
            response += f"Nome do trigger: {config_instance['name']}\n"
            response += f"Palavras-chave: {', '.join(config_instance['keywords'])}\n"
            response += f"Imagem: {config_instance['image_name']}\n"
            response += f"Mensagem: {config_instance['custom_message']}\n"
    await ctx.send(response)

@bot.command()
async def ping(ctx):
    time = round(bot.latency * 1000)
    await ctx.send('pong {}ms'.format(time))


TAKES_FILE = "take.json"

if not os.path.exists(TAKES_FILE):
    with open(TAKES_FILE, "w") as f:
        json.dump({"last_take": None, "record": 0, "total": 0}, f)

def load_takes_json():
    with open(TAKES_FILE, "r") as f:
        return json.load(f)

def save_takes_json(data):
    with open(TAKES_FILE, "w") as f:
        json.dump(data, f)

def days_since_last_take(last_take):
    if last_take is None:
        return 0

    last_take = datetime.fromisoformat(last_take)
    delta = datetime.now() - last_take
    return delta.days

@bot.command()
async def take(ctx):
    data = load_takes_json()
    days = days_since_last_take(data["last_take"])
    record = data["record"]

    if days > record:
        record = days

    await ctx.send(f"ESTAMOS A {days} DIAS SEM TAKE MERDA. \nNOSSO RECORDE É DE {record} DIAS \nTOTAL DE TAKES: {data['total']}")


@bot.command()
async def takemerda(ctx):
    data = load_takes_json()
    last_take = data["last_take"]
    current_days = days_since_last_take(last_take)

    if current_days > data["record"]:
        data["record"] = current_days

    data["last_take"] = datetime.now().isoformat()

    data["total"] += 1
    save_takes_json(data)

    await ctx.send(f"ESTAMOS A 0 DIAS SEM TAKE MERDA. \nNOSSO RECORDE É DE {data['record']} DIAS! \nTOTAL DE TAKES: {data['total']}")

TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
