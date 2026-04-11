"""
Image search utility.
Uses Serper when SERPER_API_KEY is configured and falls back to DuckDuckGo.
"""
import asyncio
import importlib
import json
import os
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError


SERPER_IMAGE_URL = "https://google.serper.dev/images"


async def _serper_image_search(query: str, num_results: int) -> list[dict]:
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("SERPER_API_KEY is not configured")

    payload = {"q": query, "num": max(1, min(num_results, 20))}
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }

    def _fetch() -> dict:
        req = urllib_request.Request(
            SERPER_IMAGE_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    try:
        data = await asyncio.to_thread(_fetch)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Serper image search failed: {exc}") from exc

    image_results = data.get("images", [])
    return [
        {
            "title": item.get("title", ""),
            "imageUrl": item.get("imageUrl", ""),
            "link": item.get("link", "") or item.get("source", ""),
            "source": item.get("source", ""),
            "thumbnailUrl": item.get("thumbnailUrl", ""),
        }
        for item in image_results[:num_results]
    ]


async def _duckduckgo_image_search(query: str, num_results: int) -> list[dict]:
    duckduckgo_module = importlib.import_module("duckduckgo_search")
    ddgs_class = getattr(duckduckgo_module, "DDGS")

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None,
        lambda: ddgs_class().images(query, max_results=num_results),
    )

    return [
        {
            "title": r.get("title", ""),
            "imageUrl": r.get("image", ""),
            "link": r.get("url", ""),
            "source": r.get("source", ""),
            "thumbnailUrl": r.get("thumbnail", ""),
        }
        for r in (results or [])[:num_results]
    ]


async def image_search(query: str, num_results: int = 6) -> list[dict]:
    """Return list of image results with title, imageUrl, link, and source metadata."""
    try:
        if os.getenv("SERPER_API_KEY", "").strip():
            return await _serper_image_search(query, num_results)

        return await _duckduckgo_image_search(query, num_results)
    except Exception as e:
        return [
            {
                "title": f"[Image search unavailable] for '{query}'",
                "imageUrl": f"https://via.placeholder.com/400x300?text={query.replace(' ', '+')}",
                "link": "",
                "source": "",
                "thumbnailUrl": "",
                "error": str(e),
            }
        ]
