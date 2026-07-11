"""Open tourism data tools, exposed as LangChain tools for the agents.

All tools return (human_summary, structured_artifact) via the content_and_artifact
response format, so the LLM sees a readable summary while the graph reads typed
data from ToolMessage.artifact. Every tool degrades gracefully on failure.
"""

from odyssey.providers.tools.geocode import geocode_place
from odyssey.providers.tools.poi import search_pois
from odyssey.providers.tools.weather import get_weather

DESTINATION_TOOLS = [geocode_place, get_weather, search_pois]

__all__ = ["geocode_place", "get_weather", "search_pois", "DESTINATION_TOOLS"]
