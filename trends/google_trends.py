import requests
import xml.etree.ElementTree as ET


GOOGLE_TRENDS_URL = (
    "https://trends.google.com/trending/rss"
)


def get_google_trends(
    country: str = "US",
    limit: int = 20
):
    """
    Получает актуальные тренды Google Trends.

    country:
        US - United States
        GB - United Kingdom
        CA - Canada
        AU - Australia

    limit:
        Максимальное количество трендов.
    """

    url = f"{GOOGLE_TRENDS_URL}?geo={country}"

    print(
        f"🌍 Получаем Google Trends: {country}"
    )

    try:

        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64)"
                )
            }
        )

        response.raise_for_status()

        root = ET.fromstring(
            response.content
        )

        trends = []

        namespace = {
            "ht": "https://trends.google.com/trending/rss"
        }

        for item in root.findall(".//item"):

            title = item.findtext("title")

            if not title:
                continue

            traffic = item.findtext(
                "{https://trends.google.com/trending/rss}"
                "approx_traffic"
            )

            trends.append(
                {
                    "source": "google",
                    "title": title.strip(),
                    "traffic": traffic or "unknown"
                }
            )

            if len(trends) >= limit:
                break

        print(
            f"✅ Google Trends: "
            f"{len(trends)} тем"
        )

        return trends

    except Exception as error:

        print(
            f"❌ Google Trends error: {error}"
        )

        return []
