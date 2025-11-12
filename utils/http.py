import html
import re

import aiohttp
import logging

logger = logging.getLogger("bot_logger")


async def fetch_http_dog_image(http, flag):
    json_url = f'https://http.dog/{http}.json'
    image_jpg = f'https://http.dog/{http}.jpg'
    url = f'https://http.dog/{http}'

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(json_url) as response:
                if response.status == 200:
                    data = await response.json()
                    title = data.get("title", "Título não encontrado")
                    description = title if flag else "nao achei no mdn"
                    return description, url, image_jpg
    except Exception as e:
        logger.info(f"Erro ao buscar dados: {e}")

    return None, None, None


async def fetch_mdn_description(http):
    url = f'https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Status/{http}'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']\s*/?>',
                                      content)
                    if match:
                        description = match.group(1)
                        return html.unescape(description), url
    except Exception as e:
        logger.info(f"Erro ao buscar descrição MDN: {e}")
    
    return None, url


async def fetch_generic_description(http, base_url, pattern):
    url = f'{base_url}{http}'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    match = re.search(pattern, content)
                    if match:
                        description = match.group(1)
                        return html.unescape(description), url
    except Exception as e:
        logger.info(f"Erro ao buscar descrição genérica: {e}")
    
    return None, url

async def xingar():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://xinga-me.appspot.com/api") as response:
                data = await response.json()
                return data.get("xingamento")
    except Exception as e:
        logger.error(f"Erro ao buscar xingamento: {e}")
        return None
