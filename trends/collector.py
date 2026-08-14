from trends.google_trends import (
    get_google_trends
)

from trends.youtube_trends import (
    get_youtube_trends
)


def collect_trends():

    print(
        "\n"
        "🔥 TREND ENGINE"
        "\n"
    )

    google_trends = get_google_trends(
        country="US",
        limit=20
    )

    youtube_trends = get_youtube_trends(
        region="US",
        limit=20
    )

    trends = (
        google_trends
        + youtube_trends
    )

    print(
        "\n"
        f"📊 Всего найдено: "
        f"{len(trends)}"
    )

    return trends
