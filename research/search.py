import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote


# =========================================================
# GOOGLE NEWS RSS
# =========================================================

BASE_URL = (
    "https://news.google.com/rss/search"
    "?q={query}"
    "&hl=en-US"
    "&gl=US"
    "&ceid=US:en"
)


# =========================================================
# SEARCH
# =========================================================

def search_news(
    query,
    limit=5
):

    print()
    print(
        f"🌐 Searching news: {query}"
    )

    url = BASE_URL.format(
        query=quote(query)
    )

    try:

        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        root = ET.fromstring(
            response.content
        )

        results = []

        channel = root.find(
            "channel"
        )

        if channel is None:
            return []

        for item in channel.findall(
            "item"
        ):

            if len(results) >= limit:
                break

            title = item.findtext(
                "title",
                ""
            )

            link = item.findtext(
                "link",
                ""
            )

            description = item.findtext(
                "description",
                ""
            )

            pub_date = item.findtext(
                "pubDate",
                ""
            )

            if not title:
                continue

            results.append({

                "title": title,

                "url": link,

                "content": description,

                "published_at": pub_date

            })

        print(
            f"✅ News results: "
            f"{len(results)}"
        )

        return results

    except Exception as error:

        print(
            f"⚠️ News search error: "
            f"{error}"
        )

        return []
