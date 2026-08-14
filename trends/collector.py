from trends.google_trends import get_google_trends
from trends.youtube_trends import get_youtube_trends


def collect_trends():

    print("🔥 Collecting global trends...")
    print()

    google = get_google_trends(
        country="US",
        limit=20
    )

    youtube = get_youtube_trends(
        region="US",
        limit=20
    )

    trends = google + youtube

    print()
    print(
        f"📊 Total trends collected: {len(trends)}"
    )

    return trends
