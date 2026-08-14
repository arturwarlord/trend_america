from trends.collector import collect_trends

from trends.storage import (
    save_trends
)

from trends.analyzer import (
    analyze_trends,
    save_analyzed_trends,
    save_top_trends
)

from ai.trend_judge import (
    judge_topics
)


# ==========================================
# CONFIG
# ==========================================

MAX_AI_TOPICS = 30

MIN_AI_SCORE = 60

FINAL_TOPICS = 5


# ==========================================
# MAIN
# ==========================================

def main():

    print()
    print("🚀 YouTube Global Shorts")
    print()

    # ======================================
    # COLLECT GLOBAL TRENDS
    # ======================================

    trends = collect_trends()

    if not trends:

        print()
        print("❌ No trends collected")
        print()

        return

    save_trends(
        trends
    )

    # ======================================
    # MATHEMATICAL ANALYSIS
    # ======================================

    analyzed_trends = analyze_trends(
        trends
    )

    if not analyzed_trends:

        print()
        print("❌ No analyzed trends")
        print()

        save_top_trends([])

        return

    # ======================================
    # SAVE TOP 30
    # ======================================

    save_analyzed_trends(
        analyzed_trends
    )

    # ======================================
    # PREPARE AI JUDGE
    # ======================================

    print()
    print("================================")
    print("🤖 PREPARING AI TREND JUDGE")
    print("================================")
    print()

    # --------------------------------------
    # LIMIT TOPICS FOR GEMINI
    # --------------------------------------

    ai_candidates = analyzed_trends[
        :MAX_AI_TOPICS
    ]

    topics = [

        trend.get(
            "topic",
            ""
        )

        for trend in ai_candidates

        if trend.get(
            "topic",
            ""
        )
    ]

    if not topics:

        print()
        print("❌ No topics for AI Judge")
        print()

        save_top_trends([])

        return

    print(
        f"📊 Topics for AI Judge: "
        f"{len(topics)}"
    )

    print()

    # ======================================
    # AI JUDGE
    # ======================================

    judged_trends = judge_topics(
        topics
    )

    if not judged_trends:

        print()
        print("❌ AI Judge returned no results")
        print()

        save_top_trends([])

        return

    # ======================================
    # KEEP APPROVED
    # ======================================

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
        ) >= MIN_AI_SCORE
    ]

    # ======================================
    # SORT
    # ======================================

    approved_trends.sort(

        key=lambda item:
            item.get(
                "score",
                0
            ),

        reverse=True
    )

    # ======================================
    # FINAL TOP 5
    # ======================================

    approved_trends = approved_trends[
        :FINAL_TOPICS
    ]

    # ======================================
    # PRINT RESULTS
    # ======================================

    print()
    print("================================")
    print("🔥 AI APPROVED TRENDS")
    print("================================")
    print()

    if not approved_trends:

        print(
            "❌ AI did not approve any topics"
        )

    else:

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

    # ======================================
    # SAVE FINAL RESULTS
    # ======================================

    save_top_trends(
        approved_trends
    )

    # ======================================
    # FINAL STATUS
    # ======================================

    print()
    print("================================")
    print("✅ Global trend pipeline completed")
    print("================================")
    print()

    print(
        f"🎯 Final topics: "
        f"{len(approved_trends)}"
    )

    print()


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":

    main()
