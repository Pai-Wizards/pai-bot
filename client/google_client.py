import logging
import os
import asyncio
from urllib.parse import urlparse, quote_plus

import aiohttp

logger = logging.getLogger("bot_logger")

VALID_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'svg'}


def is_valid_image_url(url: str) -> bool:
    """Verifica se a URL termina com uma extensão de imagem válida."""
    try:
        parsed = urlparse(url)
        path = parsed.path

        if '.' in path:
            ext = path.rsplit('.', 1)[-1].lower()
            return ext in VALID_EXTENSIONS

        return False
    except Exception:
        return False


async def verify_image_accessibility(session: aiohttp.ClientSession, url: str, timeout: int = 3, semaphore: asyncio.Semaphore = None) -> bool:
    """
    Verifica se a URL é acessível e retorna uma imagem válida.
    Usa Semaphore para limitar concorrência.
    """
    if semaphore:
        async with semaphore:
            return await _verify_with_timeout(session, url, timeout)
    else:
        return await _verify_with_timeout(session, url, timeout)


async def _verify_with_timeout(session: aiohttp.ClientSession, url: str, timeout: int) -> bool:
    """Helper para verificação com timeout"""
    try:
        async with session.head(url, timeout=timeout, allow_redirects=True, ssl=False) as head_resp:
            if head_resp.status == 200:
                ct = head_resp.headers.get('Content-Type', '').lower()
                return ct.startswith('image/')
            return False
    except (asyncio.TimeoutError, aiohttp.ClientError):
        return False
    except Exception as e:
        logger.debug(f"Erro ao verificar {url}: {type(e).__name__}")
        return False


async def filter_valid_images(session: aiohttp.ClientSession, items: list, semaphore: asyncio.Semaphore = None) -> list:
    """
    Filtra uma lista de itens Google CSE em paralelo com Semaphore.
    Retorna lista de dicts com 'title' e 'link'
    """
    # Pré-filtrar por extensão (rápido) antes de fazer HEAD requests
    candidates = []
    for item in items:
        link = item.get("link")
        title = item.get("title", "Sem título")
        display = item.get("displayLink", "").lower()

        # Ignorar Instagram
        if "instagram.com" in display or "lookaside.instagram.com" in display:
            continue

        if not link or not is_valid_image_url(link):
            continue

        candidates.append({"title": title, "link": link, "item": item})

    # Criar Semaphore se não foi fornecido (máx 5 requisições simultâneas)
    if semaphore is None:
        semaphore = asyncio.Semaphore(5)

    # Verificar acessibilidade em paralelo
    verification_tasks = [
        _verify_item(session, item, semaphore) for item in candidates
    ]

    results = await asyncio.gather(*verification_tasks, return_exceptions=False)
    return [r for r in results if r is not None]


async def _verify_item(session: aiohttp.ClientSession, item: dict, semaphore: asyncio.Semaphore):
    """Verifica um item e retorna dict com título/link ou None"""
    if await verify_image_accessibility(session, item["link"], semaphore=semaphore):
        return {"title": item["title"], "link": item["link"]}
    return None


def build_google_cse_url(api_key: str, cx: str, query: str, num: int, start: int) -> str:
    """Constrói a URL da API Google Custom Search."""
    return (
        f"https://www.googleapis.com/customsearch/v1"
        f"?key={quote_plus(api_key)}&cx={quote_plus(cx)}&searchType=image"
        f"&q={quote_plus(query)}&num={num}&start={start}"
    )


async def handle_spelling_correction(data: dict, query: str, corrected_query_used: bool) -> tuple:
    """
    Verifica se Google sugeriu correção de ortografia.
    Retorna (novo_query, corrected_query_used_flag, deve_continuar)
    """
    if corrected_query_used:
        return query, corrected_query_used, False

    spelling = data.get("spelling", {})
    corrected = spelling.get("correctedQuery")

    if corrected and corrected.lower() != query.lower():
        logger.info(f"Google sugeriu correção: '{query}' → '{corrected}'")
        return corrected, True, True

    return query, corrected_query_used, False


async def search_images_google(query, max_results=30):
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")
    if not api_key or not cx:
        raise RuntimeError("GOOGLE_API_KEY e GOOGLE_CX são necessários para search_images_google")

    results = []
    per_request = 10
    start = 1
    corrected_query_used = False
    semaphore = asyncio.Semaphore(5)

    try:
        async with aiohttp.ClientSession() as session:
            while len(results) < max_results:
                to_request = min(per_request, max_results - len(results))
                url = build_google_cse_url(api_key, cx, query, to_request, start)

                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.error(f"Google CSE status {resp.status}")
                        break

                    data = await resp.json()

                    # Verificar correção de ortografia
                    query, corrected_query_used, should_continue = await handle_spelling_correction(
                        data, query, corrected_query_used
                    )
                    if should_continue:
                        start = 1
                        continue

                    items = data.get("items", [])
                    if not items:
                        break

                    valid_images = await filter_valid_images(session, items, semaphore)
                    results.extend(valid_images)

                    start += len(items)
                    if len(items) < to_request:
                        break

    except Exception as e:
        logger.error(f"Erro ao buscar imagens via Google CSE: {e}")

    return results


async def search_images(query, max_results=30):
    """Busca imagens: tenta Google CSE se possível, senão retorna None."""
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")

    if api_key and cx:
        try:
            imgs = await search_images_google(query, max_results=max_results)
            if imgs:
                return imgs
        except Exception as e:
            logger.info(f"Google search failed: {e}")
    return None
