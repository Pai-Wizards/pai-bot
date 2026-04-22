from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    model_config = {
        'env_file': '.env',
        'case_sensitive': False,
        'extra': 'allow',
    }

    # Discord
    adm_id: int = Field(default=0, description="ID do administrador")
    announce_channel_id: int = Field(default=0, description="ID do canal de anúncios")
    img_path: str = Field(default="", description="Caminho para os assets de imagem")
    token: str = Field(description="Token do bot Discord")
    cooldown: int = Field(default=120, description="Cooldown em segundos")
    citation: int = Field(default=0, description="ID para citações")
    notification_channel_id: int = Field(default=0, description="ID do canal de notificações")
    user_id: int = Field(default=0, description="ID do usuário")

    # Servidor HTTP para notificações
    http_server_host: str = Field(default="0.0.0.0", description="Host do servidor HTTP")
    http_server_port: int = Field(default=8081, description="Porta do servidor HTTP")

    # Twitch
    twitch_client_id: Optional[str] = Field(default=None, description="Twitch Client ID")
    twitch_client_secret: Optional[str] = Field(default=None, description="Twitch Client Secret")
    twitch_eventsub_callback: Optional[str] = Field(default=None, description="URL de callback do Twitch EventSub")

    # Arquivos de configuração
    takes_file: str = Field(default="take.json", description="Arquivo JSON para armazenar dados de takes")
    config_file: str = Field(default="pai_config.json", description="Arquivo JSON com configurações do bot")


# Instância singleton global
settings = Settings()

TAKES_FILE = settings.takes_file
CONFIG_FILE = settings.config_file


NEGATIVE_REPLIES = (
    "Nao achei 😿",
)