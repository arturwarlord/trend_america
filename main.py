from trends.collector import collect_trends
from trends.storage import save_trends
from trends.analyzer import (
    analyze_trends,
    save_top_trends
)

from ai.trend_judge import (
    judge_topics
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

    # ==========================
    # AI TREND JUDGE
    # ==========================

    print()
    print("================================")
    print("🤖 PREPARING AI TREND JUDGE")
    print("================================")
    print()

    # analyze_trends currently
    # returns TOP 10.
    #
    # For the first test we send
    # these 10 candidates to Gemini.

    topics = [
        trend["topic"]
        for trend in top_trends
    ]

    if not topics:

        print(
            "❌ No trend candidates found"
        )

        return

    judged_trends = judge_topics(
        topics
    )

    # ==========================
    # KEEP ONLY APPROVED TOPICS
    # ==========================

    approved_trends = [

        trend

        for trend in judged_trends

        if trend.get(
            "is_good_for_shorts",
            False
        )

        and trend.get(
            "score",
            0
        ) >= 60

    ]

    # ==========================
    # TOP AI TRENDS
    # ==========================

    approved_trends = sorted(
        approved_trends,
        key=lambda item:
            item.get(
                "score",
                0
            ),
        reverse=True
    )

    approved_trends = (
        approved_trends[:5]
    )

    print()
    print("================================")
    print("🔥 AI APPROVED TRENDS")
    print("================================")
    print()

    for index, trend in enumerate(
        approved_trends,
        start=1
    ):

        print(
            f"#{index} "
            f"{trend.get('topic', '')}"
        )

        print(
            f"   AI Score: "
            f"{trend.get('score', 0)}/100"
        )

        print(
            f"   Category: "
            f"{trend.get('category', 'unknown')}"
        )

        print(
            f"   Global Interest: "
            f"{trend.get('global_interest', 0)}/10"
        )

        print(
            f"   Viral Potential: "
            f"{trend.get('viral_potential', 0)}/10"
        )

        print(
            f"   English Audience: "
            f"{trend.get('english_audience', 0)}/10"
        )

        print(
            f"   Story Potential: "
            f"{trend.get('story_potential', 0)}/10"
        )

        print(
            f"   Reason: "
            f"{trend.get('reason', '')}"
        )

        print()

    # ==========================
    # SAVE AI RESULTS
    # ==========================

    save_top_trends(
        approved_trends
    )

    print()
    print(
        "✅ Global trend pipeline completed"
    )
    print()


if __name__ == "__main__":
    main()
