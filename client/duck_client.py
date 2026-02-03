import logging
from typing import List, Dict

from duckduckgo_search import DDGS

logger = logging.getLogger("bot_logger")

VALID_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "bmp"}

def _has_valid_extension(url: str) -> bool:
    url = url.split("?", 1)[0]
    if "." not in url:
        return False
    ext = url.rsplit(".", 1)[-1].lower()
    return ext in VALID_EXTENSIONS


def _duck_search_images_sync(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    logger.info(f"Buscando imagens no DuckDuckGo para: '{query}' (max_results={max_results})")

    results: List[Dict[str, str]] = []

    try:
        with DDGS() as ddgs:
            raw_results = ddgs.images(
                keywords=query,
                region="wt-wt",
                safesearch="off",
                size=None,
                color=None,
                type_image=None,
                layout=None,
                license_image=None,
                max_results=max_results * 3,
            )

        if not raw_results:
            logger.warning(f"DuckDuckGo não retornou resultados para: {query}")
            return []

        for item in raw_results:
            # Estrutura típica do DDGS().images():
            # {
            #   "title": str,
            #   "image": "https://... .jpg",
            #   "thumbnail": "https://...",
            #   "url": "https://página-de-origem",
            #   ...
            # }
            image_url = item.get("image")
            title = item.get("title") or "Sem título"

            if not image_url:
                continue

            if not _has_valid_extension(image_url):
                continue

            results.append({"title": title, "link": image_url})

            if len(results) >= max_results:
                break

        logger.info(f"DuckDuckGo retornou {len(results)} imagens válidas para '{query}'")
        return results

    except Exception as e:
        logger.error(f"Erro ao buscar imagens com DuckDuckGo: {e}")
        return []


async def search_images_duck(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _duck_search_images_sync,
        query,
        max_results,
    )


async def duck_search_images(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    return await search_images_duck(query, max_results)
