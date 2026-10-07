import pandas as pd
import streamlit as st

from database import list_results
from scoring import grade_for, weak_topics
from ui import highlights_html, page_title, show_result


def render():
    page_title("История", "Всички решени тестове и как се променя успеваемостта ти.")

    user = st.session_state.get("user")
    if not user:
        st.info("Влез в профила си (меню → Профил), за да виждаш историята на тестовете си.")
        return

    results = list_results(user["id"])
    if not results:
        st.info("Още нямаш запазени тестове. Реши един в „Нов тест“ и резултатът ще се появи тук.")
        return

    percents = [r["percent"] for r in results]
    _summary(percents)
    if len(percents) >= 2:
        _progress_chart(percents)
    _weakest_topics(results)
    _test_picker(results)


def _summary(percents):
    total, average, best = st.columns(3)
    total.metric("Тестове", len(percents))
    average.metric("Средна успеваемост", f"{round(sum(percents) / len(percents))}%")
    best.metric("Най-добър резултат", f"{max(percents)}%")


def _progress_chart(percents):
    st.subheader("Прогрес")
    oldest_first = percents[::-1]
    data = pd.DataFrame(
        {"Тест №": range(1, len(oldest_first) + 1), "Успеваемост %": oldest_first}
    ).set_index("Тест №")
    st.line_chart(data, color="#087F6C")


def _weakest_topics(results):
    totals = {}
    for r in results:
        for topic, (points, maximum) in r["data"]["topics"].items():
            entry = totals.setdefault(topic, [0.0, 0.0])
            entry[0] += points
            entry[1] += maximum

    st.subheader("Най-слаби теми досега")
    weak = weak_topics(totals, limit=5)
    if weak:
        st.markdown(highlights_html(weak), unsafe_allow_html=True)
    else:
        st.success("Всички теми са над 70%. Продължавай така.")


def _test_picker(results):
    def label(i):
        r = results[i]
        name, digit, _ = grade_for(r["percent"])
        date = r["data"].get("date", r["created_at"])
        return f"{date}, {r['percent']}%, {name} {digit}"

    st.subheader("Твоите тестове")
    choice = st.selectbox("Отвори тест", range(len(results)), format_func=label)
    show_result(results[choice]["data"])
