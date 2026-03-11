from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Timer
from urllib.parse import parse_qs, urlparse
import webbrowser

from baza import (
    COLORS,
    MOTHERBOARD_BRANDS,
    RAM_BRANDS,
    build_requirements,
    load_or_generate_data,
    save_set_hms,
    select_best_matches,
)


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DEFAULT_HMS_SIZE = 10
HOST = "127.0.0.1"
PORT = 5000


def _parse_positive_int(raw_value):
    value = (raw_value or "").strip()
    if not value or not value.isdigit():
        return None

    parsed = int(value)
    return parsed if parsed > 0 else None


def _empty_to_none(raw_value):
    value = (raw_value or "").strip()
    return value or None


def _default_form_data():
    return {
        "desired_ddr": "",
        "motherboard_brand": "",
        "ram_brand": "",
        "preferred_color": "",
        "rgb_pref": "",
        "total_budget": "",
        "motherboard_budget": "",
        "ram_budget": "",
        "target_quality": "",
    }


def _serialize_set(item):
    motherboard = item["set"]["motherboard"]
    ram = item["set"]["ram"]
    return {
        "score": round(item["score"], 3),
        "total_price": motherboard["price"] + ram["price"],
        "total_value": motherboard["value"] + ram["value"],
        "motherboard": motherboard,
        "ram": ram,
    }


def _option_list(name, options, selected_value, placeholder, labels=None):
    rendered = [f'<option value="">{escape(placeholder)}</option>']
    labels = labels or {}

    for option in options:
        selected = ' selected' if selected_value == option else ''
        label = labels.get(option, option)
        rendered.append(
            f'<option value="{escape(option)}"{selected}>{escape(label)}</option>'
        )

    return f'<select name="{escape(name)}">{"".join(rendered)}</select>'


def _text_input(name, value, placeholder):
    return (
        f'<input type="number" name="{escape(name)}" min="1" '
        f'value="{escape(value)}" placeholder="{escape(placeholder)}">'
    )


def _render_featured_set(selected_set):
    if not selected_set:
        return ""

    motherboard = selected_set["motherboard"]
    ram = selected_set["ram"]
    return f"""
        <section class=\"card featured-card\">
            <p class=\"eyebrow\">Wylosowany najlepszy kandydat</p>
            <h2>{escape(motherboard['name'])}</h2>
            <p class=\"pairing\">+ {escape(ram['name'])}</p>
            <div class=\"featured-stats\">
                <div>
                    <span>Calkowita cena</span>
                    <strong>{selected_set['total_price']}</strong>
                </div>
                <div>
                    <span>Typ RAM</span>
                    <strong>{escape(motherboard['supported_ram_type'])}</strong>
                </div>
                <div>
                    <span>RGB</span>
                    <strong>{escape(ram['rgb'])}</strong>
                </div>
            </div>
        </section>
    """


def _render_results(results, search_performed):
    if results:
        cards = []
        for item in results:
            cards.append(
                f"""
                <article class=\"result-card\">
                    <div class=\"result-topline\">
                        <span>Score {item['score']}</span>
                        <strong>{item['total_price']}</strong>
                    </div>
                    <h3>{escape(item['motherboard']['name'])}</h3>
                    <p>{escape(item['ram']['name'])}</p>
                    <dl>
                        <div>
                            <dt>Plyta</dt>
                            <dd>{escape(item['motherboard']['brand'])} • {escape(item['motherboard']['color'])} • {escape(item['motherboard']['supported_ram_type'])}</dd>
                        </div>
                        <div>
                            <dt>RAM</dt>
                            <dd>{escape(item['ram']['brand'])} • {escape(item['ram']['color'])} • RGB {escape(item['ram']['rgb'])}</dd>
                        </div>
                        <div>
                            <dt>Value razem</dt>
                            <dd>{item['total_value']}</dd>
                        </div>
                    </dl>
                </article>
                """
            )
        return f'<div class="results-grid">{"".join(cards)}</div>'

    if search_performed:
        return '<p class="empty-state">Brak kompatybilnych zestawow dla podanych wymagan.</p>'

    return '<p class="empty-state">Wybierz parametry po lewej stronie i uruchom ranking.</p>'


def render_page(form_data, results, selected_set, search_performed):
    rgb_labels = {
        "yes": "Tak",
        "no": "Nie",
    }

    return f"""<!DOCTYPE html>
<html lang=\"pl\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Konfigurator zestawu PC</title>
    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
    <link href=\"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap\" rel=\"stylesheet\">
    <link rel=\"stylesheet\" href=\"/static/styles.css\">
</head>
<body>
    <div class=\"page-shell\">
        <header class=\"hero\">
            <div>
                <p class=\"eyebrow\">SI • Konfigurator WWW</p>
                <h1>Dobierz kompatybilna plyte glowna i RAM bez terminala.</h1>
                <p class=\"hero-copy\">Ta strona robi to samo co menu z baza.py, ale w formie lokalnej aplikacji webowej. Wyniki sa dalej zapisywane do pliku hms_sets.csv.</p>
            </div>
            <div class=\"hero-panel\">
                <span>Tryb pracy</span>
                <strong>Harmony Memory Search</strong>
                <p>Ranking pokazuje najlepiej dopasowane zestawy wedlug zgodnosci, ceny i value.</p>
            </div>
        </header>

        <main class=\"layout\">
            <section class=\"card form-card\">
                <h2>Parametry wyszukiwania</h2>
                <form method=\"post\" class=\"config-form\">
                    <label>
                        <span>Typ RAM</span>
                        {_option_list('desired_ddr', ['DDR3', 'DDR4', 'DDR5'], form_data['desired_ddr'], 'Obojetnie')}
                    </label>

                    <label>
                        <span>Marka plyty</span>
                        {_option_list('motherboard_brand', MOTHERBOARD_BRANDS, form_data['motherboard_brand'], 'Obojetnie')}
                    </label>

                    <label>
                        <span>Marka RAM</span>
                        {_option_list('ram_brand', RAM_BRANDS, form_data['ram_brand'], 'Obojetnie')}
                    </label>

                    <label>
                        <span>Kolor</span>
                        {_option_list('preferred_color', COLORS, form_data['preferred_color'], 'Obojetnie')}
                    </label>

                    <label>
                        <span>RGB w RAM</span>
                        {_option_list('rgb_pref', ['yes', 'no'], form_data['rgb_pref'], 'Obojetnie', rgb_labels)}
                    </label>

                    <label>
                        <span>Maksymalny budzet zestawu</span>
                        {_text_input('total_budget', form_data['total_budget'], 'np. 2500')}
                    </label>

                    <label>
                        <span>Maksymalna cena plyty</span>
                        {_text_input('motherboard_budget', form_data['motherboard_budget'], 'np. 1500')}
                    </label>

                    <label>
                        <span>Maksymalna cena RAM</span>
                        {_text_input('ram_budget', form_data['ram_budget'], 'np. 1000')}
                    </label>

                    <label>
                        <span>Docelowa jakosc / value</span>
                        {_text_input('target_quality', form_data['target_quality'], 'np. 80')}
                    </label>

                    <button type=\"submit\">Pokaz najlepsze zestawy</button>
                </form>
            </section>

            <section class=\"results-column\">
                {_render_featured_set(selected_set)}
                <section class=\"card table-card\">
                    <div class=\"table-header\">
                        <div>
                            <p class=\"eyebrow\">Top 10</p>
                            <h2>Ranking dopasowanych zestawow</h2>
                        </div>
                        <span class=\"file-pill\">zapis: hms_sets.csv</span>
                    </div>
                    {_render_results(results, search_performed)}
                </section>
            </section>
        </main>
    </div>
</body>
</html>
"""


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(render_page(_default_form_data(), [], None, False))
            return

        if parsed.path == "/static/styles.css":
            self._send_static(STATIC_DIR / "styles.css", "text/css; charset=utf-8")
            return

        self.send_error(404, "Nie znaleziono strony")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self.send_error(404, "Nie znaleziono strony")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        payload = parse_qs(body, keep_blank_values=True)
        form_data = {
            key: payload.get(key, [""])[0].strip() for key in _default_form_data()
        }

        motherboard_requirements, ram_requirements, hms_size = build_requirements(
            desired_ddr=_empty_to_none(form_data["desired_ddr"]),
            motherboard_brand=_empty_to_none(form_data["motherboard_brand"]),
            ram_brand=_empty_to_none(form_data["ram_brand"]),
            preferred_color=_empty_to_none(form_data["preferred_color"]),
            rgb_pref=_empty_to_none(form_data["rgb_pref"]),
            total_budget=_parse_positive_int(form_data["total_budget"]),
            motherboard_budget=_parse_positive_int(form_data["motherboard_budget"]),
            ram_budget=_parse_positive_int(form_data["ram_budget"]),
            target_quality=_parse_positive_int(form_data["target_quality"]),
            hms_size=DEFAULT_HMS_SIZE,
        )

        motherboards, ram_modules = load_or_generate_data(BASE_DIR)
        result = select_best_matches(
            motherboards,
            ram_modules,
            motherboard_requirements=motherboard_requirements,
            ram_requirements=ram_requirements,
            hms_size=hms_size,
        )

        save_set_hms(BASE_DIR / "hms_sets.csv", result["set_hms"])
        results = [_serialize_set(item) for item in result["set_hms"]]
        selected_set = None

        if result["selected_set"]:
            selected_set = {
                "motherboard": result["selected_set"]["motherboard"],
                "ram": result["selected_set"]["ram"],
                "total_price": result["selected_set"]["motherboard"]["price"] + result["selected_set"]["ram"]["price"],
            }

        self._send_html(render_page(form_data, results, selected_set, True))

    def log_message(self, format, *args):
        return

    def _send_html(self, content):
        payload = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_static(self, file_path, content_type):
        if not file_path.exists():
            self.send_error(404, "Nie znaleziono pliku")
            return

        payload = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def open_browser():
    webbrowser.open_new(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    Timer(1, open_browser).start()
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Serwer uruchomiony: http://{HOST}:{PORT}")
    server.serve_forever()