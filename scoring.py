"""Оценяване на тест: точки, оценка и обобщение по теми."""

PASS_PERCENT = 50  # от колко процента нагоре тестът е издържан
WEAK_PERCENT = 70  # под колко процента една тема се смята за слаба

RULES = {
    "strict": "Като на изпит: всичко или нищо",
    "partial": "Частично (минус за грешни)",
}

POINT_VALUES = {
    "one": "1 точка за въпрос",
    "by_correct": "Колкото са верните отговори (напр. 3 верни = 3 точки)",
}

# (от колко процента, оценка, цифра, коментар)
GRADES = [
    (90, "Отличен", 6, "Отлична работа! Продължавай все така!"),
    (75, "Много добър", 5, "Много добре! Още малко и си на върха."),
    (60, "Добър", 4, "Добре, но има какво да подобриш."),
    (50, "Среден", 3, "Минаваш, но ти трябва още повторение."),
    (0, "Слаб", 2, "Този път не стана. Прегледай слабите теми и опитай пак."),
]


def fmt(number):
    """3.0 -> '3', 0.75 -> '0.75'."""
    return f"{round(number, 2):g}"


def grade_for(percent):
    """Връща (име на оценката, цифра, коментар)."""
    for threshold, name, digit, remark in GRADES:
        if percent >= threshold:
            return name, digit, remark


def question_score(selected, correct, rule):
    """Каква част от точките на въпроса е спечелена (от 0 до 1)."""
    if rule == "strict":
        return 1.0 if selected == correct else 0.0
    hits = len(selected & correct)
    misses = len(selected - correct)
    return max(0.0, (hits - misses) / len(correct))


def _feedback_line(number, question, selected, correct, points, max_points):
    right = "; ".join(question.options[j] for j in sorted(correct))
    chosen = "; ".join(question.options[j] for j in sorted(selected))
    max_text = fmt(max_points)
    if not selected:
        text = f"{number}. Няма отговор (0 от {max_text} т.). Верни: {right}."
        return "warning", f"{text} {question.explanation}"
    if points == max_points:
        text = f"{number}. Напълно вярно! ({max_text} от {max_text} т.)"
        return "success", f"{text} {question.explanation}"
    if points > 0:
        text = (
            f"{number}. Частично ({fmt(points)} от {max_text} т.). "
            f"Ти избра: {chosen}. Верни: {right}."
        )
        return "info", f"{text} {question.explanation}"
    text = f"{number}. Грешно (0 от {max_text} т.). Ти избра: {chosen}. Верни: {right}."
    return "error", f"{text} {question.explanation}"


def evaluate(test, answers, rule, point_value, started_at, finished_at):
    """Проверява теста и връща речника, който се показва и запазва в базата.

    answers: {номер на въпрос: множество от избраните отговори}
    """
    earned = 0.0
    possible = 0.0
    topics = {}  # тема -> [спечелени точки, възможни точки]
    feedback = []

    for i, question in enumerate(test):
        correct = set(question.correct_indices)
        selected = answers[i]
        max_points = len(correct) if point_value == "by_correct" else 1
        points = question_score(selected, correct, rule) * max_points

        earned += points
        possible += max_points

        topic = topics.setdefault(question.topic.strip().capitalize(), [0.0, 0.0])
        topic[0] += points
        topic[1] += max_points

        feedback.append(_feedback_line(i + 1, question, selected, correct, points, max_points))

    return {
        "percent": round(earned / possible * 100),
        "points": earned,
        "max_points": possible,
        "questions": len(test),
        "topics": topics,
        "feedback": feedback,
        "started": started_at.strftime("%H:%M"),
        "finished": finished_at.strftime("%H:%M"),
        "duration_sec": int((finished_at - started_at).total_seconds()),
        "date": finished_at.strftime("%d.%m.%Y %H:%M"),
    }


def weak_topics(topics, limit=None):
    """Теми под WEAK_PERCENT като (процент, тема), най-слабите първи."""
    ranked = sorted(
        (round(points / maximum * 100), name)
        for name, (points, maximum) in topics.items()
        if maximum > 0
    )
    weak = [(percent, name) for percent, name in ranked if percent < WEAK_PERCENT]
    return weak[:limit]
