import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()

MODEL = "gemini-3.5-flash-lite"

LEVELS = {
    "easy": "Въпросите да са лесни: основни факти и определения, директно от текста.",
    "medium": "Въпросите да са със средна трудност: проверяват разбиране, а не само наизустяване.",
    "hard": (
        "Въпросите да са трудни: изискват анализ и връзки между идеи, "
        "а грешните отговори да са правдоподобни."
    ),
}


class Question(BaseModel):
    topic: str
    question: str
    options: list[str]
    correct_indices: list[int]  # индекси от 0 на всички верни отговори
    explanation: str


def _build_prompt(count, difficulty, multi):
    if multi:
        options_rule = (
            "Всеки въпрос има точно 5 възможни отговора, а верните са от 1 до 4 "
            "(различен брой за различните въпроси). В correct_indices изброй "
            "индексите на ВСИЧКИ верни отговори, като броенето започва от 0."
        )
    else:
        options_rule = (
            "Всеки въпрос има точно 4 възможни отговора и само един верен. "
            "В correct_indices сложи само индекса му, като броенето започва от 0."
        )
    return " ".join(
        [
            f"Ти си учител. Направи тест с {count} въпроса върху приложения материал.",
            "Използвай САМО информацията от материала, без външни знания.",
            LEVELS[difficulty],
            options_rule,
            "Групирай въпросите в 3-5 общи теми и за всеки въпрос посочи темата му (1-3 думи).",
            "Една и съща тема винаги се пише с едно и също име.",
            "За всеки въпрос дай и кратко обяснение.",
            "Пиши на езика на материала.",
            "Ако материалът не съдържа учебно съдържание, върни празен списък.",
        ]
    )


def _clean(questions):
    """Маха невалидни индекси и въпроси без верен отговор."""
    cleaned = []
    for q in questions:
        q.correct_indices = sorted({j for j in q.correct_indices if 0 <= j < len(q.options)})
        if q.correct_indices:
            cleaned.append(q)
    return cleaned


def make_test(data, mime_type, count=5, difficulty="medium", multi=False):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Липсва GEMINI_API_KEY във файла .env")

    if mime_type == "text/plain":
        material = data.decode("utf-8", errors="ignore")
    else:
        material = types.Part.from_bytes(data=data, mime_type=mime_type)

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL,
        contents=[material, _build_prompt(count, difficulty, multi)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=list[Question],
        ),
    )
    return _clean(response.parsed or [])
