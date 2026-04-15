import requests
import json
import re
from config import OLLAMA_URL, OLLAMA_MODEL
from actions import ACTIONS


SYSTEM_PROMPT = f"""Jesteś autonomicznym agentem webowym. 
Dostajesz zadanie od użytkownika, uproszczone drzewo DOM bieżącej strony 
oraz historię poprzednich akcji.

Twój cel: wykonać zadanie krok po kroku wybierając JEDNĄ akcję na raz.

Dostępne akcje:
{ACTIONS}

ZASADY:
- Odpowiadaj WYŁĄCZNIE jedną linią zawierającą akcję, np: click(3)
- Nie dodawaj żadnych wyjaśnień, komentarzy ani formatowania
- Używaj tylko elementów widocznych w DOM (mają atrybut [id=N])
- Gdy zadanie jest wykonane, użyj done("twoja odpowiedź")
- Jeśli utkniesz w pętli, spróbuj innej metody
"""


def build_user_message(instruction: str, dom: str, history: list[dict]) -> str:
    history_text = ""
    if history:
        history_text = "\n\nHISTORIA AKCJI:\n"
        for i, h in enumerate(history[-5:]):  # ostatnie 5 kroków
            history_text += f"Krok {i+1}: {h['action']} → {h['result']}\n"

    return f"""ZADANIE: {instruction}

AKTUALNY DOM:
{dom[:3000]}
{history_text}
Twoja następna akcja:"""


def ask_gemma(instruction: str, dom: str, history: list[dict]) -> str:
    """Wysyła zapytanie do Ollama i zwraca akcję jako string."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": build_user_message(instruction, dom, history)},
    ]

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,   # niska temperatura = deterministyczne akcje
            "num_predict": 50,    # akcja to max kilka tokenów
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        raw = data["message"]["content"].strip()
        return _clean_action(raw)
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Nie można połączyć się z Ollama. "
            "Uruchom: ollama serve  oraz  ollama pull gemma3"
        )
    except Exception as e:
        raise RuntimeError(f"Błąd Ollama: {e}")


def _clean_action(raw: str) -> str:
    """
    Gemma czasem dodaje markdown lub tekst przed akcją.
    Wyciągamy samą linię z akcją.
    """
    # usuń bloki ```
    raw = re.sub(r"```.*?```", "", raw, flags=re.DOTALL).strip()
    # weź pierwszą niepustą linię
    for line in raw.splitlines():
        line = line.strip()
        if line:
            return line
    return raw
