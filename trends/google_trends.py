import requests
import xml.etree.ElementTree as ET


def get_google_trends(
    country="US",
    limit=20
):

    print(
        f"🌍 Google Trends: {country}"
    )

    url = (
        "https://trends.google.com/"
        "trending/rss"
        f"?geo={country}"
    )

    try:

        response = requests.get(
            url,
            timeout=20,
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

        for item in root.findall(".//item"):

            title = item.findtext("title")

            if not title:
                continue

            results.append({

                "source": "google",

                "title": title.strip()

            })

            if len(results) >= limit:
                break

        print(
            f"✅ Google: {len(results)} trends"
        )

        return results

    except Exception as error:

        print(
            f"❌ Google Trends error: {error}"
        )

        return []
