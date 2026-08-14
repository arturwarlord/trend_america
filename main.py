from dotenv import load_dotenv

from trends.collector import (
    collect_trends
)

from trends.storage import (
    save_trends
)


def main():

    print(
        "\n"
        "🚀 YouTube Global Shorts"
        "\n"
    )

    trends = collect_trends()

    save_trends(
        trends
    )

    print(
        "\n"
        "✅ Trend Engine завершён"
        "\n"
    )


if __name__ == "__main__":
    main()
