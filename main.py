from trends.collector import collect_trends
from trends.storage import save_trends

from trends.analyzer import (
    analyze_trends,
    save_top_trends
)

from ai.trend_judge import (
    judge_topics
)


# ==========================================
# SETTINGS
# ==========================================

# Сколько математически лучших кандидатов
# отправляем в Gemini.
#
# 100 = хороший баланс между качеством
# отбора и количеством запросов.
AI_CANDIDATES = 100

# Минимальный AI score
MIN_AI_SCORE = 60

# Сколько финальных тем сохраняем
FINAL_TOPICS = 5


# ==========================================
# MAIN
# ==========================================

def main():

    print()
    print("🚀 YouTube Global Shorts")
    print()

    # ======================================
    # COLLECT
    # ======================================

    trends = collect_trends()

    save_trends(
        trends
    )

    # ======================================
    # MATHEMATICAL ANALYSIS
    # ======================================

    analyzed_trends = analyze_trends(
        trends,
        return_all=True
    )

    if not analyzed_trends:

        print()
        print(
            "❌ No analyzed trends found"
        )

        return

    # ======================================
    # SELECT AI CANDIDATES
    # ======================================

    ai_candidates = analyzed_trends[
        :AI_CANDIDATES
    ]

    print()
    print("================================")
    print("🤖 PREPARING AI TREND JUDGE")
    print("================================")
    print()

    print(
        f"📊 Original analyzed trends: "
        f"{len(analyzed_trends)}"
    )

    print(
        f"🎯 Candidates for AI Judge: "
        f"{len(ai_candidates)}"
    )

    # ======================================
    # EXTRACT TOPICS
    # ======================================

    topics = [

        trend["topic"]

        for trend in ai_candidates

        if trend.get(
            "topic"
        )
    ]

    if not topics:

        print()
        print(
            "❌ No trend candidates found"
        )

        return

    # ======================================
    # AI JUDGE
    # ======================================

    judged_trends = judge_topics(
        topics
    )

    if not judged_trends:

        print()
        print(
            "❌ AI Judge returned no results"
        )

        return

    # ======================================
    # KEEP APPROVED TOPICS
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
    # SORT BY AI SCORE
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
    # FINAL TOP
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
    # SAVE FINAL AI RESULTS
    # ======================================

    save_top_trends(
        approved_trends
    )

    # ======================================
    # COMPLETE
    # ======================================

    print()
    print(
        "================================"
    )

    print(
        "✅ Global trend pipeline completed"
    )

    print(
        f"🎯 Final topics: "
        f"{len(approved_trends)}"
    )

    print(
        "================================"
    )

    print()


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":

    main()
