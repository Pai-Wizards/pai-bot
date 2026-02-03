from io import BytesIO
import logging
import os
import asyncio
from urllib.parse import urlparse, quote_plus

import aiohttp
from PIL import Image

logger = logging.getLogger("bot_logger")

VALID_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff"}
MIN_IMAGE_SIZE_BYTES = 10 * 1024
PROBLEM_DOMAINS = {"instagram.com", "lookaside.instagram.com"}


def is_valid_image_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        path = parsed.path
        if "." in path:
            ext = path.rsplit(".", 1)[-1].lower()
            return ext in VALID_EXTENSIONS
        return False
    except Exception:
        return False


def is_problem_domain(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        return any(dom in host for dom in PROBLEM_DOMAINS)
    except Exception:
        return False


async def verify_image_accessibility(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 3,
    semaphore: asyncio.Semaphore | None = None,
) -> bool:
    async def _inner() -> bool:
        return await _verify_image_lightweight(session, url, timeout=timeout)

    if semaphore is not None:
        async with semaphore:
            return await _inner()
    return await _inner()


async def _verify_image_lightweight(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 3,
) -> bool:
    if is_problem_domain(url):
        logger.debug("Ignorando domínio problemático em URL: %s", url)
        return False

    try:
        async with session.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            ssl=False,
        ) as head_resp:
            status = head_resp.status
            if status == 200:
                ct = head_resp.headers.get("Content-Type", "").lower()
                cl = head_resp.headers.get("Content-Length")

                if not ct.startswith("image/"):
                    logger.debug("HEAD rejeitado por Content-Type (%s): %s", ct, url)
                    return False

                if cl is not None:
                    try:
                        size = int(cl)
                        if size < MIN_IMAGE_SIZE_BYTES:
                            logger.debug(
                                "HEAD rejeitado por Content-Length (%d < %d): %s",
                                size,
                                MIN_IMAGE_SIZE_BYTES,
                                url,
                            )
                            return False
                    except ValueError:
                        logger.debug("Content-Length inválido em HEAD: %s", cl)

                return True

            if status in (403, 405):
                logger.debug("HEAD não suportado (%d), tentando GET parcial: %s", status, url)
                return await _verify_with_partial_get(session, url, timeout)

            logger.debug("HEAD retornou status %d para %s", status, url)
            return False
    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        logger.debug("Falha em HEAD para %s: %s", url, type(e).__name__)
        return False
    except Exception as e:
        logger.debug("Erro inesperado em HEAD para %s: %s", url, type(e).__name__)
        return False


async def _verify_with_partial_get(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 3,
) -> bool:
    headers = {"Range": "bytes=0-4095"}
    try:
        async with session.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            ssl=False,
            headers=headers,
        ) as resp:
            if resp.status not in (200, 206):
                logger.debug("GET parcial status %d para %s", resp.status, url)
                return False

            ct = resp.headers.get("Content-Type", "").lower()
            if not ct.startswith("image/"):
                logger.debug("GET parcial rejeitado por Content-Type (%s): %s", ct, url)
                return False

            chunk = await resp.content.read(4096)
            if not chunk or len(chunk) < 2048:
                logger.debug("GET parcial retornou chunk muito pequeno (%d bytes): %s", len(chunk), url)
                return False

            try:
                img = Image.open(BytesIO(chunk))
                img.load()
            except Exception as e:
                logger.debug("Chunk inicial não parece uma imagem válida (%s): %s", type(e).__name__, url)
                return False

            return True

    except (asyncio.TimeoutError, aiohttp.ClientError) as e:
        logger.debug("Falha em GET parcial para %s: %s", url, type(e).__name__)
        return False
    except Exception as e:
        logger.debug("Erro inesperado em GET parcial para %s: %s", url, type(e).__name__)
        return False


async def validate_cors_and_format(session: aiohttp.ClientSession, url: str, timeout: int = 5) -> bool:
    try:
        async with session.get(url, timeout=timeout, allow_redirects=True, ssl=False) as resp:
            if resp.status != 200:
                return False

            content = await resp.read()
            if not content:
                return False

            try:
                img = Image.open(BytesIO(content))
                img.load()
                fmt = (img.format or "").upper()
            except Exception as e:
                logger.debug("Formato de imagem inválido em %s: %s", url, type(e).__name__)
                return False

            ct = resp.headers.get("Content-Type", "").lower()
            if not ct.startswith("image/"):
                logger.debug("Content-Type inválido: %s", ct)
                return False

            parsed = urlparse(url)
            path = parsed.path or ""
            ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""

            if fmt == "BMP":
                if ext in ("jpg", "jpeg") or "jpeg" in ct or "jpg" in ct:
                    logger.debug("Rejeitando imagem BMP servida como JPEG/JPG: %s", url)
                    return False

            return True
    except (asyncio.TimeoutError, aiohttp.ClientError):
        return False
    except Exception as e:
        logger.debug("Erro ao validar CORS e formato %s: %s", url, type(e).__name__)
        return False


async def filter_valid_images(
    session: aiohttp.ClientSession,
    items: list,
    semaphore: asyncio.Semaphore | None = None,
) -> list:
    candidates: list[dict] = []
    for item in items:
        link = item.get("link")
        title = item.get("title", "Sem título")
        display = item.get("displayLink", "").lower()

        if any(dom in display for dom in PROBLEM_DOMAINS):
            continue

        if not link or not is_valid_image_url(link):
            continue

        candidates.append({"title": title, "link": link, "item": item})

    if not candidates:
        return []

    if semaphore is None:
        semaphore = asyncio.Semaphore(5)

    verification_tasks = [
        _verify_item(session, item, semaphore) for item in candidates
    ]

    results = await asyncio.gather(*verification_tasks, return_exceptions=False)
    return [r for r in results if r is not None]


async def _verify_item(
    session: aiohttp.ClientSession,
    item: dict,
    semaphore: asyncio.Semaphore,
):
    link = item["link"]

    if not await verify_image_accessibility(session, link, semaphore=semaphore):
        return None

    if not await validate_cors_and_format(session, link, timeout=5):
        logger.debug("Imagem rejeitada por CORS ou formato inválido: %s", link)
        return None

    return {"title": item["title"], "link": link}


def build_google_cse_url(api_key: str, cx: str, query: str, num: int, start: int) -> str:
    return (
        "https://www.googleapis.com/customsearch/v1"
        f"?key={quote_plus(api_key)}"
        f"&cx={quote_plus(cx)}"
        "&searchType=image"
        f"&q={quote_plus(query)}"
        f"&num={num}"
        f"&start={start}"
        "&imgSize=large"
    )


async def handle_spelling_correction(data: dict, query: str, corrected_query_used: bool) -> tuple:
    if corrected_query_used:
        return query, corrected_query_used, False

    spelling = data.get("spelling", {})
    corrected = spelling.get("correctedQuery")

    if corrected and corrected.lower() != query.lower():
        logger.info("Google sugeriu correção: '%s' → '%s'", query, corrected)
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
                            if resp.status == 429:
                                wait_time = retry_delay * (2 ** retries)
                                logger.warning("Rate limited (429). Aguardando %ss antes de retry...", wait_time)
                                await asyncio.sleep(wait_time)
                                retries += 1
                                continue

                            if resp.status != 200:
                                logger.error("Google CSE status %s", resp.status)
                                break

                            data = await resp.json()

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

                            await asyncio.sleep(0.5)
                            break

                    except asyncio.TimeoutError:
                        logger.warning(
                            "Timeout na requisição. Retry %s/%s", retries + 1, max_retries
                        )
                        retries += 1
                        if retries < max_retries:
                            await asyncio.sleep(retry_delay)
                    except Exception as e:
                        logger.error("Erro na requisição Google: %s", e)
                        break

                if retries >= max_retries:
                    logger.error("Máximo de retries atingido. Abortando busca.")
                    break

    except Exception as e:
        logger.error("Erro ao buscar imagens via Google CSE: %s", e)

    return results


async def search_images(query, max_results=30):
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")

    if api_key and cx:
        try:
            imgs = await search_images_google(query, max_results=max_results)
            if imgs:
                return imgs
        except Exception as e:
            logger.info("Google search failed: %s", e)
    return None
