import asyncio
import os
from collections import OrderedDict
from urllib.parse import urlparse, quote_plus

import aiohttp

from logger import get_logger

log = get_logger(__name__)

VALID_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff"}
MIN_IMAGE_SIZE_BYTES = 10 * 1024
PROBLEM_DOMAINS = {"instagram.com", "lookaside.instagram.com"}


class LimitedURLCache:
    """Cache LRU para URLs com limite de memória."""

    def __init__(self, maxsize: int = 300):
        self.cache: OrderedDict = OrderedDict()
        self.maxsize = maxsize

    def get(self, url: str) -> bool | None:
        return self.cache.get(url)

    def add(self, url: str, valid: bool) -> None:
        if url in self.cache:
            del self.cache[url]
        elif len(self.cache) >= self.maxsize:
            self.cache.popitem(last=False)
        self.cache[url] = valid


class LimitedQueryCache:
    """Cache LRU para queries de busca."""

    def __init__(self, maxsize: int = 50):
        self.cache: OrderedDict = OrderedDict()
        self.maxsize = maxsize

    def get(self, query: str) -> list | None:
        return self.cache.get(query)

    def add(self, query: str, results: list) -> None:
        if query in self.cache:
            del self.cache[query]
        elif len(self.cache) >= self.maxsize:
            self.cache.popitem(last=False)
        self.cache[query] = results


_url_cache = LimitedURLCache(maxsize=300)
_query_cache = LimitedQueryCache(maxsize=50)


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
    # Verificar cache primeiro
    cached = _url_cache.get(url)
    if cached is not None:
        return cached

    async def _inner() -> bool:
        result = await _verify_image_lightweight(session, url, timeout=timeout)
        _url_cache.add(url, result)
        return result

    if semaphore is not None:
        async with semaphore:
            return await _inner()
    return await _inner()


async def _verify_image_lightweight(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 2,
) -> bool:
    """Verifica imagem apenas com HEAD (sem GET parcial para economia de memória)."""
    if is_problem_domain(url):
        log.debug("Ignorando domínio problemático: %s", url)
        return False

    try:
        async with session.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            ssl=False,
        ) as resp:
            if resp.status != 200:
                log.debug("HEAD status %d para %s", resp.status, url)
                return False

            ct = resp.headers.get("Content-Type", "").lower()
            if not ct.startswith("image/"):
                log.debug("Content-Type inválido (%s) para %s", ct, url)
                return False

            cl = resp.headers.get("Content-Length")
            if cl is not None:
                try:
                    size = int(cl)
                    if size < MIN_IMAGE_SIZE_BYTES:
                        log.debug("Imagem muito pequena (%d bytes) para %s", size, url)
                        return False
                except ValueError:
                    pass

            return True

    except asyncio.TimeoutError:
        log.debug("Timeout em HEAD para %s", url)
        return False
    except (aiohttp.ClientError, Exception) as e:
        log.debug("Erro em HEAD para %s: %s", url, type(e).__name__)
        return False


async def filter_valid_images(
    session: aiohttp.ClientSession,
    items: list,
    max_needed: int = 30,
    semaphore: asyncio.Semaphore | None = None,
) -> list:
    """Filtra imagens válidas com lazy loading (retorna assim que tiver suficiente)."""
    if not items:
        return []

    # Pré-filtrar links válidos e domínios problemáticos
    candidates = []
    for item in items:
        link = item.get("link")
        title = item.get("title", "Sem título")
        display = item.get("displayLink", "").lower()

        if any(dom in display for dom in PROBLEM_DOMAINS):
            continue

        if not link or not is_valid_image_url(link):
            continue

        candidates.append((link, title))

    if not candidates:
        return []

    if semaphore is None:
        semaphore = asyncio.Semaphore(3)

    results = []

    # Lazy loading: verificar até conseguir max_needed resultados válidos
    for link, title in candidates:
        if len(results) >= max_needed:
            break

        if await verify_image_accessibility(session, link, timeout=2, semaphore=semaphore):
            results.append({"title": title, "link": link})

    return results




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
        log.info("Google sugeriu correção: '%s' → '%s'", query, corrected)
        return corrected, True, True

    return query, corrected_query_used, False


async def search_images_google(query, max_results=30):
    """Busca imagens com cache por query e connection pooling otimizado."""
    # Verificar cache de query primeiro
    cached_results = _query_cache.get(query)
    if cached_results is not None:
        log.info("Retornando %d imagens do cache para query: %s", len(cached_results), query)
        return cached_results

    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CX")
    if not api_key or not cx:
        raise RuntimeError("GOOGLE_API_KEY e GOOGLE_CX são necessários para search_images_google")

    results = []
    per_request = 10
    start = 1
    corrected_query_used = False
    semaphore = asyncio.Semaphore(3)
    max_retries = 2
    retry_delay = 2

    # Connection pooling otimizado
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5, ttl_dns_cache=300)

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            while len(results) < max_results:
                to_request = min(per_request, max_results - len(results))
                url = build_google_cse_url(api_key, cx, query, to_request, start)

                retries = 0
                while retries < max_retries:
                    try:
                        async with session.get(url, timeout=5) as resp:  # Timeout Google: 5s
                            if resp.status == 429:
                                wait_time = retry_delay * (2 ** retries)
                                log.warning("Rate limited. Aguardando %ds...", wait_time)
                                await asyncio.sleep(wait_time)
                                retries += 1
                                continue

                            if resp.status != 200:
                                log.error("Google CSE status %s", resp.status)
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

                            # Lazy loading: parar quando tiver suficiente
                            valid_images = await filter_valid_images(
                                session, items, max_needed=max_results - len(results), semaphore=semaphore
                            )
                            results.extend(valid_images)

                            # Parar se já temos suficiente
                            if len(results) >= max_results:
                                break

                            start += len(items)
                            if len(items) < to_request:
                                break

                            await asyncio.sleep(0.05)  # Sleep mínimo
                            break

                    except asyncio.TimeoutError:
                        log.warning("Timeout na requisição Google. Retry %s/%s", retries + 1, max_retries)
                        retries += 1
                        if retries < max_retries:
                            await asyncio.sleep(retry_delay)
                    except Exception as e:
                        log.error("Erro na requisição Google: %s", e)
                        break

                if retries >= max_retries:
                    log.error("Máximo de retries atingido.")
                    break

    except Exception as e:
        log.error("Erro ao buscar imagens via Google CSE: %s", e)

    # Cachear resultados
    if results:
        _query_cache.add(query, results)

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
            log.info("Google search failed: %s", e)
    return None
