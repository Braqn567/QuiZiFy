import re
from datetime import datetime
from io import BytesIO

import streamlit as st
from PIL import Image, ImageOps

from database import (
    change_password,
    count_friends,
    create_user,
    get_profile,
    list_results,
    update_profile,
    verify_user,
)
from ui import avatar_html, page_title, profile_info_html, recent_tests_html

MAX_PHOTO_BYTES = 5 * 1024 * 1024
AVATAR_SIZE = (256, 256)
MIN_PASSWORD_LENGTH = 8
USERNAME_PATTERN = re.compile(r"\w{3,30}")


def render():
    user = st.session_state.get("user")
    if user:
        _show_profile(user)
    else:
        _show_login()


# ---------- Вход и регистрация ----------

def _show_login():
    page_title("Влез в Quizify", "Профилът запазва резултатите ти и показва как напредваш.")
    with st.container(key="card_auth"):
        login_tab, register_tab = st.tabs(["Вход", "Регистрация"])
        with login_tab:
            _login_form()
        with register_tab:
            _register_form()


def _login_form():
    with st.form("login_form"):
        username = st.text_input("Потребителско име")
        password = st.text_input("Парола", type="password")
        submitted = st.form_submit_button("Влез", type="primary")
    if not submitted:
        return
    user = verify_user(username, password)
    if user:
        st.session_state["user"] = user
        st.rerun()
    st.error("Грешно потребителско име или парола.")


def _register_form():
    with st.form("register_form"):
        username = st.text_input("Избери потребителско име")
        password = st.text_input("Парола (поне 8 символа)", type="password")
        repeat = st.text_input("Повтори паролата", type="password")
        submitted = st.form_submit_button("Създай профил", type="primary")
    if not submitted:
        return

    error = _username_error(username) or _password_error(password, repeat)
    if error:
        st.error(error)
    elif create_user(username, password):
        st.session_state["user"] = verify_user(username, password)
        st.rerun()
    else:
        st.error("Това име вече е заето. Избери друго.")


def _username_error(username):
    if not USERNAME_PATTERN.fullmatch(username.strip()):
        return "Името е от 3 до 30 символа: букви, цифри или _ (без интервали)."
    return None


def _password_error(password, repeat):
    if len(password) < MIN_PASSWORD_LENGTH:
        return "Паролата трябва да е поне 8 символа."
    if password != repeat:
        return "Двете пароли не съвпадат."
    return None


# ---------- Профил ----------

def _show_profile(user):
    profile = get_profile(user["id"])
    results = list_results(user["id"])

    page_title("Профил")
    if st.session_state.pop("profile_saved", False):
        st.success("Профилът е запазен.")

    _header_card(profile)
    _stats(results, count_friends(user["id"]))
    _recent_tests(results)
    _edit_form(user, profile)
    _password_form(user)

    if st.button("Изход"):
        for key in ("user", "test", "result", "settings"):
            st.session_state.pop(key, None)
        st.rerun()


def _header_card(profile):
    member_since = datetime.fromisoformat(profile["created_at"]).strftime("%d.%m.%Y")
    with st.container(key="card_profile"):
        avatar_col, info_col = st.columns([1, 3])
        avatar_col.markdown(
            avatar_html(profile["avatar"], profile["username"]), unsafe_allow_html=True
        )
        info_col.markdown(
            profile_info_html(profile["username"], member_since, profile["bio"]),
            unsafe_allow_html=True,
        )


def _stats(results, friends):
    tests_col, friends_col, average_col = st.columns(3)
    tests_col.metric("Решени тестове", len(results))
    friends_col.metric("Приятели", friends)
    if results:
        average = round(sum(r["percent"] for r in results) / len(results))
        average_col.metric("Среден резултат", f"{average}%")
    else:
        average_col.metric("Среден резултат", "няма")
    st.caption("Добавянето на приятели идва скоро.")


def _recent_tests(results):
    st.subheader("Последни тестове")
    if not results:
        st.info("Още няма решени тестове. Започни от „Нов тест“.")
        return
    st.markdown(recent_tests_html(results[:5]), unsafe_allow_html=True)
    st.caption("Всички тестове и графиката на прогреса са в „История“.")


def _edit_form(user, profile):
    with st.expander("Редактирай профила"):
        # номерът в ключа се сменя след запазване, за да се изчисти полето за снимка
        upload_number = st.session_state.get("avatar_upload_n", 0)
        with st.form("profile_form"):
            photo = st.file_uploader(
                "Профилна снимка (PNG или JPG)",
                type=["png", "jpg", "jpeg"],
                key=f"avatar_upload_{upload_number}",
            )
            bio = st.text_area(
                "Био",
                value=profile["bio"],
                max_chars=200,
                height=110,
                placeholder="Няколко думи за теб. Например какво учиш.",
            )
            submitted = st.form_submit_button("Запази промените", type="primary")
        if not submitted:
            return

        avatar = None
        if photo is not None:
            raw = photo.getvalue()
            if len(raw) > MAX_PHOTO_BYTES:
                st.error("Снимката е над 5 MB. Избери по-малка.")
                return
            try:
                avatar = _make_avatar(raw)
            except Exception:
                st.error("Файлът не е валидна снимка. Опитай с PNG или JPG.")
                return

        update_profile(user["id"], bio.strip(), avatar)
        st.session_state["avatar_upload_n"] = upload_number + 1
        st.session_state["profile_saved"] = True
        st.rerun()


def _password_form(user):
    with st.expander("Смяна на парола"):
        with st.form("password_form"):
            current = st.text_input("Сегашна парола", type="password")
            new = st.text_input("Нова парола (поне 8 символа)", type="password")
            repeat = st.text_input("Повтори новата парола", type="password")
            submitted = st.form_submit_button("Смени паролата", type="primary")
        if not submitted:
            return

        error = _password_error(new, repeat)
        if error:
            st.error(error)
        elif new == current:
            st.error("Новата парола трябва да е различна от сегашната.")
        elif change_password(user["id"], current, new):
            st.success("Паролата е сменена.")
        else:
            st.error("Сегашната парола не е вярна.")


def _make_avatar(raw_bytes):
    """Изрязва снимката на квадрат и я връща като PNG байтове."""
    image = Image.open(BytesIO(raw_bytes))
    image = ImageOps.exif_transpose(image).convert("RGB")
    image = ImageOps.fit(image, AVATAR_SIZE, Image.Resampling.LANCZOS)
    out = BytesIO()
    image.save(out, format="PNG")
    return out.getvalue()