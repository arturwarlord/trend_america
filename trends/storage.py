import json
import os


FILE_PATH = (
    "data/trend_candidates.json"
)


def save_trends(trends):

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        FILE_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            trends,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(
        f"💾 Saved: {FILE_PATH}"
    )
