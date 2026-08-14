from trends.collector import collect_trends
from trends.storage import save_trends


def main():

    print()
    print("================================")
    print("🌍 GLOBAL TREND ENGINE")
    print("================================")
    print()

    trends = collect_trends()

    save_trends(trends)

    print()
    print("✅ Trend scan completed")
    print()


if __name__ == "__main__":
    main()
