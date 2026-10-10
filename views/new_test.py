from datetime import datetime

import streamlit as st

from ai import make_test
from database import save_result
from scoring import POINT_VALUES, RULES, evaluate
from ui import page_title, question_head, show_result, step_title

QUESTION_TYPES = {
    "single": "Един верен отговор",
    "multi": "Няколко верни отговора (като на изпит)",
}
DIFFICULTY = {"easy": "Лесен", "medium": "Среден", "hard": "Труден"}
RULE_HINTS = {
    "strict": (
        "Ако сгрешиш каквото и да е в един въпрос (отбележиш грешен отговор "
        "или пропуснеш верен), губиш всичките му точки."
    ),
    "partial": (
        "Частично: (верни избрани − грешни избрани) ÷ брой верни отговори, "
        "не по-малко от 0. Пример: 4 верни, избираш 3 верни = 0,75 от точките."
    ),
}


def render():
    page_title(
        "Нов тест",
        "Качи снимка или документ от учебния си материал. AI прави въпроси само от него.",
    )
    material = _choose_material()
    if material is not None:
        _configure_and_generate(material)
    if "test" in st.session_state:
        _solve(st.session_state["test"], st.session_state["settings"])


def _choose_material():
    step_title(1, "Добави материал")
    source = st.radio(
        "Източник",
        ["Качи файл", "Снимай с камерата"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if source == "Качи файл":
        return st.file_uploader(
            "Избери PDF, текст или снимка",
            type=["pdf", "png", "jpg", "jpeg", "txt"],
        )
    return st.camera_input("Снимай страницата")


def _configure_and_generate(material):
    if material.type.startswith("image"):
        st.image(material, caption="Твоят материал")
    else:
        st.success("Документът е получен.")

    step_title(2, "Настрой теста")
    question_type = st.radio("Вид на въпросите", list(QUESTION_TYPES), format_func=QUESTION_TYPES.get)
    multi = question_type == "multi"

    rule, point_value = "strict", "one"
    if multi:
        rule = st.radio("Как се дават точките?", list(RULES), format_func=RULES.get)
        st.caption(RULE_HINTS[rule])
        point_value = st.radio(
            "Колко точки носи един въпрос?", list(POINT_VALUES), format_func=POINT_VALUES.get
        )

    count_col, level_col = st.columns(2)
    count = count_col.slider("Брой въпроси", 5, 15, 10)
    difficulty = level_col.select_slider(
        "Трудност", options=list(DIFFICULTY), value="medium", format_func=DIFFICULTY.get
    )

    if not st.button("Направи тест", type="primary"):
        return

    with st.spinner("AI чете материала и прави въпроси..."):
        try:
            test = make_test(material.getvalue(), material.type, count, difficulty, multi)
        except Exception as e:
            if "429" in str(e):
                st.error("Достигнат е лимитът на безплатните заявки. Изчакай 1-2 минути и опитай пак.")
            else:
                st.error(f"Тестът не се създаде. Причина: {e}")
            return

    _clear_answers()
    st.session_state["test"] = test
    st.session_state["settings"] = {"multi": multi, "rule": rule, "point_value": point_value}
    st.session_state["started_at"] = datetime.now()
    st.session_state.pop("result", None)


def _clear_answers():
    for key in [k for k in st.session_state if k.startswith("answer_")]:
        del st.session_state[key]


def _solve(test, settings):
    if not test:
        st.warning("От този материал не се получи тест. Опитай с друг, в който има учебен текст.")
        return

    step_title(3, "Реши теста")
    with st.form("quiz"):
        for i, question in enumerate(test):
            _question_card(i, question, settings["multi"])
        submitted = st.form_submit_button("Провери отговорите", type="primary")

    if submitted:
        _check(test, settings)

    if "result" in st.session_state:
        result = st.session_state["result"]
        show_result(result, after_topics=lambda: _retry_wrong(test, result))
        if not st.session_state.get("user"):
            st.info("Влез в профила си (меню → Профил), за да се запазват резултатите ти.")


def _retry_wrong(test, result):
    """Нов тест от въпросите, на които не е отговорено напълно вярно."""
    wrong = [q for q, (kind, _) in zip(test, result["feedback"]) if kind != "success"]
    if not wrong:
        return
    if st.button(f"Повтори грешните въпроси ({len(wrong)})"):
        _clear_answers()
        st.session_state["test"] = wrong
        st.session_state["started_at"] = datetime.now()
        st.session_state.pop("result", None)
        st.rerun()


def _question_card(i, question, multi):
    with st.container(key=f"qcard_{i}"):
        hint = "Избери всички верни отговори" if multi else "Избери един отговор"
        question_head(i + 1, question.question, question.topic, hint)
        if multi:
            for j, option in enumerate(question.options):
                st.checkbox(option, key=f"answer_{i}_{j}")
        else:
            st.radio(
                "Отговор",
                list(range(len(question.options))),
                format_func=lambda j: question.options[j],
                index=None,
                key=f"answer_{i}",
                label_visibility="collapsed",
            )


def _read_answers(test, multi):
    answers = {}
    for i, question in enumerate(test):
        if multi:
            answers[i] = {
                j for j in range(len(question.options)) if st.session_state.get(f"answer_{i}_{j}")
            }
        else:
            chosen = st.session_state.get(f"answer_{i}")
            answers[i] = set() if chosen is None else {chosen}
    return answers


def _check(test, settings):
    finished_at = datetime.now()
    started_at = st.session_state.get("started_at", finished_at)
    result = evaluate(
        test,
        _read_answers(test, settings["multi"]),
        settings["rule"],
        settings["point_value"],
        started_at,
        finished_at,
    )
    st.session_state["result"] = result

    user = st.session_state.get("user")
    if user:
        save_result(user["id"], result)
        st.toast("Резултатът е запазен в профила ти")
    if result["percent"] >= 90:
        st.balloons()