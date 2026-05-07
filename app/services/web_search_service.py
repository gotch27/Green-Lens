import os

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)


def search_disease_links(diagnosis):
    if not diagnosis:
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