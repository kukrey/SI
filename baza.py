import csv
import random
import re
from pathlib import Path


MOTHERBOARD_BRANDS = ["ASUS", "MSI", "Gigabyte", "ASRock", "Biostar"]
RAM_BRANDS = ["Corsair", "Kingston", "G.SKILL", "Crucial", "Patriot"]
COLORS = ["black", "white", "silver", "gray"]
SOCKETS = ["LGA1700", "AM5"]
CHIPSETS = ["B650", "X670", "B760", "Z790"]
FORM_FACTORS = ["ATX", "mATX", "Mini-ITX"]
DDR_GENERATIONS = [3, 4, 5]
RAM_SPEEDS = [1333, 1600, 1866, 2133, 3200, 3600, 4000, 5200, 5600, 6000, 6400]
RAM_CAPACITIES = [8, 16, 32, 64]


def _write_products(file_path, products):
    if not products:
        return

    preferred_headers = [
        "name",
        "price",
        "value",
        "type",
        "color",
        "brand",
        "ram_type",
        "rgb",
        "supported_ram_type",
    ]
    headers = [header for header in preferred_headers if header in products[0]]

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(products)


def generate_motherboards(count=1000):
    products = []

    for i in range(1, count + 1):
        brand = random.choice(MOTHERBOARD_BRANDS)
        socket = random.choice(SOCKETS)
        chipset = random.choice(CHIPSETS)
        form_factor = random.choice(FORM_FACTORS)
        supported_ram_type = f"DDR{random.choice(DDR_GENERATIONS)}"
        name = f"{brand} {chipset} {socket} {form_factor} MB-{i:04d}"

        products.append(
            {
                "name": name,
                "price": random.randint(300, 2300),
                "value": random.randint(45, 100),
                "type": "motherboard",
                "color": random.choice(COLORS),
                "brand": brand,
                "supported_ram_type": supported_ram_type,
            }
        )

    return products


def generate_ram_modules(count=1000):
    products = []

    for i in range(1, count + 1):
        brand = random.choice(RAM_BRANDS)
        ddr = random.choice(DDR_GENERATIONS)
        capacity = random.choice(RAM_CAPACITIES)
        speed = random.choice(RAM_SPEEDS)
        kits = random.choice([1, 2, 4])
        name = f"{brand} DDR{ddr} {capacity}GB {speed}MHz {kits}x RAM-{i:04d}"
        ram_type = f"DDR{ddr}"

        base_price = capacity * 12 + (speed // 100) * 4 + kits * 20
        price = max(120, base_price + random.randint(-40, 120))

        products.append(
            {
                "name": name,
                "price": price,
                "value": random.randint(40, 100),
                "type": "ram",
                "color": random.choice(COLORS),
                "brand": brand,
                "ram_type": ram_type,
                "rgb": random.choice(["yes", "no"]),
            }
        )

    return products


def generate_hardware_data(motherboards_count=1000, ram_count=1000, output_dir="."):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    motherboards = generate_motherboards(motherboards_count)
    _write_products(output / "motherboards.csv", motherboards)

    ram_modules = generate_ram_modules(ram_count)
    _write_products(output / "ram.csv", ram_modules)

    return motherboards, ram_modules


def load_products(csv_path):
    products = []

    with open(csv_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            products.append(
                {
                    "name": row["name"],
                    "price": int(row["price"]),
                    "value": int(row["value"]),
                    "type": row["type"],
                    "color": row["color"],
                    "brand": row["brand"],
                    "ram_type": row.get("ram_type", ""),
                    "rgb": row.get("rgb", ""),
                    "supported_ram_type": row.get("supported_ram_type", ""),
                }
            )

    return products


def score_product(product, requirements):
    score = 0.0

    req_type = requirements.get("type")
    if req_type:
        score += 60 if product["type"] == req_type else -200

    preferred_brand = requirements.get("brand")
    if preferred_brand:
        score += 25 if product["brand"] == preferred_brand else 0

    preferred_color = requirements.get("color")
    if preferred_color:
        score += 8 if product["color"] == preferred_color else 0

    preferred_ram_type = requirements.get("ram_type")
    if preferred_ram_type:
        score += 20 if product.get("ram_type") == preferred_ram_type else 0

    preferred_supported_ram_type = requirements.get("supported_ram_type")
    if preferred_supported_ram_type:
        score += 20 if product.get("supported_ram_type") == preferred_supported_ram_type else 0

    preferred_rgb = requirements.get("rgb")
    if preferred_rgb:
        score += 10 if product.get("rgb") == preferred_rgb else 0

    min_value = requirements.get("min_value")
    if min_value is not None:
        score += max(0, product["value"] - min_value)

    target_value = requirements.get("target_value")
    if target_value is not None:
        score += max(0, 20 - abs(product["value"] - target_value))

    max_price = requirements.get("max_price")
    if max_price is not None:
        if product["price"] <= max_price:
            score += 30
            # Under budget gets extra points proportional to savings.
            score += ((max_price - product["price"]) / max_price) * 20
        else:
            score -= (product["price"] - max_price) * 0.15

    target_price = requirements.get("target_price")
    if target_price is not None:
        score += max(0, 25 - abs(product["price"] - target_price) * 0.03)

    return score


def initialize_hms(products, requirements, hms_size=15, candidate_pool=300):
    if not products:
        return []

    sampled_count = min(len(products), max(hms_size, candidate_pool))
    sampled_products = random.sample(products, sampled_count)

    scored = []
    for product in sampled_products:
        scored.append({"score": score_product(product, requirements), "product": product})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[: min(hms_size, len(scored))]


def pick_from_hms(hms, top_n=5):
    if not hms:
        return None

    top = hms[: min(top_n, len(hms))]
    min_score = min(item["score"] for item in top)
    weights = [(item["score"] - min_score) + 1 for item in top]
    chosen = random.choices(top, weights=weights, k=1)[0]
    return chosen["product"]


def pick_set_from_hms(hms, top_n=5):
    if not hms:
        return None

    top = hms[: min(top_n, len(hms))]
    min_score = min(item["score"] for item in top)
    weights = [(item["score"] - min_score) + 1 for item in top]
    return random.choices(top, weights=weights, k=1)[0]["set"]


def _extract_ram_metric(name, pattern, default=0):
    match = re.search(pattern, name)
    if not match:
        return default
    return int(match.group(1))


def score_set(motherboard, ram_module, motherboard_requirements, ram_requirements):
    if motherboard.get("supported_ram_type") != ram_module.get("ram_type"):
        return float("-inf")

    score = 0.0
    score += score_product(motherboard, motherboard_requirements)
    score += score_product(ram_module, ram_requirements)

    # Extra preference for stronger RAM performance in selected sets.
    ram_speed = _extract_ram_metric(ram_module.get("name", ""), r"(\d+)MHz")
    ram_capacity = _extract_ram_metric(ram_module.get("name", ""), r"(\d+)GB")
    score += ram_speed / 400
    score += ram_capacity / 2

    total_price = motherboard["price"] + ram_module["price"]
    max_total_price = (motherboard_requirements.get("max_price") or 0) + (ram_requirements.get("max_price") or 0)
    if max_total_price > 0:
        if total_price <= max_total_price:
            score += 40
            score += ((max_total_price - total_price) / max_total_price) * 40
        else:
            score -= (total_price - max_total_price) * 0.2

    return score


def initialize_set_hms(
    motherboards,
    ram_modules,
    motherboard_requirements,
    ram_requirements,
    hms_size=15,
    motherboard_pool=120,
    ram_pool=180,
):
    if not motherboards or not ram_modules:
        return []

    sampled_motherboards = random.sample(motherboards, min(len(motherboards), motherboard_pool))
    sampled_ram_modules = random.sample(ram_modules, min(len(ram_modules), ram_pool))

    scored_sets = []
    for motherboard in sampled_motherboards:
        for ram_module in sampled_ram_modules:
            if motherboard.get("supported_ram_type") != ram_module.get("ram_type"):
                continue

            set_score = score_set(motherboard, ram_module, motherboard_requirements, ram_requirements)
            if set_score == float("-inf"):
                continue

            scored_sets.append(
                {
                    "score": set_score,
                    "set": {
                        "motherboard": motherboard,
                        "ram": ram_module,
                    },
                }
            )

    if scored_sets:
        min_raw = min(item["score"] for item in scored_sets)
        max_raw = max(item["score"] for item in scored_sets)

        if max_raw == min_raw:
            for item in scored_sets:
                item["score"] = 100.0
        else:
            for item in scored_sets:
                normalized_score = ((item["score"] - min_raw) / (max_raw - min_raw)) * 100
                item["score"] = normalized_score

    scored_sets.sort(
        key=lambda item: (
            -item["score"],
            item["set"]["motherboard"]["price"] + item["set"]["ram"]["price"],
            -(item["set"]["motherboard"]["value"] + item["set"]["ram"]["value"]),
        )
    )
    return scored_sets[: min(hms_size, len(scored_sets))]


def save_hms(file_path, hms):
    if not hms:
        return

    preferred_headers = [
        "name",
        "price",
        "value",
        "type",
        "color",
        "brand",
        "ram_type",
        "rgb",
        "supported_ram_type",
    ]
    product_headers = [header for header in preferred_headers if header in hms[0]["product"]]
    headers = product_headers + ["score"]
    rows = []
    for item in hms:
        row = dict(item["product"])
        row["score"] = round(item["score"], 3)
        rows.append(row)

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def save_set_hms(file_path, set_hms):
    if not set_hms:
        return

    headers = [
        "motherboard_name",
        "motherboard_brand",
        "motherboard_color",
        "motherboard_supported_ram_type",
        "motherboard_price",
        "motherboard_value",
        "ram_name",
        "ram_brand",
        "ram_color",
        "ram_type",
        "ram_rgb",
        "ram_price",
        "ram_value",
        "total_price",
        "total_value",
        "score",
    ]

    rows = []
    for item in set_hms:
        motherboard = item["set"]["motherboard"]
        ram = item["set"]["ram"]

        rows.append(
            {
                "motherboard_name": motherboard["name"],
                "motherboard_brand": motherboard["brand"],
                "motherboard_color": motherboard["color"],
                "motherboard_supported_ram_type": motherboard["supported_ram_type"],
                "motherboard_price": motherboard["price"],
                "motherboard_value": motherboard["value"],
                "ram_name": ram["name"],
                "ram_brand": ram["brand"],
                "ram_color": ram["color"],
                "ram_type": ram["ram_type"],
                "ram_rgb": ram["rgb"],
                "ram_price": ram["price"],
                "ram_value": ram["value"],
                "total_price": motherboard["price"] + ram["price"],
                "total_value": motherboard["value"] + ram["value"],
                "score": round(item["score"], 3),
            }
        )

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def select_best_matches(motherboards, ram_modules, motherboard_requirements, ram_requirements, hms_size=15):
    set_hms = initialize_set_hms(
        motherboards,
        ram_modules,
        motherboard_requirements,
        ram_requirements,
        hms_size=hms_size,
    )

    selected_set = pick_set_from_hms(set_hms)

    selected_motherboard = selected_set["motherboard"] if selected_set else None
    selected_ram = selected_set["ram"] if selected_set else None

    return {
        "selected_motherboard": selected_motherboard,
        "selected_ram": selected_ram,
        "selected_set": selected_set,
        "set_hms": set_hms,
    }


def _prompt_choice(label, options, allow_skip=True):
    options_text = "/".join(options)
    skip_hint = " (Enter = obojetnie)" if allow_skip else ""

    while True:
        value = input(f"{label} [{options_text}]{skip_hint}: ").strip()
        if not value and allow_skip:
            return None

        for option in options:
            if value.lower() == option.lower():
                return option

        print("Niepoprawna opcja. Sprobuj ponownie.")


def _prompt_int(label, allow_skip=True, minimum=None):
    skip_hint = " (Enter = pomin)" if allow_skip else ""

    while True:
        value = input(f"{label}{skip_hint}: ").strip()
        if not value and allow_skip:
            return None

        if value.isdigit():
            number = int(value)
            if minimum is None or number >= minimum:
                return number

        print("Wpisz poprawna liczbe calkowita.")


def build_requirements(
    desired_ddr=None,
    motherboard_brand=None,
    ram_brand=None,
    preferred_color=None,
    rgb_pref=None,
    total_budget=None,
    motherboard_budget=None,
    ram_budget=None,
    target_quality=None,
    hms_size=10,
):
    if total_budget is not None:
        if motherboard_budget is None:
            motherboard_budget = int(total_budget * 0.6)
        if ram_budget is None:
            ram_budget = total_budget - motherboard_budget
            if ram_budget <= 0:
                ram_budget = max(1, int(total_budget * 0.4))

    motherboard_requirements = {
        "type": "motherboard",
    }
    ram_requirements = {
        "type": "ram",
    }

    if desired_ddr:
        motherboard_requirements["supported_ram_type"] = desired_ddr
        ram_requirements["ram_type"] = desired_ddr

    if motherboard_brand:
        motherboard_requirements["brand"] = motherboard_brand

    if ram_brand:
        ram_requirements["brand"] = ram_brand

    if preferred_color:
        motherboard_requirements["color"] = preferred_color
        ram_requirements["color"] = preferred_color

    if rgb_pref:
        ram_requirements["rgb"] = rgb_pref

    if motherboard_budget is not None:
        motherboard_requirements["max_price"] = motherboard_budget

    if ram_budget is not None:
        ram_requirements["max_price"] = ram_budget

    if target_quality is not None:
        motherboard_requirements["target_value"] = target_quality
        ram_requirements["target_value"] = target_quality

    return motherboard_requirements, ram_requirements, hms_size


def load_or_generate_data(base_dir=None, motherboards_count=1000, ram_count=1000):
    output_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent
    motherboards_path = output_dir / "motherboards.csv"
    ram_path = output_dir / "ram.csv"

    if motherboards_path.exists() and ram_path.exists():
        return load_products(motherboards_path), load_products(ram_path)

    return generate_hardware_data(
        motherboards_count=motherboards_count,
        ram_count=ram_count,
        output_dir=output_dir,
    )


def build_requirements_from_menu():
    print("\n=== KONFIGURATOR CELU ZESTAWU (PLYTA + RAM) ===")

    desired_ddr = _prompt_choice("Typ RAM", ["DDR3", "DDR4", "DDR5"], allow_skip=True)
    motherboard_brand = _prompt_choice("Marka plyty", MOTHERBOARD_BRANDS, allow_skip=True)
    ram_brand = _prompt_choice("Marka RAM", RAM_BRANDS, allow_skip=True)
    preferred_color = _prompt_choice("Kolor", COLORS, allow_skip=True)
    rgb_pref = _prompt_choice("RAM z RGB", ["yes", "no"], allow_skip=True)

    total_budget = _prompt_int("Maksymalny budzet calego zestawu", allow_skip=True, minimum=1)
    motherboard_budget = _prompt_int("Maksymalna cena plyty", allow_skip=True, minimum=1)
    ram_budget = _prompt_int("Maksymalna cena RAM", allow_skip=True, minimum=1)

    target_quality = _prompt_int("Docelowa jakosc/value (np. 80)", allow_skip=True, minimum=1)
    return build_requirements(
        desired_ddr=desired_ddr,
        motherboard_brand=motherboard_brand,
        ram_brand=ram_brand,
        preferred_color=preferred_color,
        rgb_pref=rgb_pref,
        total_budget=total_budget,
        motherboard_budget=motherboard_budget,
        ram_budget=ram_budget,
        target_quality=target_quality,
        hms_size=10,
    )


def print_set_results(set_hms, limit=5):
    if not set_hms:
        print("Brak kompatybilnych zestawow dla podanych wymagan.")
        return

    print("\n=== NAJLEPSZE ZESTAWY ===")
    for idx, item in enumerate(set_hms[:limit], start=1):
        motherboard = item["set"]["motherboard"]
        ram = item["set"]["ram"]
        total_price = motherboard["price"] + ram["price"]
        print(
            f"{idx}. SCORE={item['score']:.3f} | CENA={total_price} | "
            f"PLYTA: {motherboard['name']} ({motherboard['supported_ram_type']}) | "
            f"RAM: {ram['name']} (RGB: {ram['rgb']})"
        )


if __name__ == "__main__":
    generated_motherboards, generated_ram = load_or_generate_data()

    motherboard_req, ram_req, hms_size = build_requirements_from_menu()

    result = select_best_matches(
        generated_motherboards,
        generated_ram,
        motherboard_requirements=motherboard_req,
        ram_requirements=ram_req,
        hms_size=hms_size,
    )

    save_set_hms("hms_sets.csv", result["set_hms"])
    print_set_results(result["set_hms"], limit=hms_size)
    print("\nZapisano ranking do pliku: hms_sets.csv")