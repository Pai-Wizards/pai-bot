"""
image_search.py — busca de imagens via DuckDuckGo.
"""
from __future__ import annotations

import asyncio
from typing import Final, TypedDict

from ddgs import DDGS

from logger import get_logger

log = get_logger(__name__)

_DEFAULT_TIMEOUT: Final[float] = 15.0
_MAX_RETRIES: Final[int] = 3
_RETRY_BASE_DELAY: Final[float] = 1.0


class ImageResult(TypedDict):
    title: str
    link: str


def _search_sync(query: str, max_results: int) -> list[ImageResult]:
    raw = DDGS().images(query=query, region="wt-wt", safesearch="off", max_results=max_results)

    return [
        ImageResult(title=item.get("title") or "Sem título", link=item["image"])
        for item in raw or []
        if item.get("image")
    ]


async def search_images(
    query: str,
    max_results: int = 20,
    *,
    timeout: float = _DEFAULT_TIMEOUT,
    retries: int = _MAX_RETRIES,
) -> list[ImageResult]:
    """
    Busca imagens no DuckDuckGo de forma assíncrona.

    Args:
        query:       Termo de busca.
        max_results: Número máximo de resultados.
        timeout:     Tempo máximo por tentativa em segundos.
        retries:     Tentativas em caso de erro transitório.

    Returns:
        Lista de dicts com ``title`` e ``link``. Vazia em caso de falha.
    """
    if not query or not query.strip():
        log.warning("search_images chamado com query vazia — abortando.")
        return []

    log.info("Buscando imagens: %r (max=%d)", query, max_results)
    last_exc: BaseException | None = None

    for attempt in range(1, retries + 1):
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(_search_sync, query, max_results),
                timeout=timeout,
            )
            log.info("%d imagem(ns) retornada(s) para %r", len(results), query)
            return results

        except TimeoutError:
            last_exc = TimeoutError(f"Timeout após {timeout}s")
            log.warning("Timeout (tentativa %d/%d)", attempt, retries)

        except Exception as exc:
            last_exc = exc
            log.warning("Erro (tentativa %d/%d): %s", attempt, retries, exc)

        if attempt < retries:
            await asyncio.sleep(_RETRY_BASE_DELAY * (2 ** (attempt - 1)))

    log.error("Todas as tentativas falharam para %r: %s", query, last_exc)
    return []