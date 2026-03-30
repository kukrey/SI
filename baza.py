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
        score += 25 if product["brand"] == preferred_brand else -8

    preferred_color = requirements.get("color")
    if preferred_color:
        score += 8 if product["color"] == preferred_color else -3

    preferred_ram_type = requirements.get("ram_type")
    if preferred_ram_type:
        score += 20 if product.get("ram_type") == preferred_ram_type else -12

    preferred_supported_ram_type = requirements.get("supported_ram_type")
    if preferred_supported_ram_type:
        score += 20 if product.get("supported_ram_type") == preferred_supported_ram_type else -12

    preferred_rgb = requirements.get("rgb")
    if preferred_rgb:
        score += 10 if product.get("rgb") == preferred_rgb else -4

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


def is_product_valid(product):
    product_type = product.get("type")
    if product_type not in {"motherboard", "ram"}:
        return False

    if not product.get("name"):
        return False

    if product.get("price", 0) <= 0:
        return False

    if product.get("value", 0) < 0:
        return False

    if product_type == "motherboard" and not product.get("supported_ram_type"):
        return False

    if product_type == "ram" and not product.get("ram_type"):
        return False

    return True


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


def _score_exact_match(actual, expected, weight):
    if not expected:
        return 0.0, 0.0
    return (weight if actual == expected else 0.0), float(weight)


def _score_budget_match(price, max_price, weight):
    if max_price is None:
        return 0.0, 0.0

    safe_limit = max(1, max_price)
    overflow_ratio = max(0.0, (price - safe_limit) / safe_limit)
    matched = max(0.0, weight * (1.0 - overflow_ratio))
    return matched, float(weight)


def _score_target_value_match(value, target_value, weight):
    if target_value is None:
        return 0.0, 0.0

    safe_target = max(1, target_value)
    diff_ratio = abs(value - safe_target) / safe_target
    matched = max(0.0, weight * (1.0 - diff_ratio))
    return matched, float(weight)


def _score_min_value_match(value, min_value, weight):
    if min_value is None:
        return 0.0, 0.0

    safe_min = max(1, min_value)
    ratio = min(1.0, value / safe_min)
    matched = max(0.0, weight * ratio)
    return matched, float(weight)


def score_set(motherboard, ram_module, motherboard_requirements, ram_requirements):
    if not is_product_valid(motherboard):
        return float("-inf")

    if not is_product_valid(ram_module):
        return float("-inf")

    if motherboard.get("supported_ram_type") != ram_module.get("ram_type"):
        return float("-inf")

    matched_points = 0.0
    possible_points = 0.0

    # Zgodnosc cech plyty.
    for matched, possible in (
        _score_exact_match(motherboard.get("brand"), motherboard_requirements.get("brand"), 12),
        _score_exact_match(motherboard.get("color"), motherboard_requirements.get("color"), 7),
        _score_exact_match(
            motherboard.get("supported_ram_type"),
            motherboard_requirements.get("supported_ram_type"),
            15,
        ),
        _score_budget_match(motherboard.get("price", 0), motherboard_requirements.get("max_price"), 20),
        _score_target_value_match(motherboard.get("value", 0), motherboard_requirements.get("target_value"), 8),
        _score_min_value_match(motherboard.get("value", 0), motherboard_requirements.get("min_value"), 8),
    ):
        matched_points += matched
        possible_points += possible

    # Zgodnosc cech RAM.
    for matched, possible in (
        _score_exact_match(ram_module.get("brand"), ram_requirements.get("brand"), 12),
        _score_exact_match(ram_module.get("color"), ram_requirements.get("color"), 7),
        _score_exact_match(ram_module.get("ram_type"), ram_requirements.get("ram_type"), 15),
        _score_exact_match(ram_module.get("rgb"), ram_requirements.get("rgb"), 8),
        _score_budget_match(ram_module.get("price", 0), ram_requirements.get("max_price"), 20),
        _score_target_value_match(ram_module.get("value", 0), ram_requirements.get("target_value"), 8),
        _score_min_value_match(ram_module.get("value", 0), ram_requirements.get("min_value"), 8),
    ):
        matched_points += matched
        possible_points += possible

    # Zgodnosc budzetu calego zestawu.
    total_price = motherboard["price"] + ram_module["price"]
    max_total_price = (motherboard_requirements.get("max_price") or 0) + (ram_requirements.get("max_price") or 0)
    matched, possible = _score_budget_match(total_price, max_total_price if max_total_price > 0 else None, 25)
    matched_points += matched
    possible_points += possible

    # Dodatkowe lekkie kryteria jakosciowe (zawsze aktywne, male wagi).
    ram_speed = _extract_ram_metric(ram_module.get("name", ""), r"(\d+)MHz")
    ram_capacity = _extract_ram_metric(ram_module.get("name", ""), r"(\d+)GB")

    quality_possible = 8.0
    speed_component = min(1.0, ram_speed / 6400) * 4.0
    capacity_component = min(1.0, ram_capacity / 64) * 4.0
    matched_points += speed_component + capacity_component
    possible_points += quality_possible

    if possible_points <= 0:
        return 0.0

    return (matched_points / possible_points) * 100.0


def initialize_set_hms(
    motherboards,
    ram_modules,
    motherboard_requirements,
    ram_requirements,
    hms_size=10,
    motherboard_pool=180,
    ram_pool=700,
    ram_candidates_per_motherboard=140,
):
    if not motherboards or not ram_modules:
        return []

    # Liczymy procent podobienstwa dla wszystkich kompatybilnych par.
    valid_motherboards = [motherboard for motherboard in motherboards if is_product_valid(motherboard)]
    valid_ram_modules = [ram_module for ram_module in ram_modules if is_product_valid(ram_module)]

    if not valid_motherboards or not valid_ram_modules:
        return []

    ram_by_type = {}
    for ram_module in valid_ram_modules:
        ram_type = ram_module.get("ram_type")
        if not ram_type:
            continue
        ram_by_type.setdefault(ram_type, []).append(ram_module)

    scored_sets = []
    for motherboard in valid_motherboards:
        compatible_rams = ram_by_type.get(motherboard.get("supported_ram_type"), [])
        if not compatible_rams:
            continue

        for ram_module in compatible_rams:
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

    scored_sets.sort(
        key=lambda item: (
            -item["score"],
            item["set"]["motherboard"]["price"] + item["set"]["ram"]["price"],
            -(item["set"]["motherboard"]["value"] + item["set"]["ram"]["value"]),
        )
    )
    return scored_sets[: min(hms_size, len(scored_sets))]


def _build_scored_set(motherboard, ram_module, motherboard_requirements, ram_requirements):
    set_score = score_set(motherboard, ram_module, motherboard_requirements, ram_requirements)
    if set_score == float("-inf"):
        return None

    return {
        "score": set_score,
        "set": {
            "motherboard": motherboard,
            "ram": ram_module,
        },
    }


def _random_scored_set(valid_motherboards, ram_by_type, motherboard_requirements, ram_requirements):
    if not valid_motherboards or not ram_by_type:
        return None

    random_motherboard = random.choice(valid_motherboards)
    compatible_rams = ram_by_type.get(random_motherboard.get("supported_ram_type"), [])
    if not compatible_rams:
        return None

    random_ram = random.choice(compatible_rams)
    return _build_scored_set(random_motherboard, random_ram, motherboard_requirements, ram_requirements)


def initialize_set_hms_iterative(
    motherboards,
    ram_modules,
    motherboard_requirements,
    ram_requirements,
    hms_size=10,
    elite_ratio=0.35,
    max_iterations=100000,
):
    valid_motherboards = [motherboard for motherboard in motherboards if is_product_valid(motherboard)]
    valid_ram_modules = [ram_module for ram_module in ram_modules if is_product_valid(ram_module)]

    if not valid_motherboards or not valid_ram_modules:
        return {
            "set_hms": [],
            "initial_random_set": None,
            "iteration_trace": [],
        }

    ram_by_type = {}
    for ram_module in valid_ram_modules:
        ram_type = ram_module.get("ram_type")
        if ram_type:
            ram_by_type.setdefault(ram_type, []).append(ram_module)

    set_hms = []
    attempts = 0
    max_attempts = 100000

    while len(set_hms) < hms_size and attempts < max_attempts:
        attempts += 1
        random_set = _random_scored_set(
            valid_motherboards,
            ram_by_type,
            motherboard_requirements,
            ram_requirements,
        )
        if random_set is not None:
            set_hms.append(random_set)

    if not set_hms:
        return {
            "set_hms": [],
            "initial_random_set": None,
            "iteration_trace": [],
        }

    initial_random_set = set_hms[0]
    iteration_trace = []

    for iteration in range(1, max_iterations + 1):
        set_hms.sort(key=lambda item: item["score"], reverse=True)
        best_before = set_hms[0]["score"]

        elite_count = max(1, int(round(hms_size * elite_ratio)))
        elite_count = min(elite_count, len(set_hms))
        elite = set_hms[:elite_count]

        new_population = list(elite)
        refill_attempts = 0
        refill_target = hms_size
        max_refill_attempts = 100000

        while len(new_population) < refill_target and refill_attempts < max_refill_attempts:
            refill_attempts += 1
            random_set = _random_scored_set(
                valid_motherboards,
                ram_by_type,
                motherboard_requirements,
                ram_requirements,
            )
            if random_set is not None:
                new_population.append(random_set)

        if new_population:
            new_population.sort(key=lambda item: item["score"], reverse=True)
            set_hms = new_population[:hms_size]

            best_after = set_hms[0]["score"]
            iteration_trace.append(
                {
                    "iteration": iteration,
                    "elite_kept": elite_count,
                    "best_before": round(best_before, 3),
                    "best_after": round(best_after, 3),
                }
            )

    set_hms.sort(
        key=lambda item: (
            -item["score"],
            item["set"]["motherboard"]["price"] + item["set"]["ram"]["price"],
            -(item["set"]["motherboard"]["value"] + item["set"]["ram"]["value"]),
        )
    )

    return {
        "set_hms": set_hms[: min(hms_size, len(set_hms))],
        "initial_random_set": initial_random_set,
        "iteration_trace": iteration_trace,
    }


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


def search_random_solutions(
    motherboards,
    ram_modules,
    motherboard_requirements,
    ram_requirements,
    solutions_count=10,
    iterations=10000,
    show_progress=True,
):
    """Tworzy losowe top N i ulepsza je przez zadana liczbe iteracji."""
    valid_motherboards = [mb for mb in motherboards if is_product_valid(mb)]
    valid_ram_modules = [ram for ram in ram_modules if is_product_valid(ram)]

    if not valid_motherboards or not valid_ram_modules:
        return [], {
            "total": 0,
            "compatible": 0,
            "valid": 0,
            "incompatible": 0,
        }

    best_solutions = {}
    attempts = 0
    compatible_attempts = 0
    max_initial_attempts = max(10000, solutions_count * 500)

    if show_progress:
        print(f"\n[LOSOWE WYSZUKIWANIE] Tworze top {solutions_count} kompatybilnych rozwiazan")
        print(f"  Etap 1: losowanie startowe, Etap 2: {iterations} iteracji ulepszania\n")

    # Etap 1: wypelnij poczatkowe top N kompatybilnymi parami.
    while len(best_solutions) < solutions_count and attempts < max_initial_attempts:
        attempts += 1

        motherboard = random.choice(valid_motherboards)
        ram_module = random.choice(valid_ram_modules)

        # Sprawdź czy para jest kompatybilna (zgodne DDR)
        is_compatible = motherboard.get("supported_ram_type") == ram_module.get("ram_type")

        if not is_compatible:
            continue

        compatible_attempts += 1
        set_score = score_set(motherboard, ram_module, motherboard_requirements, ram_requirements)
        if set_score != float("-inf"):
            solution_key = (motherboard["name"], ram_module["name"])
            candidate = {
                "score": set_score,
                "set": {
                    "motherboard": motherboard,
                    "ram": ram_module,
                },
                "is_compatible": True,
            }

            existing = best_solutions.get(solution_key)
            if existing is None or candidate["score"] > existing["score"]:
                best_solutions[solution_key] = candidate

    # Etap 2: iteracyjne losowe ulepszanie top N.
    for _ in range(iterations):
        attempts += 1

        motherboard = random.choice(valid_motherboards)
        ram_module = random.choice(valid_ram_modules)
        if motherboard.get("supported_ram_type") != ram_module.get("ram_type"):
            continue

        compatible_attempts += 1
        set_score = score_set(motherboard, ram_module, motherboard_requirements, ram_requirements)
        if set_score == float("-inf"):
            continue

        solution_key = (motherboard["name"], ram_module["name"])
        candidate = {
            "score": set_score,
            "set": {
                "motherboard": motherboard,
                "ram": ram_module,
            },
            "is_compatible": True,
        }

        existing = best_solutions.get(solution_key)
        if existing is not None:
            if candidate["score"] > existing["score"]:
                best_solutions[solution_key] = candidate
            continue

        if len(best_solutions) < solutions_count:
            best_solutions[solution_key] = candidate
            continue

        worst_key = min(best_solutions, key=lambda key: best_solutions[key]["score"])
        if candidate["score"] > best_solutions[worst_key]["score"]:
            del best_solutions[worst_key]
            best_solutions[solution_key] = candidate

    all_solutions = sorted(best_solutions.values(), key=lambda x: x["score"], reverse=True)
    all_solutions = all_solutions[:solutions_count]

    if show_progress:
        print(f"\n  [OK] Znaleziono {len(all_solutions)} kompatybilnych rozwiazan")
        print(f"  [OK] Laczna liczba prob: {attempts}")
        print(f"  [OK] Proby kompatybilne: {compatible_attempts}")
        print(f"  [OK] Iteracje ulepszania: {iterations}")

        if all_solutions:
            best = all_solutions[0]
            mb = best["set"]["motherboard"]
            ram = best["set"]["ram"]
            total_price = mb["price"] + ram["price"]
            print(f"\n  >> NAJLEPSZE ROZWIAZANIE:")
            print(f"    Score: {best['score']:.3f}%")
            print(f"    Plyta: {mb['name']} ({mb['supported_ram_type']})")
            print(f"    RAM: {ram['name']} ({ram['ram_type']})")
            print(f"    Cena calkowita: {total_price} zl")
        print()

    stats = {
        "total": len(all_solutions),
        "compatible": len(all_solutions),
        "valid": len(all_solutions),
        "incompatible": 0,
        "attempts": attempts,
        "iterations": iterations,
    }

    return all_solutions, stats


def select_best_matches(motherboards, ram_modules, motherboard_requirements, ram_requirements, hms_size=10):
    iterative_result = initialize_set_hms_iterative(
        motherboards,
        ram_modules,
        motherboard_requirements,
        ram_requirements,
        hms_size=hms_size,
    )
    set_hms = iterative_result["set_hms"]

    selected_set = pick_set_from_hms(set_hms)

    selected_motherboard = selected_set["motherboard"] if selected_set else None
    selected_ram = selected_set["ram"] if selected_set else None

    return {
        "selected_motherboard": selected_motherboard,
        "selected_ram": selected_ram,
        "selected_set": selected_set,
        "set_hms": set_hms,
        "initial_random_set": iterative_result["initial_random_set"],
        "iteration_trace": iterative_result["iteration_trace"],
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