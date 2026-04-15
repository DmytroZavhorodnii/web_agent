from browser import Browser
from llm import ask_gemma
from actions import execute
from config import MAX_STEPS, START_URL


def run(instruction: str, start_url: str = START_URL):
    print(f"\n{'='*60}")
    print(f"ZADANIE: {instruction}")
    print(f"URL:     {start_url}")
    print(f"{'='*60}\n")

    browser = Browser()
    browser.goto(start_url)

    history: list[dict] = []

    for step in range(1, MAX_STEPS + 1):
        print(f"── Krok {step}/{MAX_STEPS} {'─'*40}")

        # 1. Pobierz DOM
        dom = browser.get_dom()
        print(f"[DOM] {len(dom)} znaków")

        # 2. Zapytaj Gemmę
        try:
            action = ask_gemma(instruction, dom, history)
        except RuntimeError as e:
            print(f"[LLM ERROR] {e}")
            break

        print(f"[GEMMA] → {action}")

        # 3. Wykonaj akcję
        result = execute(action, browser.page)
        print(f"[WYNIK] {result}")

        # 4. Zapisz krok w historii
        history.append({"action": action, "result": result})

        # 5. Sprawdź czy zadanie zakończone
        if result.startswith("DONE:"):
            print(f"\n{'='*60}")
            print(f"✓ ZADANIE ZAKOŃCZONE")
            print(result)
            print(f"{'='*60}")
            break

        if result.startswith("ERROR:"):
            print(f"[WARN] Akcja zakończyła się błędem, kontynuuję...")

    else:
        print(f"\n[TIMEOUT] Osiągnięto limit {MAX_STEPS} kroków.")

    browser.close()
    return history


# ── Uruchomienie ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Przykładowe zadania — zmień na własne
    run(
        instruction="Znajdź sekcję 'More information' i powiedz mi co się tam znajduje.",
        start_url="https://example.com"
    )
