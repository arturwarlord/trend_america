from trends.global_collector import (
    collect_global_trends
)

from trends.storage import (
    save_global_trends
)


def main():

    print()
    print("🚀 YouTube Global Shorts")
    print()

    trends = collect_global_trends()

    save_global_trends(
        trends
    )

    print()
    print("✅ Global trend scan completed")
    print()


if __name__ == "__main__":
    main()
