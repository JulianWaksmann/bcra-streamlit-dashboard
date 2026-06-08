#!/usr/bin/env python3
"""Build Streamlit-ready BCRA level metrics by entity and segment.

The output grain is entity + segment + situation level. A debtor is counted
inside each entity where it appears, so the same CUIT can count once in Galicia
and once in Macro. Amounts are the exposure of that debtor in that entity only.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

from build_bcra_deudores import (
    EXPECTED_DEUDORES_LEN,
    SITUACION_LABELS,
    SLICES,
    amount_to_csv,
    clean_text,
    parse_amount_tenths,
    parse_int,
    read_fixed_lines,
)


COMPANY_PREFIXES = {"30", "33", "34"}
KNOWN_LEVELS = ["0", "1", "2", "3", "4", "5", "11"]
LEVEL_ORDER = {"0": 0, "1": 1, "11": 1, "2": 2, "3": 3, "4": 4, "5": 5}


def load_entities(input_dir: Path) -> dict[str, str]:
    entities = {}
    for line in read_fixed_lines(input_dir / "Maeent.txt"):
        code = line[:5].strip()
        entities[code] = clean_text(line[5:])
    return entities


def sector_for_entity(code: str) -> str:
    try:
        return "No Financiero" if int(code) >= 50000 else "Financiero"
    except ValueError:
        return "Sin clasificar"


def segment_for_id(nro_id: str) -> str:
    return "Empresas" if nro_id[:2] in COMPANY_PREFIXES else "Familias"


def normalize_situation(raw_value: str) -> str:
    situation = str(parse_int(raw_value))
    return situation if situation else "0"


def max_situation(current: str, candidate: str) -> str:
    return candidate if LEVEL_ORDER.get(candidate, 0) > LEVEL_ORDER.get(current, 0) else current


def exposure_tenths(line: str) -> int:
    return (
        parse_amount_tenths(line[SLICES["prestamos_total_garantias_afrontadas"]])
        + parse_amount_tenths(line[SLICES["garantias_otorgadas"]])
        + parse_amount_tenths(line[SLICES["otros_conceptos"]])
    )


def new_metric() -> dict[str, int]:
    return {
        "deudores": 0,
        "monto_tenths": 0,
        "registros_origen": 0,
    }


def add_metric(
    metrics: dict[tuple[str, str, str, str], dict[str, int]],
    period: str,
    entity: str,
    segment: str,
    situation: str,
    amount_tenths: int,
    source_rows: int,
) -> None:
    metric = metrics[(period, entity, segment, situation)]
    metric["deudores"] += 1
    metric["monto_tenths"] += amount_tenths
    metric["registros_origen"] += source_rows


def flush_debtor_entity(
    metrics: dict[tuple[str, str, str, str], dict[str, int]],
    current: dict[str, str | int] | None,
) -> None:
    if current is None:
        return

    period = str(current["period"])
    entity = str(current["entity"])
    segment = str(current["segment"])
    situation = str(current["situation"])
    amount_tenths = int(current["amount_tenths"])
    source_rows = int(current["source_rows"])

    add_metric(metrics, period, entity, segment, situation, amount_tenths, source_rows)
    add_metric(metrics, period, entity, "Total", situation, amount_tenths, source_rows)


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00"
    return f"{numerator / denominator * 100:.2f}"


def write_csv(path: Path, rows: list[dict[str, str | int]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build(input_dir: Path, output_dir: Path, period_filter: str, progress_every: int) -> dict[str, str | int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    entities = load_entities(input_dir)
    metrics: dict[tuple[str, str, str, str], dict[str, int]] = defaultdict(new_metric)

    total_rows = 0
    included_rows = 0
    skipped_period_rows = 0
    bad_length_rows = 0
    consolidated_entity_debtors = 0
    duplicate_source_rows = 0
    out_of_order_rows = 0
    unknown_situation_rows = 0
    previous_key: tuple[str, str, str] | None = None
    current: dict[str, str | int] | None = None

    for line in read_fixed_lines(input_dir / "deudores.txt"):
        total_rows += 1
        if len(line) != EXPECTED_DEUDORES_LEN:
            bad_length_rows += 1
            continue

        period = line[SLICES["fecha_info"]].strip()
        if period_filter and period != period_filter:
            skipped_period_rows += 1
            continue

        included_rows += 1
        entity = line[SLICES["codigo_entidad"]].strip()
        nro_id = line[SLICES["nro_id"]].strip()
        key = (period, entity, nro_id)

        if previous_key is not None and key < previous_key:
            out_of_order_rows += 1
        previous_key = key

        situation = normalize_situation(line[SLICES["situacion_codigo"]])
        if situation not in KNOWN_LEVELS:
            unknown_situation_rows += 1

        amount_tenths = exposure_tenths(line)

        if current is not None and key == current["key"]:
            current["amount_tenths"] = int(current["amount_tenths"]) + amount_tenths
            current["source_rows"] = int(current["source_rows"]) + 1
            current["situation"] = max_situation(str(current["situation"]), situation)
            duplicate_source_rows += 1
        else:
            flush_debtor_entity(metrics, current)
            if current is not None:
                consolidated_entity_debtors += 1
            current = {
                "key": key,
                "period": period,
                "entity": entity,
                "segment": segment_for_id(nro_id),
                "situation": situation,
                "amount_tenths": amount_tenths,
                "source_rows": 1,
            }

        if progress_every and total_rows % progress_every == 0:
            print(f"processed {total_rows:,} rows", file=sys.stderr)

    flush_debtor_entity(metrics, current)
    if current is not None:
        consolidated_entity_debtors += 1

    rows = []
    totals_by_group: dict[tuple[str, str, str], dict[str, int]] = defaultdict(new_metric)
    for (period, entity, segment, situation), metric in metrics.items():
        totals_by_group[(period, entity, segment)]["deudores"] += metric["deudores"]
        totals_by_group[(period, entity, segment)]["monto_tenths"] += metric["monto_tenths"]
        totals_by_group[(period, entity, segment)]["registros_origen"] += metric["registros_origen"]

    for key in sorted(metrics):
        period, entity, segment, situation = key
        metric = metrics[key]
        total_metric = totals_by_group[(period, entity, segment)]
        amount = metric["monto_tenths"]
        debtors = metric["deudores"]
        average_tenths = 0 if debtors == 0 else round(amount / debtors)
        rows.append(
            {
                "fecha_info": period,
                "codigo_entidad": entity,
                "nombre_entidad": entities.get(entity, ""),
                "sector": sector_for_entity(entity),
                "tipo_segmento": segment,
                "situacion_codigo": situation,
                "situacion_descripcion": SITUACION_LABELS.get(situation, "Sin situacion / no informada"),
                "deudores": debtors,
                "monto_total_miles_pesos": amount_to_csv(amount),
                "monto_promedio_miles_pesos": amount_to_csv(average_tenths),
                "pct_deudores_segmento": pct(debtors, total_metric["deudores"]),
                "pct_monto_segmento": pct(amount, total_metric["monto_tenths"]),
                "registros_origen": metric["registros_origen"],
            }
        )

    output_path = output_dir / "streamlit_morosidad_niveles_202604.csv"
    write_csv(output_path, rows)

    manifest = {
        "total_rows": total_rows,
        "included_rows": included_rows,
        "period_filter": period_filter or "all",
        "skipped_period_rows": skipped_period_rows,
        "bad_length_rows": bad_length_rows,
        "consolidated_entity_debtors": consolidated_entity_debtors,
        "duplicate_source_rows_same_entity_debtor": duplicate_source_rows,
        "out_of_order_rows": out_of_order_rows,
        "unknown_situation_rows": unknown_situation_rows,
        "level_metrics": str(output_path),
    }
    (output_dir / "manifest_streamlit_levels.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("202604"))
    parser.add_argument("--output-dir", type=Path, default=Path("202604/streamlit"))
    parser.add_argument("--period", default="202604")
    parser.add_argument("--progress-every", type=int, default=5_000_000)
    args = parser.parse_args()
    print(json.dumps(build(args.input_dir, args.output_dir, args.period, args.progress_every), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
