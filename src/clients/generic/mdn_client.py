import html
import re

import requests


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