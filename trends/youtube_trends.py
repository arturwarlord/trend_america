import os
import requests


def get_youtube_trends(
    region="US",
    limit=20
):

    print(
        f"📺 YouTube Trends: {region}"
    )

    api_key = os.getenv(
        "YOUTUBE_API_KEY"
    )

    if not api_key:

        print(
            "❌ YOUTUBE_API_KEY is missing"
        )

        return []

    url = (
        "https://www.googleapis.com/"
        "youtube/v3/videos"
    )

    params = {

        "part":
            "snippet,statistics",

        "chart":
            "mostPopular",

        "regionCode":
            region,

        "maxResults":
            limit,

        "key":
            api_key
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        results = []

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

            results.append({

                "source":
                    "youtube",

                "title":
                    snippet.get(
                        "title",
                        ""
                    ),

                "video_id":
                    video.get(
                        "id"
                    ),

                "views":
                    int(
                        statistics.get(
                            "viewCount",
                            0
                        )
                    )

            })

        print(
            f"✅ YouTube: "
            f"{len(results)} trends"
        )

        return results

    except Exception as error:

        print(
            f"❌ YouTube error: {error}"
        )

        return []
