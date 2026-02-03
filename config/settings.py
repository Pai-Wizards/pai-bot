import os

ADM_ID = int(os.getenv("ADM_ID", "0"))
ANNOUNCE_CHANNEL_ID = int(os.getenv("ANNOUNCE_CHANNEL_ID", "0"))
IMG_PATH = os.getenv("IMG_PATH", "")
TOKEN = os.getenv("TOKEN")
COOLDOWN = int(os.getenv("COOLDOWN", "120"))
CITATION = int(os.getenv("CITATION", "0"))

# Configurações do servidor HTTP para notificações
HTTP_SERVER_HOST = os.getenv("HTTP_SERVER_HOST", "0.0.0.0")
HTTP_SERVER_PORT = int(os.getenv("HTTP_SERVER_PORT", "8081"))
NOTIFICATION_CHANNEL_ID = int(os.getenv("NOTIFICATION_CHANNEL_ID", "0"))

TAKES_FILE = "take.json"
CONFIG_FILE = "pai_config.json"
