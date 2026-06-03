def answer_coverage(user_query: str, final_report: str, sub_questions: list) -> float:
    if not sub_questions:
        return 1.0
    covered = sum(1 for sq in sub_questions if sq.lower() in final_report.lower())
    return covered / len(sub_questions)