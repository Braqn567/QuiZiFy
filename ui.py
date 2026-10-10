import base64
from html import escape
from pathlib import Path

import streamlit as st

from scoring import PASS_PERCENT, WEAK_PERCENT, fmt, grade_for, weak_topics

STYLE_PATH = Path(__file__).resolve().parent / "assets" / "style.css"


def apply_style():
    css = STYLE_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def format_duration(seconds):
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _level(percent):
    if percent >= WEAK_PERCENT:
        return "good"
    return "mid" if percent >= 40 else "low"


def page_title(title, subtitle=""):
    sub = f'<div class="page-sub">{escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="page-title">{escape(title)}</div>{sub}', unsafe_allow_html=True)


def step_title(number, title):
    st.markdown(
        f'<div class="step"><div class="step-num">{number}</div>'
        f'<div class="step-title">{escape(title)}</div></div>',
        unsafe_allow_html=True,
    )


def question_head(number, text, topic, hint=""):
    st.markdown(
        '<div class="q-head">'
        f'<div class="q-num">{number}</div>'
        f'<div class="q-text">{escape(text)}</div>'
        "</div>"
        f'<div class="q-meta"><span class="chip">{escape(topic)}</span>{escape(hint)}</div>',
        unsafe_allow_html=True,
    )


def donut_html(percent):
    color = "#087F6C" if percent >= PASS_PERCENT else "#D93B30"
    return (
        f'<div class="donut" style="background: conic-gradient({color} {percent}%, #E8ECEF 0);">'
        f'<div class="donut-inner">{percent}%</div></div>'
    )


def topic_bars_html(topics):
    bars = []
    for name, (points, maximum) in topics.items():
        percent = round(points / maximum * 100)
        bars.append(
            '<div class="cat">'
            f'<div class="cat-name"><span>{escape(name)}</span><span class="cat-pct">{percent}%</span></div>'
            f'<div class="bar"><div class="bar-fill bar-{_level(percent)}" style="width:{percent}%;"></div></div>'
            "</div>"
        )
    return "<div>" + "".join(bars) + "</div>"


def highlights_html(items):
    """Теми, подчертани с маркер. items: списък от (процент, тема)."""
    spans = "".join(
        f'<span class="hl">{escape(name)}<small>{percent}%</small></span>' for percent, name in items
    )
    return f'<div class="hl-list">{spans}</div>'


def avatar_html(avatar_bytes, username):
    if avatar_bytes:
        encoded = base64.b64encode(avatar_bytes).decode("ascii")
        return (
            f'<img class="avatar" src="data:image/png;base64,{encoded}" '
            f'alt="Профилна снимка на {escape(username)}">'
        )
    return f'<div class="avatar-initial">{escape(username[:1].upper())}</div>'


def profile_info_html(username, member_since, bio):
    if bio.strip():
        bio_html = f'<p class="profile-bio">{escape(bio)}</p>'
    else:
        bio_html = (
            '<p class="profile-bio profile-bio-empty">Още няма био. '
            "Добави няколко реда за себе си от „Редактирай профила“.</p>"
        )
    return (
        f'<div><div class="profile-name">{escape(username)}</div>'
        f'<div class="profile-meta">Член от {member_since}</div>{bio_html}</div>'
    )


def recent_tests_html(results):
    rows = []
    for r in results:
        percent = r["percent"]
        name, digit, _ = grade_for(percent)
        date = escape(str(r["data"].get("date", r["created_at"])))
        rows.append(
            f'<div class="test-row"><span class="test-date">{date}</span>'
            f'<span class="test-grade">{name} {digit}</span>'
            f'<span class="test-pct pct-{_level(percent)}">{percent}%</span></div>'
        )
    return "<div>" + "".join(rows) + "</div>"


def show_result(result, after_topics=None):
    """Карта с оценката, времето и успеваемостта по теми за един решен тест."""
    percent = result["percent"]
    passed = percent >= PASS_PERCENT
    grade_name, grade_digit, remark = grade_for(percent)
    topics = result["topics"]

    st.header("Резултат")

    with st.container(key="card_grade"):
        col_stamp, col_text, col_donut = st.columns([1.1, 2.2, 1.2])
        with col_stamp:
            st.markdown(
                f'<div class="stamp-wrap"><div class="stamp">{grade_digit}</div>'
                f'<div class="grade-word">{grade_name}</div></div>',
                unsafe_allow_html=True,
            )
        with col_text:
            pill_class = "status-pass" if passed else "status-fail"
            pill_text = "Издържан тест" if passed else "Неиздържан тест"
            points = f'{fmt(result["points"])} от {fmt(result["max_points"])}'
            st.markdown(
                f'<div><span class="status-pill {pill_class}">{pill_text}</span>'
                f'<div class="remark">{remark}</div>'
                f'<p class="points-line">Точки: <b>{points}</b></p></div>',
                unsafe_allow_html=True,
            )
        with col_donut:
            st.markdown(donut_html(percent), unsafe_allow_html=True)

    col_time, col_topics = st.columns([1, 2])
    with col_time:
        with st.container(key="card_time"):
            st.markdown(
                '<div><p class="stat-label">Време за решаване</p>'
                f'<p class="timer">{format_duration(result["duration_sec"])}</p>'
                f'<p class="stat-note">Начало {result["started"]}, край {result["finished"]}</p></div>',
                unsafe_allow_html=True,
            )
    with col_topics:
        with st.container(key="card_topics"):
            st.markdown(
                '<div><p class="stat-label">Успеваемост по теми</p>' + topic_bars_html(topics) + "</div>",
                unsafe_allow_html=True,
            )

    st.subheader("На какво да наблегнеш")
    weak = weak_topics(topics)
    if weak:
        st.markdown(highlights_html(weak), unsafe_allow_html=True)
    else:
        st.success("Всички теми са над 70%. Качи нов материал и провери следващата тема.")
    if after_topics:
        after_topics()
    with st.expander("Прегледай всички отговори"):
        for kind, text in result["feedback"]:
            getattr(st, kind)(text)
