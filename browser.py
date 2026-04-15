from playwright.sync_api import sync_playwright, Page
from config import HEADLESS, START_URL


class Browser:
    def __init__(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=HEADLESS)
        self._page: Page = self._browser.new_page()

    def goto(self, url: str = START_URL):
        self._page.goto(url, wait_until="domcontentloaded")

    @property
    def page(self) -> Page:
        return self._page

    def get_dom(self) -> str:
        """
        Zwraca uproszczone drzewo DOM jako tekst.
        Każdy interaktywny element dostaje unikalny [id].
        Pomija niewidoczne węzły i irrelewantne tagi.
        """
        raw = self._page.evaluate("""
        () => {
            const SKIP = new Set(['script','style','noscript','svg','head','meta','link']);
            const INTERACTIVE = new Set(['a','button','input','select','textarea']);
            let counter = 0;
            const lines = [];

            function walk(node, depth) {
                if (node.nodeType === Node.TEXT_NODE) {
                    const text = node.textContent.trim();
                    if (text.length > 0 && text.length < 200) {
                        lines.push('  '.repeat(depth) + text);
                    }
                    return;
                }
                if (node.nodeType !== Node.ELEMENT_NODE) return;

                const tag = node.tagName.toLowerCase();
                if (SKIP.has(tag)) return;

                // pomiń niewidoczne
                const style = window.getComputedStyle(node);
                if (style.display === 'none' || style.visibility === 'hidden') return;

                let attrs = '';
                if (INTERACTIVE.has(tag)) {
                    counter++;
                    node.setAttribute('data-agentid', String(counter));
                    const type = node.getAttribute('type') || '';
                    const placeholder = node.getAttribute('placeholder') || '';
                    const href = node.getAttribute('href') || '';
                    const value = node.value || '';
                    attrs = ` [id=${counter}]`;
                    if (type)        attrs += ` type="${type}"`;
                    if (placeholder) attrs += ` placeholder="${placeholder}"`;
                    if (href)        attrs += ` href="${href.substring(0,60)}"`;
                    if (value)       attrs += ` value="${value}"`;
                }

                const text = Array.from(node.childNodes)
                    .filter(n => n.nodeType === Node.TEXT_NODE)
                    .map(n => n.textContent.trim())
                    .join(' ')
                    .substring(0, 100);

                const line = '  '.repeat(depth) + `<${tag}${attrs}>${text ? ' ' + text : ''}`;
                lines.push(line);

                for (const child of node.childNodes) {
                    walk(child, depth + 1);
                }
            }

            walk(document.body, 0);
            return lines.join('\\n');
        }
        """)
        return raw

    def close(self):
        self._browser.close()
        self._pw.stop()
