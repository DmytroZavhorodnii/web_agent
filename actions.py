from playwright.sync_api import Page
import time


# ── lista dostępnych akcji (to samo co w prompcie dla Gemmy) ──────────────────
ACTIONS = "" "
click(id)                  – kliknij element o podanym id
type(id, text)             – wpisz tekst w pole o podanym id
scroll(direction)          – przewiń stronę: direction = "up" lub "down"
go_back()                  – wróć do poprzedniej strony
goto(url)                  – przejdź pod podany url
submit(id)                 – kliknij przycisk submit / naciśnij Enter w polu
wait()                     – zaczekaj chwilę (strona się ładuje)
done(message)              – zakończ zadanie i zwróć odpowiedź
"""


def execute(action_str: str, page: Page) -> str:
    """
    Parsuje i wykonuje akcję zwróconą przez Gemmę.
    Zwraca krótki opis co zostało wykonane lub błąd.
    """
    action_str = action_str.strip()

    try:
        # ── click(id) ──────────────────────────────────────────────────────────
        if action_str.startswith("click("):
            agent_id = _extract_args(action_str)[0]
            el = page.query_selector(f'[data-agentid="{agent_id}"]')
            if el is None:
                return f"ERROR: element id={agent_id} nie istnieje"
            el.scroll_into_view_if_needed()
            el.click()
            page.wait_for_load_state("domcontentloaded")
            return f"OK: kliknięto element id={agent_id}"

        # ── type(id, text) ─────────────────────────────────────────────────────
        elif action_str.startswith("type("):
            args = _extract_args(action_str)
            agent_id, text = args[0], args[1]
            el = page.query_selector(f'[data-agentid="{agent_id}"]')
            if el is None:
                return f"ERROR: element id={agent_id} nie istnieje"
            el.click()
            el.fill(text)
            return f"OK: wpisano '{text}' w element id={agent_id}"

        # ── scroll(direction) ──────────────────────────────────────────────────
        elif action_str.startswith("scroll("):
            direction = _extract_args(action_str)[0].strip('"').strip("'")
            dy = -600 if direction == "up" else 600
            page.mouse.wheel(0, dy)
            time.sleep(0.5)
            return f"OK: przewinięto {direction}"

        # ── go_back() ──────────────────────────────────────────────────────────
        elif action_str.startswith("go_back"):
            page.go_back(wait_until="domcontentloaded")
            return "OK: wróciło do poprzedniej strony"

        # ── goto(url) ──────────────────────────────────────────────────────────
        elif action_str.startswith("goto("):
            url = _extract_args(action_str)[0].strip('"').strip("'")
            page.goto(url, wait_until="domcontentloaded")
            return f"OK: przeszło na {url}"

        # ── submit(id) ─────────────────────────────────────────────────────────
        elif action_str.startswith("submit("):
            agent_id = _extract_args(action_str)[0]
            el = page.query_selector(f'[data-agentid="{agent_id}"]')
            if el is None:
                return f"ERROR: element id={agent_id} nie istnieje"
            el.press("Enter")
            page.wait_for_load_state("domcontentloaded")
            return f"OK: submit na element id={agent_id}"

        # ── wait() ─────────────────────────────────────────────────────────────
        elif action_str.startswith("wait"):
            time.sleep(2)
            return "OK: czekano 2 sekundy"

        # ── done(message) ──────────────────────────────────────────────────────
        elif action_str.startswith("done("):
            message = _extract_args(action_str)[0]
            return f"DONE: {message}"

        else:
            return f"ERROR: nieznana akcja '{action_str}'"

    except Exception as e:
        return f"ERROR: {e}"


def _extract_args(action_str: str) -> list[str]:
    """Wyciąga argumenty z stringa w stylu func(a, b, c)."""
    inner = action_str[action_str.index("(") + 1 : action_str.rindex(")")]
    # split po pierwszym przecinku (żeby tekst z przecinkami nie był dzielony)
    parts = inner.split(",", 1)
    return [p.strip().strip('"').strip("'") for p in parts]
