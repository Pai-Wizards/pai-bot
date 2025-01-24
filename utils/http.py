import html
import re

import requests


async def fetch_http_dog_image(http, flag):
    json_url = f'https://http.dog/{http}.json'
    image_jpg = f'https://http.dog/{http}.jpg'
    url = f'https://http.dog/{http}'

    try:
        # Tentar obter o JSON
        response = requests.get(json_url)
        if response.status_code == 200:
            data = response.json()
            title = data.get("title", "Título não encontrado")
            description = title if flag else "nao achei no mdn"
            return description, url, image_jpg
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")

    return None, None, None


async def fetch_mdn_description(http):
    url = f'https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Status/{http}'
    response = requests.get(url)

    if response.status_code == 200:
        match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']\s*/?>',
                          response.content.decode('utf-8', errors='ignore'))
        if match:
            description = match.group(1)
            return html.unescape(description), url
    return None, url


async def fetch_generic_description(http, base_url, pattern):
    url = f'{base_url}{http}'
    response = requests.get(url)

    if response.status_code == 200:
        match = re.search(pattern, response.content.decode('utf-8', errors='ignore'))
        if match:
            description = match.group(1)
            return html.unescape(description), url
    return None, url
