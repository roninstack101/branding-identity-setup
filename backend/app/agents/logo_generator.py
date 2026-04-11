"""
Agent 7 – Logo Research Agent
Generates logo search queries, competitor references, and inspiration links instead of fixed logo images.
"""
import json
from urllib.parse import urlparse

from app.schemas.brand_schema import AgentResult
from app.utils.llm import call_llm
from app.utils.search import web_search


SYSTEM_PROMPT = """You are a Principal Logo Research Strategist and Visual Curator. Your goal is to map out the visual landscape for a new brand logo by identifying specific metaphors, styles, and real-world inspirations.

RESEARCH PRINCIPLES:
1. SEMANTIC SEARCH: Create search queries that combine the 'Brand Name' with 'Visual Archetypes' (e.g., 'minimalist geometric owl logo' vs. 'luxury gold monogram').
2. PLATFORM SPECIFICITY: Format queries to trigger the best results from professional design archives like Dribbble, Behance, and Pinterest.
3. LOGO TYPOLOGY: Recommend specific structures (Wordmark, Pictorial, Abstract, or Emblem) based on the brand's industry and name length.
4. VISUAL AVOIDANCE: Explicitly identify "clichés" or "overused tropes" in the industry to ensure the brand stays unique.

Your output must be a JSON object with EXACTLY these keys:
{
  "logo_direction": {
    "summary": "A high-level visual thesis for the logo (e.g., A fusion of organic lines and tech-forward geometry).",
    "best_logo_types": ["wordmark", "monogram", "symbol", "emblem", "combination mark"],
    "style_words": ["Specific descriptor 1", "Specific descriptor 2", "Specific descriptor 3"],
    "avoid_words": ["Cliche to avoid 1", "Visual trap 2"],
    "why_it_fits": "How this specific visual approach supports the Brand Strategy."
  },
  "search_queries": [
    {
      "label": "Platform Name (e.g., Pinterest Moodboard)",
      "query": "The exact search string to find high-quality inspiration.",
      "reason": "Why this specific query will yield strategic results."
    }
  ],
  "competitor_logo_brands": [
    {
      "name": "Benchmark Brand",
      "website": "URL or 'n/a'",
      "reason": "Why their logo execution is a relevant benchmark for this project."
    }
  ],
  "trend_keywords": ["Modern trend 1", "Timeless movement 2"],
  "logo_inspiration_notes": ["Note on symmetry/weight", "Note on color application", "Note on scalability"]
}

Return ONLY valid JSON. Focus on identifying 'Visual Metaphors' that aren't immediately obvious."""



def _domain_label(url: str) -> str:
    if not url:
        return ""
    host = urlparse(url).netloc.lower()
    host = host.replace("www.", "")
    if "pinterest" in host:
        return "Pinterest"
    if "dribbble" in host:
        return "Dribbble"
    if "behance" in host:
        return "Behance"
    if "logopond" in host:
        return "LogoPond"
    if "google" in host:
        return "Google"
    return host.split(".")[0].title() if host else ""


async def _generate_search_plan(naming_data: dict, design_data: dict, feedback: str | None = None) -> dict:
    brand_name = naming_data.get("brand_name", "Brand")
    tagline = naming_data.get("tagline", "")
    style = design_data.get("design_style", "modern")
    logo_direction = design_data.get("logo_direction", "clean symbol")
    mood_keywords = design_data.get("mood_keywords", [])[:4]
    trend_keywords = design_data.get("design_trends", [])[:4]

    user_prompt = (
        f"Brand name: {brand_name}\n"
        f"Tagline: {tagline}\n"
        f"Design style: {style}\n"
        f"Existing logo direction: {logo_direction}\n"
        f"Mood keywords: {', '.join(mood_keywords)}\n"
        f"Trend keywords: {', '.join(trend_keywords)}\n"
        f"Feedback: {feedback or 'none'}\n\n"
        f"Generate logo research queries, competitor-style inspiration brands, and logo direction notes."
    )

    raw = await call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.45,
        response_format={"type": "json_object"},
    )

    data = json.loads(raw)

    # Ensure a predictable base plan even if the model output is incomplete.
    if not data.get("search_queries"):
        data["search_queries"] = [
            {
                "label": "Pinterest Moodboard",
                "query": f"site:pinterest.com {brand_name} logo inspiration {style}",
                "reason": "Moodboard-style logo ideas with visual references",
            },
            {
                "label": "Dribbble Logo Concepts",
                "query": f"site:dribbble.com logo concept {brand_name} {style}",
                "reason": "Professional logo explorations and concept work",
            },
            {
                "label": "Behance Identity Systems",
                "query": f"site:behance.net brand identity logo {brand_name} {style}",
                "reason": "Identity systems and real-world branding references",
            },
            {
                "label": "LogoPond Ideas",
                "query": f"site:logopond.com logo inspiration {brand_name}",
                "reason": "Classic logo idea archive",
            },
        ]

    if not data.get("logo_direction"):
        data["logo_direction"] = {
            "summary": f"A {style} logo system that feels aligned with {brand_name}.",
            "best_logo_types": ["wordmark", "symbol", "combination mark"],
            "style_words": [style, "clean", "memorable"],
            "avoid_words": ["generic", "overused"],
            "why_it_fits": f"It reflects the brand personality and the existing design direction.",
        }

    return data


async def _collect_logo_inspiration(search_plan: list[dict]) -> list[dict]:
    inspiration: list[dict] = []

    for query_item in search_plan:
        query = query_item.get("query", "")
        if not query:
            continue

        results = await web_search(query, num_results=5)
        for result in results:
            link = result.get("link", "")
            title = result.get("title", "")
            if not link or not title:
                continue

            inspiration.append(
                {
                    "brand_name": title,
                    "title": title,
                    "link": link,
                    "snippet": result.get("snippet", ""),
                    "query": query,
                    "query_label": query_item.get("label", ""),
                    "platform": _domain_label(link),
                }
            )

    seen: set[str] = set()
    unique_inspiration: list[dict] = []
    for item in inspiration:
        link = item["link"]
        if link in seen:
            continue
        seen.add(link)
        unique_inspiration.append(item)

    return unique_inspiration[:12]


async def run(
    naming_data: dict,
    design_data: dict,
    feedback: str | None = None,
) -> AgentResult:
    """Execute the Logo Research Agent."""
    search_plan = await _generate_search_plan(naming_data, design_data, feedback)
    inspiration_links = await _collect_logo_inspiration(search_plan.get("search_queries", []))

    competitor_logo_brands = search_plan.get("competitor_logo_brands", [])
    if not competitor_logo_brands:
        competitor_logo_brands = [
            {
                "name": item.get("platform") or item.get("brand_name") or "Inspiration",
                "website": item.get("link", ""),
                "reason": item.get("query_label", "Logo inspiration search result"),
            }
            for item in inspiration_links[:8]
        ]

    data = {
        "logo_direction": search_plan.get("logo_direction", {}),
        "search_queries": search_plan.get("search_queries", []),
        "competitor_logo_brands": competitor_logo_brands[:10],
        "trend_keywords": search_plan.get("trend_keywords", []),
        "logo_inspiration_notes": search_plan.get("logo_inspiration_notes", []),
        "logo_inspiration": inspiration_links,
    }

    logo_direction = data.get("logo_direction", {})
    explanation = (
        f"Prepared {len(data.get('search_queries', []))} logo search queries and collected "
        f"{len(inspiration_links)} inspiration links for '{naming_data.get('brand_name', 'Brand')}'. "
        f"Recommended logo types: {', '.join(logo_direction.get('best_logo_types', [])[:3])}. "
        f"The result focuses on real logo ideas, competitor references, and trend-based inspiration instead of repeated generated logos."
    )

    return AgentResult(data=data, explanation=explanation)
