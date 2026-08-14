from trends.collector import collect_trends
from trends.storage import save_trends


def main():

    print()
    print("🚀 YouTube Global Shorts")
    print()

    trends = collect_trends()

    save_trends(trends)

    print()
    print("✅ Global trend scan completed")
    print()


if __name__ == "__main__":
    main()
