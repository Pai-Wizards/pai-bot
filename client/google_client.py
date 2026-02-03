import logging
import os
import asyncio
from urllib.parse import urlparse, quote_plus

import aiohttp
from PIL import Image
from io import BytesIO

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


async def validate_cors_and_format(session: aiohttp.ClientSession, url: str, timeout: int = 5) -> bool:
    """
    Valida CORS headers e formato real da imagem.
    Retorna True se a imagem é válida e segura para Discord embed.
    """
    try:
        async with session.get(url, timeout=timeout, allow_redirects=True, ssl=False) as resp:
            if resp.status != 200:
                return False

            content = await resp.read()
            if not content:
                return False

            # Validar formato real da imagem
            try:
                img = Image.open(BytesIO(content))
                img.verify()
            except Exception as e:
                logger.debug(f"Formato de imagem inválido em {url}: {type(e).__name__}")
                return False

            # Validar Content-Type
            ct = resp.headers.get('Content-Type', '').lower()
            if not ct.startswith('image/'):
                logger.debug(f"Content-Type inválido: {ct}")
                return False

            return True
    except (asyncio.TimeoutError, aiohttp.ClientError):
        return False
    except Exception as e:
        logger.debug(f"Erro ao validar CORS e formato {url}: {type(e).__name__}")
        return False


async def filter_valid_images(session: aiohttp.ClientSession, items: list, semaphore: asyncio.Semaphore = None) -> list:
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

    if semaphore is None:
        semaphore = asyncio.Semaphore(5)

    verification_tasks = [
        _verify_item(session, item, semaphore) for item in candidates
    ]

    results = await asyncio.gather(*verification_tasks, return_exceptions=False)
    return [r for r in results if r is not None]


async def _verify_item(session: aiohttp.ClientSession, item: dict, semaphore: asyncio.Semaphore):
    link = item["link"]

    if not await verify_image_accessibility(session, link, semaphore=semaphore):
        return None

    if not await validate_cors_and_format(session, link, timeout=5):
        logger.debug(f"Imagem rejeitada por CORS ou formato inválido: {link}")
        return None

    return {"title": item["title"], "link": link}


def build_google_cse_url(api_key: str, cx: str, query: str, num: int, start: int) -> str:
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
    max_retries = 2
    retry_delay = 2

    try:
        async with aiohttp.ClientSession() as session:
            while len(results) < max_results:
                to_request = min(per_request, max_results - len(results))
                url = build_google_cse_url(api_key, cx, query, to_request, start)

                retries = 0
                while retries < max_retries:
                    try:
                        async with session.get(url, timeout=10) as resp:
                            # Rate limiting: 429 Too Many Requests
                            if resp.status == 429:
                                wait_time = retry_delay * (2 ** retries)
                                logger.warning(f"Rate limited (429). Aguardando {wait_time}s antes de retry...")
                                await asyncio.sleep(wait_time)
                                retries += 1
                                continue

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
                                break

                            items = data.get("items", [])
                            if not items:
                                break

                            valid_images = await filter_valid_images(session, items, semaphore)
                            results.extend(valid_images)

                            start += len(items)
                            if len(items) < to_request:
                                break

                            # Aguardar um pouco entre requisições para evitar rate limiting
                            await asyncio.sleep(0.5)
                            break

                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout na requisição. Retry {retries + 1}/{max_retries}")
                        retries += 1
                        if retries < max_retries:
                            await asyncio.sleep(retry_delay)
                    except Exception as e:
                        logger.error(f"Erro na requisição Google: {e}")
                        break

                if retries >= max_retries:
                    logger.error("Máximo de retries atingido. Abortando busca.")
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
