from pathlib import Path

import streamlit as st

from database import init_db
from ui import apply_style
from views import history, new_test, profile

ICON_PATH = Path(__file__).resolve().parent / "assets" / "icon.png"

st.set_page_config(
    page_title="Quizify",
    page_icon=str(ICON_PATH) if ICON_PATH.exists() else "📚",
    layout="wide",
)
apply_style()
init_db()

PAGES = {
    "Нов тест": new_test.render,
    "История": history.render,
    "Профил": profile.render,
}

with st.sidebar:
    if ICON_PATH.exists():
        st.image(str(ICON_PATH), width=84)
    st.markdown(
        '<div class="brand">Quizify</div><div class="brand-sub">Тест от твоите записки</div>',
        unsafe_allow_html=True,
    )
    page = st.radio("Меню", list(PAGES), label_visibility="collapsed")
    st.divider()
    user = st.session_state.get("user")
    if user:
        st.caption(f"Влязъл като **{user['username']}**")
    else:
        st.caption("Гост. Резултатите не се запазват.")

PAGES[page]()
