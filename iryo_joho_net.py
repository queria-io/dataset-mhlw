"""医療情報ネット（ナビイ）オープンデータの取得・整形。

医療情報ネットは、全国の病院・診療所・歯科診療所・助産所・薬局の情報を、半年ごと
（6 月 1 日・12 月 1 日時点）に CSV（zip）で公開している。施設の種類ごとに
施設票（1 施設 1 行）があり、病院・診療所・歯科診療所には診療科・診療時間票
（施設 × 診療科 × 時間帯）がある。

本モジュールは最新の時点の CSV を取得し、次の 2 本の NDJSON を書き出す。

- 施設: 5 種類の施設票の共通の列（名称・所在地・緯度経度・ホームページ・病床数）。
  休診日・営業日の列は持たない
- 診療科: 診療科・診療時間票の施設 × 診療科（時間帯の重複を除く）。診療時間は持たない

ID は医療情報ネットが振る施設の番号で、保険医療機関コードではない。
"""

import csv
import io
import json
import re
import zipfile
from pathlib import Path

from shared.fetch import fetch, replacing

PAGE_URL = "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryou/newpage_43373.html"
BASE_URL = "https://www.mhlw.go.jp"

FACILITY_FILES = [
    "01-1_hospital_facility_info",
    "02-1_clinic_facility_info",
    "03-1_dental_facility_info",
    "04_maternity_home",
    "05_pharmacy",
]
SPECIALITY_FILES = [
    "01-2_hospital_speciality_hours",
    "02-2_clinic_speciality_hours",
    "03-2_dental_speciality_hours",
]

# 出力の列 → 元の列名の候補。薬局の施設票だけ名称の列名が異なる
FACILITY_COLUMNS = {
    "id": ["ID"],
    "facility_type_code": ["機関区分"],
    "name": ["正式名称", "名称"],
    "name_kana": ["正式名称（フリガナ）", "フリガナ"],
    "short_name": ["略称"],
    "short_name_kana": ["略称（フリガナ）"],
    "name_en": ["英語表記（ローマ字表記）", "ローマ字"],
    "prefecture_code": ["都道府県コード"],
    "municipality_code": ["市区町村コード"],
    "address": ["所在地"],
    "latitude": ["所在地座標（緯度）"],
    "longitude": ["所在地座標（経度）"],
    "url": ["案内用ホームページアドレス", "薬局のホームページアドレス"],
    "general_beds": ["一般病床"],
    "long_term_care_beds": ["療養病床"],
    "long_term_care_medical_insurance_beds": ["療養病床のうち医療保険適用"],
    "long_term_care_ltci_beds": ["療養病床のうち介護保険適用"],
    "psychiatric_beds": ["精神病床"],
    "tuberculosis_beds": ["結核病床"],
    "infectious_beds": ["感染症病床"],
    "total_beds": ["合計病床数"],
}


def latest_files(html: str) -> dict[str, str]:
    """ページのリンクから、最新の時点のファイル名 → URL を返す。"""
    links = re.findall(r'href="([^"]+/(\d{2}(?:-\d)?_[a-z_]+)_(\d{8})(?:\.csv)?\.zip)"', html)
    if not links:
        raise RuntimeError("医療情報ネット: オープンデータのリンクが見つからない")
    latest = max(day for _, _, day in links)
    files = {name: url for url, name, day in links if day == latest}
    missing = set(FACILITY_FILES + SPECIALITY_FILES) - set(files)
    if missing:
        raise RuntimeError(f"医療情報ネット {latest}: ファイルが無い: {sorted(missing)}")
    return {name: url if url.startswith("http") else BASE_URL + url for name, url in files.items()}


def _read_csv(url: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(io.BytesIO(fetch(url))) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError(f"{url}: CSV が 1 つではない: {names}")
        text = archive.read(names[0]).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _as_of(url: str) -> str:
    day = re.search(r"_(\d{8})(?:\.csv)?\.zip$", url).group(1)
    return f"{day[:4]}-{day[4:6]}-{day[6:]}"


def flatten_facilities(rows: list[dict[str, str]], as_of: str) -> list[dict]:
    if not rows:
        return []
    header = rows[0].keys()
    index = {}
    for column, candidates in FACILITY_COLUMNS.items():
        found = [c for c in candidates if c in header]
        if len(found) > 1:
            raise ValueError(f"列 {column} の候補が 2 つある: {found}")
        index[column] = found[0] if found else None
    for required in ("id", "name", "facility_type_code", "prefecture_code", "municipality_code", "address"):
        if index[required] is None:
            raise ValueError(f"必要な列 {required} が無い: {list(header)}")
    return [
        {"as_of": as_of} | {column: (row[source] or None) if source else None for column, source in index.items()}
        for row in rows
    ]


def flatten_specialities(rows: list[dict[str, str]], as_of: str) -> list[dict]:
    seen = set()
    records = []
    for row in rows:
        key = (row["ID"], row["診療科目コード"])
        if key in seen:
            continue
        seen.add(key)
        records.append(
            {
                "as_of": as_of,
                "id": row["ID"],
                "speciality_code": row["診療科目コード"],
                "speciality_name": row["診療科目名"],
            }
        )
    return records


def download_and_flatten(facility_path: Path, speciality_path: Path) -> tuple[int, int]:
    """最新の時点の施設票と診療科・診療時間票を取得し、2 本の NDJSON を書き出す。行数を返す。"""
    files = latest_files(fetch(PAGE_URL).decode("utf-8", errors="replace"))
    facilities = specialities = 0
    with replacing(facility_path) as facility_partial, replacing(speciality_path) as speciality_partial:
        with facility_partial.open("w", encoding="utf-8") as out:
            for name in FACILITY_FILES:
                url = files[name]
                for record in flatten_facilities(_read_csv(url), _as_of(url)):
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    facilities += 1
        with speciality_partial.open("w", encoding="utf-8") as out:
            for name in SPECIALITY_FILES:
                url = files[name]
                for record in flatten_specialities(_read_csv(url), _as_of(url)):
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    specialities += 1
        if facilities == 0 or specialities == 0:
            raise RuntimeError("医療情報ネット: 0 件")
    return facilities, specialities
