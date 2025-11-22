import html
import re

import aiohttp
import requests
import logging
import os
import asyncio
from urllib.parse import quote_plus

# duckduckgo_search has changed APIs across versions.
# Try to import an async interface first; otherwise fall back to sync function.
try:
    from duckduckgo_search import AsyncDDGS
    _DDG_ASYNC = True
    _ddg_sync = None
except Exception:
    try:
        from duckduckgo_search import ddg_images
        _DDG_ASYNC = False
        _ddg_sync = ddg_images
    except Exception:
        _DDG_ASYNC = None
        _ddg_sync = None

logger = logging.getLogger("bot_logger")


async def fetch_http_dog_image(http, flag):
    json_url = f'https://http.dog/{http}.json'
    image_jpg = f'https://http.dog/{http}.jpg'
    url = f'https://http.dog/{http}'

    try:
        response = requests.get(json_url)
        if response.status_code == 200:
            data = response.json()
            title = data.get("title", "Título não encontrado")
            description = title if flag else "nao achei no mdn"
            return description, url, image_jpg
    except Exception as e:
        logger.info(f"Erro ao buscar dados: {e}")

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

async def xingar():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://xinga-me.appspot.com/api") as response:
            return (await response.json())["xingamento"]


async def search_images_google(query, max_results=30):
    """Busca imagens usando Google Custom Search API (assíncrono via aiohttp).

    Requer `GOOGLE_API_KEY` e `GOOGLE_CX` como variáveis de ambiente.
    Retorna lista de URLs de imagens (pode retornar vazia em caso de erro).
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")
    if not api_key or not cx:
        raise RuntimeError("GOOGLE_API_KEY e GOOGLE_CX são necessários para search_images_google")

    results = []
    per_request = 10
    start = 1

    try:
        async with aiohttp.ClientSession() as session:
            while len(results) < max_results:
                to_request = min(per_request, max_results - len(results))
                url = (
                    f"https://www.googleapis.com/customsearch/v1"
                    f"?key={quote_plus(api_key)}&cx={quote_plus(cx)}&searchType=image"
                    f"&q={quote_plus(query)}&num={to_request}&start={start}"
                )
                async with session.get(url) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(f"Google CSE returned status {resp.status}: {text}")
                        break
                    data = await resp.json()
                    items = data.get("items", [])
                    if not items:
                        break
                    for item in items:
                        link = item.get("link")
                        display = item.get("displayLink", "").lower()
                        if "instagram.com" in display or "lookaside.instagram.com" in display:
                            continue

                        # verificar se a imagem e valida status 200
                        if link:
                            try:
                                async with session.head(link, timeout=5) as head_resp:
                                    if head_resp.status != 200:
                                        continue
                            except Exception as e:
                                logger.info(f"Erro ao verificar link da imagem: {e}")
                                continue

                        if link and not item.get("mime") == "image/":
                            results.append(link)

                    start += len(items)
                    if len(items) < to_request:
                        break
    except Exception as e:
        logger.error(f"Erro ao buscar imagens via Google CSE: {e}")

    return results


async def search_images(query, max_results=30):
    """Busca imagens: tenta Google CSE (se configurado) e faz fallback para DuckDuckGo."""
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")

    if api_key and cx:
        try:
            imgs = await search_images_google(query, max_results=max_results)
            if imgs:
                return imgs
        except Exception as e:
            logger.info(f"Google search failed, falling back to DuckDuckGo: {e}")

    # Fallback para DuckDuckGo
    if _DDG_ASYNC is True:
        try:
            async with AsyncDDGS() as ddgs:
                results = await ddgs.images(query, max_results=max_results)
                return [r['image'] for r in results if 'image' in r]
        except Exception as e:
            logger.error(f"Erro ao buscar imagens (DuckDuckGo async): {e}")
            return []
    elif _DDG_ASYNC is False and _ddg_sync is not None:
        try:
            # ddg_images is synchronous; run in a thread to avoid blocking
            results = await asyncio.to_thread(_ddg_sync, query, max_results)
            out = []
            for r in results:
                if isinstance(r, dict):
                    link = r.get('image') or r.get('image_url') or r.get('thumbnail') or r.get('url')
                    if link:
                        out.append(link)
                elif isinstance(r, str):
                    out.append(r)
            return out
        except Exception as e:
            logger.error(f"Erro ao buscar imagens (DuckDuckGo sync): {e}")
            return []
    else:
        logger.error("Nenhuma implementação do duckduckgo_search disponível para fallback")
        return []

