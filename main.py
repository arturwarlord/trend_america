from trends.collector import collect_trends
from trends.storage import save_trends
from trends.analyzer import (
    analyze_trends,
    save_top_trends
)


def main():

    print()
    print("🚀 YouTube Global Shorts")
    print()

    # ==========================
    # COLLECT
    # ==========================

    trends = collect_trends()

    save_trends(
        trends
    )

    # ==========================
    # ANALYZE
    # ==========================

    top_trends = analyze_trends(
        trends
    )

    save_top_trends(
        top_trends
    )

    print()
    print(
        "✅ Global trend pipeline completed"
    )
    print()


if __name__ == "__main__":
    main()
