from html import escape
import base64
import streamlit as st

PASS_PERCENT = 50  # от колко процента нагоре тестът се смята за издържан
WEAK_PERCENT = 70  # под колко процента една тема е "за наблягане"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700;800&family=Caveat:wght@600;700&display=swap');

:root {
  --abyss: #0B2B45;
  --lagoon: #087F6C;
  --lagoon-dark: #066B5B;
  --mint: #D6F5EA;
  --paper: #F6F9F7;
  --grid: #E3EBE7;
  --pen: #D93B30;
  --pen-ink: #B42318;
  --marker: #FFE76A;
  --amber: #E8A317;
  --ink: #10283A;
  --muted: #5C6F7B;
  --line: #D9E4DE;
}

/* ---------- Шрифт ---------- */
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea,
.stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
  font-family: 'Onest', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.stApp h1, .stApp h2, .stApp h3 {
  color: var(--ink);
  letter-spacing: -0.02em;
  font-weight: 800;
}
.stApp h2 { font-size: 1.6rem; }
.stApp h3 { font-size: 1.2rem; font-weight: 700; }

/* ---------- Страница: тетрадка на квадратчета ---------- */
.stApp { background: var(--paper); color: var(--ink); }
[data-testid="stMain"], section.main {
  background-color: var(--paper);
  background-image:
    linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: 28px 28px;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppDeployButton"], .stDeployButton { display: none; }
.block-container { max-width: 1040px; padding-top: 2.4rem; padding-bottom: 5rem; }

/* ---------- Меню отляво ---------- */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0B2B45 0%, #0D4A5C 100%);
}
section[data-testid="stSidebar"] > div { background: transparent; }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: #E6F1EE; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #9CC3CC; }
section[data-testid="stSidebar"] hr { border-color: rgba(255, 255, 255, 0.14); }

.brand { font-weight: 800; font-size: 1.6rem; letter-spacing: -0.03em; color: #fff; margin: 0.4rem 0 0; line-height: 1; }
.brand-sub { color: #9CC3CC; font-size: 0.92rem; margin: 0.4rem 0 1.4rem; }

section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 0.25rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label {
  width: 100%;
  padding: 0.6rem 0.85rem;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.12s;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background: rgba(255, 255, 255, 0.08); }
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
  background: rgba(61, 219, 176, 0.18);
  box-shadow: inset 3px 0 0 #3DDBB0;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label p { font-weight: 600; font-size: 1.02rem; }

/* ---------- Бутони ---------- */
button[data-testid^="stBaseButton-primary"] {
  background: var(--lagoon);
  border: 0;
  border-radius: 12px;
  padding: 0.6rem 1.4rem;
  box-shadow: 0 2px 0 #055B4C;
}
button[data-testid^="stBaseButton-primary"] p { color: #fff !important; font-weight: 700; }
button[data-testid^="stBaseButton-primary"]:hover { background: var(--lagoon-dark); }
button[data-testid^="stBaseButton-primary"]:active { transform: translateY(1px); box-shadow: 0 1px 0 #055B4C; }
button[data-testid^="stBaseButton-secondary"] {
  background: #fff;
  border: 1.5px solid var(--line);
  border-radius: 12px;
}
button[data-testid^="stBaseButton-secondary"] p { color: var(--ink); font-weight: 600; }
button:focus-visible { outline: 3px solid #7FD9C3 !important; outline-offset: 2px; }

/* ---------- Полета ---------- */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
  border-radius: 10px !important;
  border-color: var(--line) !important;
}
[data-baseweb="input"]:focus-within { border-color: var(--lagoon) !important; }

[data-testid="stFileUploaderDropzone"] {
  background: #fff;
  border: 2px dashed #7DB9AB;
  border-radius: 18px;
  padding: 1.8rem 1.2rem;
}
[data-testid="stFileUploaderDropzone"]:hover { background: #F2FBF8; border-color: var(--lagoon); }

[data-testid="stForm"] { border: 0; padding: 0; }
button[data-baseweb="tab"] p { font-weight: 600; }
[data-baseweb="tab-highlight"] { background-color: var(--lagoon) !important; }
[data-testid="stAlert"] { border-radius: 12px; }
[data-testid="stExpander"] details { border: 1px solid var(--line); border-radius: 14px; background: #fff; }

[data-testid="stMetric"] {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.9rem 1.1rem;
}
[data-testid="stMetricLabel"] p { color: var(--muted); font-size: 0.88rem; }
[data-testid="stMetricValue"] { font-weight: 800; letter-spacing: -0.02em; }

/* ---------- Карти ---------- */
[class*="st-key-card_"] {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 1.3rem 1.5rem;
  box-shadow: 0 1px 0 rgba(11, 43, 69, 0.05), 0 14px 28px -18px rgba(11, 43, 69, 0.35);
}
[class*="st-key-qcard"] {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 1.1rem 1.25rem;
  box-shadow: 0 1px 0 rgba(11, 43, 69, 0.05);
}

/* Отговорите във въпросите: като редове за отбелязване */
[class*="st-key-qcard"] div[role="radiogroup"] { gap: 0.45rem; }
[class*="st-key-qcard"] div[role="radiogroup"] > label,
[class*="st-key-qcard"] [data-testid="stCheckbox"] label {
  display: flex;
  align-items: center;
  width: 100%;
  border: 1.5px solid var(--line);
  border-radius: 10px;
  padding: 0.6rem 0.85rem;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.12s, background 0.12s;
}
[class*="st-key-qcard"] div[role="radiogroup"] > label:hover,
[class*="st-key-qcard"] [data-testid="stCheckbox"] label:hover { border-color: var(--lagoon); background: #F4FBF8; }
[class*="st-key-qcard"] div[role="radiogroup"] > label:has(input:checked),
[class*="st-key-qcard"] [data-testid="stCheckbox"] label:has(input:checked) {
  border-color: var(--lagoon);
  background: var(--mint);
}

/* ---------- Заглавия и стъпки ---------- */
.page-title { font-size: 2.3rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; color: var(--ink); margin: 0 0 0.3rem; }
.page-sub { color: var(--muted); font-size: 1.05rem; max-width: 60ch; margin: 0 0 1.4rem; }

.step { display: flex; align-items: center; gap: 0.7rem; margin: 2rem 0 0.8rem; }
.step-num {
  flex: none; width: 1.9rem; height: 1.9rem; border-radius: 50%;
  background: var(--abyss); color: #fff; font-weight: 700; font-size: 0.95rem;
  display: flex; align-items: center; justify-content: center;
}
.step-title { font-size: 1.3rem; font-weight: 800; letter-spacing: -0.02em; color: var(--ink); }

.q-head { display: flex; gap: 0.8rem; align-items: flex-start; margin-bottom: 0.35rem; }
.q-num {
  flex: none; min-width: 1.7rem; height: 1.7rem; border-radius: 999px; margin-top: 0.1rem;
  background: var(--mint); color: var(--lagoon-dark); font-weight: 800; font-size: 0.9rem;
  display: flex; align-items: center; justify-content: center;
}
.q-text { font-weight: 700; font-size: 1.08rem; line-height: 1.4; color: var(--ink); }
.q-meta { margin: 0 0 0.7rem 2.5rem; color: var(--muted); font-size: 0.9rem; }
.chip {
  display: inline-block; background: #EEF4F1; color: var(--muted);
  border-radius: 999px; padding: 0.1rem 0.7rem; font-size: 0.82rem; font-weight: 600; margin-right: 0.6rem;
}

/* ---------- Резултат ---------- */
.stamp-wrap { display: flex; flex-direction: column; align-items: center; padding: 0.3rem 0; }
.stamp {
  width: 112px; height: 112px; display: flex; align-items: center; justify-content: center;
  border: 5px solid var(--pen);
  border-radius: 58% 42% 55% 45% / 47% 57% 43% 53%;
  color: var(--pen);
  font-family: 'Caveat', cursive !important;
  font-weight: 700; font-size: 4.6rem; line-height: 1;
  transform: rotate(-6deg);
  animation: stamp-in 0.35s cubic-bezier(0.2, 0.9, 0.3, 1.2) both;
}
@keyframes stamp-in {
  from { opacity: 0; transform: rotate(-6deg) scale(1.7); }
  to { opacity: 1; transform: rotate(-6deg) scale(1); }
}
.grade-word { color: var(--muted); font-size: 0.92rem; font-weight: 600; margin-top: 0.6rem; text-align: center; }

.status-pill { display: inline-block; padding: 0.25rem 0.85rem; border-radius: 999px; font-weight: 700; font-size: 0.92rem; }
.status-pass { background: var(--mint); color: var(--lagoon-dark); }
.status-fail { background: #FDE3E0; color: var(--pen-ink); }
.remark {
  font-family: 'Caveat', cursive !important;
  font-weight: 700; font-size: 1.9rem; line-height: 1.15; color: var(--pen-ink);
  margin: 0.7rem 0 0.5rem; transform: rotate(-1deg);
}
.points-line { color: var(--muted); font-size: 0.97rem; margin: 0; }
.points-line b { color: var(--ink); }

.donut { width: 124px; height: 124px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0.3rem auto; }
.donut-inner {
  width: 92px; height: 92px; border-radius: 50%; background: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 1.55rem; letter-spacing: -0.03em; color: var(--ink);
}

.stat-label { color: var(--muted); font-size: 0.9rem; font-weight: 600; margin: 0 0 0.3rem; }
.timer { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; font-variant-numeric: tabular-nums; color: var(--ink); margin: 0 0 0.5rem; }
.stat-note { color: var(--muted); font-size: 0.92rem; margin: 0; }

.cat { margin-bottom: 1rem; }
.cat-name { display: flex; justify-content: space-between; gap: 1rem; font-size: 0.97rem; font-weight: 600; color: var(--ink); margin-bottom: 0.3rem; }
.cat-pct { font-weight: 800; font-variant-numeric: tabular-nums; }
.bar { background: #E9F0EC; border-radius: 999px; height: 10px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 999px; }
.bar-good { background: var(--lagoon); }
.bar-mid { background: var(--amber); }
.bar-low { background: var(--pen); }

.hl-list { display: flex; flex-wrap: wrap; gap: 0.6rem 1rem; margin: 0.4rem 0 0.5rem; }
.hl {
  padding: 0 0.3rem; font-weight: 700; font-size: 1.08rem; border-radius: 2px;
  background: linear-gradient(transparent 52%, var(--marker) 52%);
}
.hl small { font-weight: 600; color: var(--muted); margin-left: 0.35rem; font-size: 0.85rem; }

@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
</style>
"""


def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)


def fmt(x):
    """Красиво число: 3.0 става 3, а 0.75 си остава 0.75."""
    return f"{round(x, 2):g}"


def format_duration(seconds):
    """Секунди във вид ЧЧ:ММ:СС."""
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def grade_for(percent):
    """Оценка по българската система (2-6) и кратко съобщение."""
    if percent >= 90:
        return "Отличен 6", "Отлична работа! Продължавай все така!"
    if percent >= 75:
        return "Много добър 5", "Много добре! Още малко и си на върха."
    if percent >= 60:
        return "Добър 4", "Добре, но има какво да подобриш."
    if percent >= 50:
        return "Среден 3", "Минаваш, но ти трябва още повторение."
    return "Слаб 2", "Този път не стана. Прегледай слабите теми и опитай пак."


# ---------- Малки части за страниците ----------
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
    """Кръг с процент (рисува се само с CSS)."""
    color = "#087F6C" if percent >= PASS_PERCENT else "#D93B30"
    return (
        f'<div class="donut" style="background: conic-gradient({color} {percent}%, #E8ECEF 0);">'
        f'<div class="donut-inner">{percent}%</div></div>'
    )


def categories_html(topics):
    """Ленти по теми. Цветът показва успеха: зелено, жълто или червено."""
    parts = []
    for topic, (pts, mx) in topics.items():
        pct = round(pts / mx * 100)
        level = "good" if pct >= WEAK_PERCENT else ("mid" if pct >= 40 else "low")
        parts.append(
            '<div class="cat">'
            f'<div class="cat-name"><span>{escape(topic)}</span><span class="cat-pct">{pct}%</span></div>'
            f'<div class="bar"><div class="bar-fill bar-{level}" style="width:{pct}%;"></div></div>'
            "</div>"
        )
    return "<div>" + "".join(parts) + "</div>"


def highlights_html(items):
    """Теми, подчертани с маркер. items = списък от (процент, тема)."""
    spans = "".join(
        f'<span class="hl">{escape(topic)}<small>{pct}%</small></span>' for pct, topic in items
    )
    return f'<div class="hl-list">{spans}</div>'





def show_result(result):
    """Показва резултата. result е речник с всичко за един решен тест."""
    percent = result["percent"]
    passed = percent >= PASS_PERCENT
    grade, message = grade_for(percent)
    grade_word, grade_digit = grade.rsplit(" ", 1)
    topics = result["topics"]

    st.header("Резултат")

    # Оценка като от учител: цифра в кръгче, коментар, процент
    with st.container(key="card_grade"):
        col_stamp, col_text, col_donut = st.columns([1.1, 2.2, 1.2])
        with col_stamp:
            st.markdown(
                f'<div class="stamp-wrap"><div class="stamp">{grade_digit}</div>'
                f'<div class="grade-word">{grade_word}</div></div>',
                unsafe_allow_html=True,
            )
        with col_text:
            pill_class = "status-pass" if passed else "status-fail"
            pill_text = "Издържан тест" if passed else "Неиздържан тест"
            st.markdown(
                f'<div><span class="status-pill {pill_class}">{pill_text}</span>'
                f'<div class="remark">{message}</div>'
                f'<p class="points-line">Точки: <b>{fmt(result["points"])} от {fmt(result["max_points"])}</b></p></div>',
                unsafe_allow_html=True,
            )
        with col_donut:
            st.markdown(donut_html(percent), unsafe_allow_html=True)

    # Време и теми
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
                '<div><p class="stat-label">Успеваемост по теми</p>' + categories_html(topics) + "</div>",
                unsafe_allow_html=True,
            )

    # На какво да наблегнеш
    st.subheader("На какво да наблегнеш")
    weak = []
    for topic, (pts, mx) in topics.items():
        pct = round(pts / mx * 100)
        if pct < WEAK_PERCENT:
            weak.append((pct, topic))
    weak.sort()  # най-слабите първи
    if weak:
        st.markdown(highlights_html(weak), unsafe_allow_html=True)
    else:
        st.success("Всички теми са над 70%. Качи нов материал и провери следващата тема.")

    # Подробно по въпроси
    with st.expander("Прегледай всички отговори"):
        for kind, text in result["feedback"]:
            if kind == "success":
                st.success(text)
            elif kind == "info":
                st.info(text)
            elif kind == "warning":
                st.warning(text)
            else:
                st.error(text)
# ---------- Профил ----------
PROFILE_CSS = """
<style>
.avatar {
  width: 128px; height: 128px; border-radius: 50%; object-fit: cover; display: block;
  border: 4px solid #fff;
  box-shadow: 0 0 0 3px var(--mint), 0 10px 24px -12px rgba(11, 43, 69, 0.5);
}
.avatar-initial {
  width: 128px; height: 128px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #0B2B45, #087F6C);
  color: #fff; font-weight: 800; font-size: 3.2rem;
  border: 4px solid #fff;
  box-shadow: 0 0 0 3px var(--mint), 0 10px 24px -12px rgba(11, 43, 69, 0.5);
}
.profile-name { font-size: 2rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; color: var(--ink); margin: 0.2rem 0 0; }
.profile-meta { color: var(--muted); font-size: 0.95rem; margin: 0.3rem 0 0.9rem; }
.profile-bio { font-size: 1.05rem; line-height: 1.55; max-width: 60ch; color: var(--ink); margin: 0; white-space: pre-wrap; }
.profile-bio-empty { color: var(--muted); }

.test-row { display: flex; align-items: center; gap: 1rem; padding: 0.75rem 0; border-bottom: 1px solid var(--line); }
.test-row:last-child { border-bottom: 0; }
.test-date { flex: 1; color: var(--muted); font-size: 0.95rem; }
.test-grade { font-weight: 700; color: var(--ink); }
.test-pct { min-width: 3.4rem; text-align: center; padding: 0.15rem 0.6rem; border-radius: 999px; font-weight: 800; font-variant-numeric: tabular-nums; }
.pct-good { background: var(--mint); color: var(--lagoon-dark); }
.pct-mid { background: #FFF1CC; color: #8A5A00; }
.pct-low { background: #FDE3E0; color: var(--pen-ink); }
</style>
"""


def apply_profile_style():
    st.markdown(PROFILE_CSS, unsafe_allow_html=True)


def avatar_html(avatar_bytes, username):
    """Снимка в кръгче. Ако няма снимка - първата буква от името."""
    if avatar_bytes:
        encoded = base64.b64encode(avatar_bytes).decode("ascii")
        return (
            f'<img class="avatar" src="data:image/png;base64,{encoded}" '
            f'alt="Профилна снимка на {escape(username)}">'
        )
    return f'<div class="avatar-initial">{escape(username[:1].upper())}</div>'


def profile_info_html(username, member_since, bio):
    """Име, от кога е член и биото."""
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
    """Редове с дата, оценка и процент за списък от тестове."""
    rows = []
    for r in results:
        pct = r["percent"]
        level = "good" if pct >= WEAK_PERCENT else ("mid" if pct >= 40 else "low")
        date = escape(str(r["data"].get("date", r["created_at"])))
        grade = escape(grade_for(pct)[0])
        rows.append(
            f'<div class="test-row"><span class="test-date">{date}</span>'
            f'<span class="test-grade">{grade}</span>'
            f'<span class="test-pct pct-{level}">{pct}%</span></div>'
        )
    return "<div>" + "".join(rows) + "</div>"