import os

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()


def get_tavily_client():
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return None

    return TavilyClient(api_key=api_key)


def search_disease_links(diagnosis):
    if not diagnosis:
        return []

    client = get_tavily_client()

    if client is None:
        return []

    query = f"{diagnosis} plant disease treatment"

    response = client.search(
        query=query,
        search_depth="basic",
        max_results=3
    )

    results = response.get("results", [])

    links = []

    for result in results:
        url = result.get("url")

        if url:
            links.append(url)

    return links
