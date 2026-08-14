from trends.google_trends import get_google_trends
from trends.youtube_trends import get_youtube_trends


COUNTRIES = [
    {
        "name": "United States",
        "code": "US"
    },
    {
        "name": "United Kingdom",
        "code": "GB"
    },
    {
        "name": "Canada",
        "code": "CA"
    },
    {
        "name": "Australia",
        "code": "AU"
    },
    {
        "name": "India",
        "code": "IN"
    },
    {
        "name": "Germany",
        "code": "DE"
    },
    {
        "name": "France",
        "code": "FR"
    },
    {
        "name": "Japan",
        "code": "JP"
    },
    {
        "name": "South Korea",
        "code": "KR"
    },
    {
        "name": "Brazil",
        "code": "BR"
    }
]


def normalize_topic(trend):
    """
    Создаёт единый формат тренда.

    Важно:
    не меняем оригинальный title,
    а сохраняем дополнительные поля.
    """

    title = str(
        trend.get("title")
        or trend.get("topic")
        or trend.get("query")
        or ""
    ).strip()

    source = str(
        trend.get("source")
        or trend.get("type")
        or ""
    ).lower()

    return {
        **trend,

        "title": title,
        "topic": title,

        "source": source,

        "views": trend.get(
            "views",
            0
        ),

        "country": trend.get(
            "country",
            ""
        ),

        "country_name": trend.get(
            "country_name",
            ""
        )
    }


def collect_trends():

    print()
    print("================================")
    print("🌎 GLOBAL TREND ENGINE")
    print("================================")
    print()

    all_trends = []

    for country in COUNTRIES:

        name = country["name"]
        code = country["code"]

        print()
        print("--------------------------------")
        print(
            f"🌍 {name} ({code})"
        )
        print("--------------------------------")

        # ==================================================
        # GOOGLE TRENDS
        # ==================================================

        print(
            f"🌍 Google Trends: {code}"
        )

        try:

            google = get_google_trends(
                country=code,
                limit=20
            )

        except Exception as error:

            print(
                f"⚠️ Google Trends error: {error}"
            )

            google = []

        print(
            f"   Google: {len(google)}"
        )

        for trend in google:

            trend = normalize_topic(
                trend
            )

            trend["country"] = code
            trend["country_name"] = name

            trend["source"] = "google"

            all_trends.append(
                trend
            )

        # ==================================================
        # YOUTUBE TRENDS
        # ==================================================

        print(
            f"📺 YouTube Trends: {code}"
        )

        try:

            youtube = get_youtube_trends(
                region=code,
                limit=20
            )

        except Exception as error:

            print(
                f"⚠️ YouTube Trends error: {error}"
            )

            youtube = []

        print(
            f"   YouTube: {len(youtube)}"
        )

        for trend in youtube:

            trend = normalize_topic(
                trend
            )

            trend["country"] = code
            trend["country_name"] = name

            trend["source"] = "youtube"

            all_trends.append(
                trend
            )

    # ==================================================
    # REMOVE EMPTY TOPICS
    # ==================================================

    all_trends = [
        trend
        for trend in all_trends
        if trend.get("title")
    ]

    # ==================================================
    # COLLECTION COMPLETE
    # ==================================================

    print()
    print("================================")
    print("📊 GLOBAL COLLECTION COMPLETE")
    print("================================")
    print()

    print(
        f"🌎 Countries scanned: "
        f"{len(COUNTRIES)}"
    )

    print(
        f"📈 Total trends collected: "
        f"{len(all_trends)}"
    )

    return all_trends
