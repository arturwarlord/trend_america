import json
import os


DATA_FILE = (
    "data/trend_candidates.json"
)


def save_trends(trends):

    os.makedirs(
        "data",
        exist_ok=True
    )

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            trends,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"💾 Тренды сохранены: "
        f"{DATA_FILE}"
    )
