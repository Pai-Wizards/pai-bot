import html
import re

import requests


async def fetch_http_dog_image(http):
    image_jpg = f'https://http.dog/' + http + '.jpg'
    url = f'https://http.dog/{http}'

    description = "nao achei no mdn"
    return description, url, image_jpg


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
