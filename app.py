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
    search_random_solutions,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_HMS_SIZE = 10
HOST = "127.0.0.1"
PORT = 5000

STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0a0a0f;
  --bg-card: #111118;
  --bg-input: #16161f;
  --bg-hover: #1c1c28;
  --border: rgba(255,255,255,0.07);
  --border-accent: rgba(99,102,241,0.4);
  --text: #f0f0f8;
  --text2: #8888aa;
  --text3: #55556a;
  --accent: #6366f1;
  --accent2: #22d3ee;
  --green: #10b981;
  --r: 12px;
  --rs: 8px;
  --font: 'Outfit', system-ui, sans-serif;
  --mono: 'JetBrains Mono', monospace;
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 15px;
  line-height: 1.6;
  min-height: 100vh;
}

.shell {
  max-width: 1320px;
  margin: 0 auto;
  padding: 0 24px 80px;
}

.hero {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 40px;
  align-items: start;
  padding: 52px 0 44px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 36px;
}

.hero-eyebrow {
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.hero-eyebrow::before {
  content: '';
  display: inline-block;
  width: 20px;
  height: 1px;
  background: var(--accent);
}

.hero h1 {
  font-size: clamp(24px, 3vw, 36px);
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.2;
  margin-bottom: 14px;
}
.hero h1 span { color: var(--accent); }

.hero-copy { font-size: 14px; color: var(--text2); max-width: 480px; }
.hero-copy code {
  font-family: var(--mono);
  font-size: 12px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--accent2);
}

.hero-badge {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 20px 24px;
  min-width: 220px;
}
.hero-badge .badge-label {
  font-size: 10px;
  font-family: var(--mono);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text3);
  display: block;
  margin-bottom: 6px;
}
.hero-badge .badge-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--accent2);
  display: block;
  margin-bottom: 10px;
}
.hero-badge .badge-desc { font-size: 12px; color: var(--text2); line-height: 1.5; }

.layout {
  display: grid;
  grid-template-columns: 290px 1fr;
  gap: 22px;
  align-items: start;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 22px;
}

.form-card h2 {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text3);
  font-family: var(--mono);
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}

.config-form { display: flex; flex-direction: column; gap: 13px; }
.config-form label { display: flex; flex-direction: column; gap: 5px; }
.config-form label span { font-size: 12px; font-weight: 500; color: var(--text2); }

.config-form select,
.config-form input[type="number"] {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--rs);
  color: var(--text);
  font-family: var(--font);
  font-size: 14px;
  padding: 9px 12px;
  width: 100%;
  transition: border-color 0.15s;
  -webkit-appearance: none;
  appearance: none;
}
.config-form select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='7' viewBox='0 0 10 7'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%2355556a' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 30px;
}
.config-form select:focus,
.config-form input[type="number"]:focus {
  outline: none;
  border-color: var(--border-accent);
}
.config-form input[type="number"]::-webkit-inner-spin-button,
.config-form input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; }

.config-form button[type="submit"] {
  margin-top: 8px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--rs);
  font-family: var(--font);
  font-size: 14px;
  font-weight: 600;
  padding: 12px;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
  letter-spacing: 0.02em;
}
.config-form button[type="submit"]:hover { opacity: 0.88; }
.config-form button[type="submit"]:active { transform: scale(0.98); }

.results-column { display: flex; flex-direction: column; gap: 18px; }

.featured-card { border-color: var(--border-accent); position: relative; overflow: hidden; }
.featured-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
}

.eyebrow {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 9px;
}

.featured-card h2,
.random-start-card h2 { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.pairing { font-size: 13px; color: var(--text2); margin-bottom: 16px; }

.featured-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 14px;
}
.featured-stats > div {
  background: var(--bg-input);
  border-radius: var(--rs);
  padding: 11px 13px;
}
.featured-stats span {
  display: block;
  font-size: 10px;
  color: var(--text3);
  margin-bottom: 4px;
  font-family: var(--mono);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.featured-stats strong { display: block; font-size: 14px; font-weight: 600; }

.random-start-card { position: relative; overflow: hidden; border-color: rgba(34,211,238,0.2); }
.random-start-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent2), transparent);
}
.random-start-card .eyebrow { color: var(--accent2); }

.table-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}
.table-header h2 { font-size: 16px; font-weight: 600; margin-top: 4px; }

.file-pill {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 999px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text3);
  padding: 4px 12px;
  white-space: nowrap;
}

.trace-table-wrap { overflow-x: auto; }
.trace-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.trace-table th {
  text-align: left;
  padding: 7px 11px;
  font-family: var(--mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text3);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
.trace-table td {
  padding: 8px 11px;
  color: var(--text2);
  border-bottom: 1px solid var(--border);
}
.trace-table tr:last-child td { border-bottom: none; }
.trace-table tr:hover td { background: var(--bg-hover); color: var(--text); }
.trace-table td:first-child { color: var(--accent); font-family: var(--mono); font-weight: 500; }
.delta-pos { color: var(--green) !important; }
.delta-neg { color: #f87171 !important; }

.results-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 11px; }

.result-card {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--rs);
  padding: 15px;
  transition: border-color 0.15s, background 0.15s;
}
.result-card:hover { border-color: rgba(255,255,255,0.12); background: var(--bg-hover); }

.result-topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 9px;
}
.result-topline span {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--green);
  background: rgba(16,185,129,0.1);
  padding: 2px 8px;
  border-radius: 999px;
}
.result-topline strong { font-size: 15px; font-weight: 700; }

.result-card h3 {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.result-card > p {
  font-size: 12px;
  color: var(--text2);
  margin-bottom: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.result-card dl { display: grid; gap: 4px; }
.result-card dl > div { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.result-card dt { font-size: 11px; color: var(--text3); font-family: var(--mono); white-space: nowrap; flex-shrink: 0; }
.result-card dd { font-size: 11px; color: var(--text2); text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.empty-state { font-size: 14px; color: var(--text3); padding: 32px 0; text-align: center; }

@media (max-width: 960px) {
  .hero { grid-template-columns: 1fr; }
  .layout { grid-template-columns: 1fr; }
  .results-grid { grid-template-columns: 1fr; }
  .featured-stats { grid-template-columns: repeat(2, 1fr); }
}
</style>
"""


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
        "desired_ddr": "DDR3",
        "motherboard_brand": MOTHERBOARD_BRANDS[0],
        "ram_brand": RAM_BRANDS[0],
        "preferred_color": COLORS[0],
        "rgb_pref": "yes",
        "total_budget": "",
        "motherboard_budget": "",
        "ram_budget": "",
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
    rendered = []
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
        <section class="card featured-card">
            <p class="eyebrow">&#9733; Najlepsze dopasowanie</p>
            <h2>{escape(motherboard['name'])}</h2>
            <p class="pairing">+ {escape(ram['name'])}</p>
            <div class="featured-stats">
                <div>
                    <span>Cena zestawu</span>
                    <strong>{selected_set['total_price']} z&#322;</strong>
                </div>
                <div>
                    <span>Typ RAM</span>
                    <strong>{escape(motherboard['supported_ram_type'])}</strong>
                </div>
                <div>
                    <span>RGB</span>
                    <strong>{'Tak' if ram['rgb'] == 'yes' else 'Nie'}</strong>
                </div>
            </div>
        </section>
    """


def _render_random_stats(stats):
    if not stats:
        return ""

    attempts = stats.get("attempts", 0)

    return f"""
        <section class="card random-start-card">
            <p class="eyebrow">&#128256; Statystyki losowania</p>
            <h2>{stats["total"]} kompatybilnych rozwiązań</h2>
            <p class="pairing">Wielokrotne losowanie aż do znalezienia zgodnych par</p>
            <div class="featured-stats">
                <div>
                    <span>Znalezione rozwiązania</span>
                    <strong>{stats["total"]} par</strong>
                </div>
                <div>
                    <span>Liczba prób</span>
                    <strong>{attempts}</strong>
                </div>
                <div>
                    <span>Zgodny DDR</span>
                    <strong>100%</strong>
                </div>
            </div>
        </section>
    """


def _render_initial_random_set(initial_random_set):
    if not initial_random_set:
        return ""
    motherboard = initial_random_set["set"]["motherboard"]
    ram = initial_random_set["set"]["ram"]
    total_price = motherboard["price"] + ram["price"]
    return f"""
        <section class="card random-start-card">
            <p class="eyebrow">Punkt startowy algorytmu</p>
            <h2>{escape(motherboard['name'])}</h2>
            <p class="pairing">+ {escape(ram['name'])}</p>
            <div class="featured-stats">
                <div>
                    <span>Score startowy</span>
                    <strong>{round(initial_random_set['score'], 3)}%</strong>
                </div>
                <div>
                    <span>Cena zestawu</span>
                    <strong>{total_price} z&#322;</strong>
                </div>
                <div>
                    <span>Typ RAM</span>
                    <strong>{escape(ram['ram_type'])}</strong>
                </div>
            </div>
        </section>
    """


def _render_iteration_trace(iteration_trace):
    if not iteration_trace:
        return ""
    rows = []
    for step in iteration_trace[:12]:
        delta = round(step['best_after'] - step['best_before'], 3)
        delta_class = "delta-pos" if delta >= 0 else "delta-neg"
        delta_str = f"+{delta}" if delta >= 0 else str(delta)
        rows.append(f"""
            <tr>
                <td>{step['iteration']}</td>
                <td>{step['elite_kept']}</td>
                <td>{step['best_before']}%</td>
                <td>{step['best_after']}%</td>
                <td class="{delta_class}">{delta_str}%</td>
            </tr>
        """)
    shown = min(12, len(iteration_trace))
    return f"""
        <section class="card trace-card">
            <div class="table-header">
                <div>
                    <p class="eyebrow">Przebieg optymalizacji</p>
                    <h2>Iteracje algorytmu HMS</h2>
                </div>
                <span class="file-pill">pokazane: {shown} / {len(iteration_trace)}</span>
            </div>
            <div class="trace-table-wrap">
                <table class="trace-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Elite</th>
                            <th>Score przed</th>
                            <th>Score po</th>
                            <th>Delta</th>
                        </tr>
                    </thead>
                    <tbody>{''.join(rows)}</tbody>
                </table>
            </div>
        </section>
    """


def _render_results(results, search_performed):
    if results:
        cards = []
        for item in results:
            rgb_text = 'Tak' if item['ram']['rgb'] == 'yes' else 'Nie'
            cards.append(f"""
                <article class="result-card">
                    <div class="result-topline">
                        <span>Score {item['score']}%</span>
                        <strong>{item['total_price']} z&#322;</strong>
                    </div>
                    <h3>{escape(item['motherboard']['name'])}</h3>
                    <p>{escape(item['ram']['name'])}</p>
                    <dl>
                        <div>
                            <dt>P&#322;yta</dt>
                            <dd>{escape(item['motherboard']['brand'])} &middot; {escape(item['motherboard']['color'])} &middot; {escape(item['motherboard']['supported_ram_type'])}</dd>
                        </div>
                        <div>
                            <dt>Cena p&#322;yty</dt>
                            <dd>{item['motherboard']['price']} z&#322;</dd>
                        </div>
                        <div>
                            <dt>RAM</dt>
                            <dd>{escape(item['ram']['brand'])} &middot; {escape(item['ram']['color'])} &middot; RGB: {rgb_text}</dd>
                        </div>
                        <div>
                            <dt>Cena RAM</dt>
                            <dd>{item['ram']['price']} z&#322;</dd>
                        </div>
                    </dl>
                </article>
            """)
        return f'<div class="results-grid">{"".join(cards)}</div>'

    if search_performed:
        return '<p class="empty-state">Brak kompatybilnych zestawów dla podanych wymagań.</p>'

    return '<p class="empty-state">Wybierz parametry po lewej stronie i uruchom ranking.</p>'


def render_page(form_data, results, selected_set, random_stats, iteration_trace, search_performed):
    rgb_labels = {"yes": "Tak", "no": "Nie"}

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Konfigurator PC &mdash; P&#322;yta + RAM</title>
    {STYLES}
</head>
<body>
    <div class="shell">
        <header class="hero">
            <div>
                <p class="hero-eyebrow">SI &mdash; Konfigurator zestawu PC</p>
                <h1>Dobierz <span>p&#322;yt&#281; g&#322;ówn&#261;</span><br>i RAM w kilka sekund.</h1>
                <p class="hero-copy">
                    Algorytm Harmony Memory Search przeszukuje tysi&#261;ce kombinacji
                    i wy&#322;ania zestawy najlepiej pasuj&#261;ce do Twoich wymaga&#324;.
                    Wyniki trafiaj&#261; automatycznie do pliku <code>hms_sets.csv</code>.
                </p>
            </div>
            <div class="hero-badge">
                <span class="badge-label">Tryb pracy</span>
                <strong class="badge-value">Harmony Memory Search</strong>
                <p class="badge-desc">Ranking wed&#322;ug zgodno&#347;ci DDR, bud&#380;etu, marki i jako&#347;ci.</p>
            </div>
        </header>

        <main class="layout">
            <section class="card form-card">
                <h2>Parametry</h2>
                <form method="post" class="config-form">
                    <label>
                        <span>Typ RAM</span>
                        {_option_list('desired_ddr', ['DDR3', 'DDR4', 'DDR5'], form_data['desired_ddr'], 'Obojętnie')}
                    </label>
                    <label>
                        <span>Marka p&#322;yty</span>
                        {_option_list('motherboard_brand', MOTHERBOARD_BRANDS, form_data['motherboard_brand'], 'Obojętnie')}
                    </label>
                    <label>
                        <span>Marka RAM</span>
                        {_option_list('ram_brand', RAM_BRANDS, form_data['ram_brand'], 'Obojętnie')}
                    </label>
                    <label>
                        <span>Kolor</span>
                        {_option_list('preferred_color', COLORS, form_data['preferred_color'], 'Obojętnie')}
                    </label>
                    <label>
                        <span>RGB w RAM</span>
                        {_option_list('rgb_pref', ['yes', 'no'], form_data['rgb_pref'], 'Obojętnie', rgb_labels)}
                    </label>
                    <label>
                        <span>Bud&#380;et ca&#322;kowity (z&#322;)</span>
                        {_text_input('total_budget', form_data['total_budget'], 'np. 2500')}
                    </label>
                    <label>
                        <span>Max cena p&#322;yty (z&#322;)</span>
                        {_text_input('motherboard_budget', form_data['motherboard_budget'], 'np. 1500')}
                    </label>
                    <label>
                        <span>Max cena RAM (z&#322;)</span>
                        {_text_input('ram_budget', form_data['ram_budget'], 'np. 1000')}
                    </label>
                    <button type="submit">Szukaj najlepszych zestawów &rarr;</button>
                </form>
            </section>

            <section class="results-column">
                {_render_random_stats(random_stats)}
                {_render_featured_set(selected_set)}
                <section class="card table-card">
                    <div class="table-header">
                        <div>
                            <p class="eyebrow">Wyniki</p>
                            <h2>Znalezione zestawy (posortowane)</h2>
                        </div>
                        <span class="file-pill">zapis: hms_sets.csv i random_solutions_10.csv</span>
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
            self._send_html(render_page(_default_form_data(), [], None, None, [], False))
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
            hms_size=DEFAULT_HMS_SIZE,
        )

        motherboards, ram_modules = load_or_generate_data(BASE_DIR)

        print("\n" + "="*70)
        print("URUCHAMIANIE ALGORYTMU LOSOWEGO WYSZUKIWANIA")
        print("="*70)

        # Znajdz 10 losowych rozwiazan i ulepszaj przez 10000 iteracji.
        all_solutions, stats = search_random_solutions(
            motherboards,
            ram_modules,
            motherboard_requirements=motherboard_requirements,
            ram_requirements=ram_requirements,
            solutions_count=10,
            iterations=10000,
            show_progress=True,
        )

        # Zapisz wszystkie rozwiazania do pliku.
        save_set_hms(BASE_DIR / "random_solutions_10.csv", all_solutions)
        print(f"[OK] Zapisano {len(all_solutions)} rozwiazan do pliku: random_solutions_10.csv")

        # Zapisz również do hms_sets.csv (wszystkie znalezione)
        save_set_hms(BASE_DIR / "hms_sets.csv", all_solutions)

        results = [_serialize_set(item) for item in all_solutions]
        selected_set = None

        if all_solutions:
            best = all_solutions[0]["set"]
            selected_set = {
                "motherboard": best["motherboard"],
                "ram": best["ram"],
                "total_price": best["motherboard"]["price"] + best["ram"]["price"],
            }

        print("="*70 + "\n")

        self._send_html(
            render_page(
                form_data,
                results,
                selected_set,
                stats,  # Przekazujemy statystyki
                [],    # iteration_trace - nie używane
                True,
            )
        )

    def log_message(self, format, *args):
        return

    def _send_html(self, content):
        payload = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
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