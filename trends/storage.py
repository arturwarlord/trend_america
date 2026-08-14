import json
import os


RAW_TRENDS_FILE = (
    "data/global_trends.json"
)


def save_global_trends(trends):

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        RAW_TRENDS_FILE,
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
        f"💾 Saved: {RAW_TRENDS_FILE}"
    )
