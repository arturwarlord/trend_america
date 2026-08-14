import os
import requests


YOUTUBE_API_URL = (
    "https://www.googleapis.com/youtube/v3/videos"
)


def get_youtube_trends(
    region: str = "US",
    limit: int = 20
):

    api_key = os.getenv(
        "YOUTUBE_API_KEY"
    )

    if not api_key:

        print(
            "⚠️ YOUTUBE_API_KEY не найден"
        )

        return []

    print(
        f"📺 Получаем YouTube Trends: {region}"
    )

    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": limit,
        "key": api_key
    }

    try:

        response = requests.get(
            YOUTUBE_API_URL,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        trends = []

        for video in data.get(
            "items",
            []
        ):

            snippet = video.get(
                "snippet",
                {}
            )

            statistics = video.get(
                "statistics",
                {}
            )

            title = snippet.get(
                "title"
            )

            if not title:
                continue

            trends.append(
                {
                    "source": "youtube",
                    "title": title,
                    "video_id": video.get(
                        "id"
                    ),
                    "views": int(
                        statistics.get(
                            "viewCount",
                            0
                        )
                    )
                }
            )

        print(
            f"✅ YouTube Trends: "
            f"{len(trends)} видео"
        )

        return trends

    except Exception as error:

        print(
            f"❌ YouTube Trends error: "
            f"{error}"
        )

        return []
