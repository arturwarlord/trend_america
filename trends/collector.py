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


def collect_global_trends():

    print()
    print("================================")
    print("🌎 GLOBAL TREND SCANNER")
    print("================================")
    print()

    all_trends = []

    for country in COUNTRIES:

        name = country["name"]
        code = country["code"]

        print()
        print("--------------------------------")
        print(f"🌍 {name} ({code})")
        print("--------------------------------")

        # ==========================
        # GOOGLE
        # ==========================

        google_trends = get_google_trends(
            country=code,
            limit=20
        )

        for trend in google_trends:

            trend["country"] = code
            trend["country_name"] = name

            all_trends.append(trend)

        # ==========================
        # YOUTUBE
        # ==========================

        youtube_trends = get_youtube_trends(
            region=code,
            limit=20
        )

        for trend in youtube_trends:

            trend["country"] = code
            trend["country_name"] = name

            all_trends.append(trend)

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
        f"📈 Total trends: "
        f"{len(all_trends)}"
    )

    return all_trends
