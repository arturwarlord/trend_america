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

    analyzed_trends = analyze_trends(
        trends,
        return_all=True
    )

    # ==========================
    # AI TREND JUDGE
    # ==========================

    print()
    print("================================")
    print("🤖 PREPARING AI TREND JUDGE")
    print("================================")
    print()

    topics = [
        trend["topic"]
        for trend in analyzed_trends
    ]

    if not topics:

        print(
            "❌ No trend candidates found"
        )

        return

    print(
        f"📊 Topics for AI Judge: "
        f"{len(topics)}"
    )

    print()

    # ==========================
    # GEMINI
    # ==========================

    judged_trends = judge_topics(
        topics
    )

    # ==========================
    # KEEP ONLY APPROVED
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
    # SORT BY AI SCORE
    # ==========================

    approved_trends.sort(
        key=lambda item:
            item.get(
                "score",
                0
            ),
        reverse=True
    )

    # ==========================
    # KEEP TOP 5
    # ==========================

    approved_trends = (
        approved_trends[:5]
    )

    # ==========================
    # PRINT RESULTS
    # ==========================

    print()
    print("================================")
    print("🔥 AI APPROVED TRENDS")
    print("================================")
    print()

    if not approved_trends:

        print(
            "❌ No suitable trends found"
        )

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
            f"{trend.get('score', 0):.0f}/100"
        )

        print(
            f"   Category: "
            f"{trend.get('category', 'unknown')}"
        )

        print(
            f"   Global Interest: "
            f"{trend.get('global_interest', 0):.0f}/10"
        )

        print(
            f"   Viral Potential: "
            f"{trend.get('viral_potential', 0):.0f}/10"
        )

        print(
            f"   English Audience: "
            f"{trend.get('english_audience', 0):.0f}/10"
        )

        print(
            f"   Story Potential: "
            f"{trend.get('story_potential', 0):.0f}/10"
        )

        print(
            f"   Specificity: "
            f"{trend.get('specificity', 0):.0f}/10"
        )

        print(
            f"   Factual Confidence: "
            f"{trend.get('factual_confidence', 0):.0f}/10"
        )

        print(
            f"   Originality: "
            f"{trend.get('originality', 0):.0f}/10"
        )

        print(
            f"   Reason: "
            f"{trend.get('reason', '')}"
        )

        print()

    # ==========================
    # SAVE
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
