"""介護サービス情報公表システム オープンデータの取得・整形。

介護サービス情報公表システムは、全国の介護サービス事業所をサービス種類別に
CSV で公開している（1 サービス種類 = 1 全国 CSV）。各 CSV は UTF-8 BOM 付き・
同一の 24 列スキーマ。本モジュールは全サービス種類の CSV を取得し、列を英語名へ
そろえて 1 本の NDJSON に統合する。型変換・座標クレンジングは dbt（stg / mart）で行う。
"""

import csv
import json
import urllib.request
from pathlib import Path

BASE_URL = "https://www.mhlw.go.jp/content/12300000/jigyosho_{code}.csv"

# サービス種類コード。介護サービス情報公表システム オープンデータ一覧に対応する
# 全 35 種類。各コードの全国 CSV を縦結合する（サービス種類は各行の service_type 列に入る）。
SERVICE_CODES = [
    "110", "120", "130", "140", "150", "155", "160", "170",
    "210", "220", "230",
    "320", "331", "332", "334", "335", "336", "337",
    "361", "362", "364",
    "410", "430",
    "510", "520", "530", "540", "550", "551",
    "710", "720", "730", "760", "770", "780",
]

# 元 CSV 24 列の並びに対応する出力キー。None の列は捨てる
# （col1 "No" は事業所番号と全行一致のため除外）。
FIELDS: list[str | None] = [
    "local_gov_code",        # 都道府県コード又は市町村コード（全国地方公共団体コード 6 桁）
    None,                    # No（事業所番号と重複）
    "prefecture",            # 都道府県名
    "city",                  # 市区町村名
    "name",                  # 事業所名
    "name_kana",             # 事業所名カナ
    "service_type",          # サービスの種類
    "address",               # 住所
    "address_note",          # 方書（ビル名等）
    "latitude",              # 緯度
    "longitude",             # 経度
    "phone",                 # 電話番号
    "fax",                   # FAX 番号
    "corporate_number",      # 法人番号
    "corporate_name",        # 法人の名称
    "establishment_number",  # 事業所番号
    "available_days",        # 利用可能曜日
    "available_days_note",   # 利用可能曜日特記事項
    "capacity",              # 定員
    "url",                   # URL
    "shared_with_disability",             # 高齢者と障害者が同時一体的に利用できるサービス
    "meets_ltci_standard",                # 介護保険の通常の指定基準を満たしている
    "meets_disability_welfare_standard",  # 障害福祉の通常の指定基準を満たしている
    "note",                  # 備考
]

_KEYS = [f for f in FIELDS if f is not None]


def _fetch_rows(code: str) -> list[list[str]]:
    """1 サービス種類の全国 CSV を取得し、ヘッダを除くデータ行を返す。"""
    with urllib.request.urlopen(BASE_URL.format(code=code)) as resp:
        text = resp.read().decode("utf-8-sig")
    reader = csv.reader(text.splitlines())
    rows = list(reader)
    return rows[1:]  # ヘッダ行を除く


def _to_record(row: list[str]) -> dict[str, str | None]:
    """24 列の 1 行を英語キーのレコードへ変換する。空文字は None にする。"""
    padded = row + [""] * (len(FIELDS) - len(row))
    record: dict[str, str | None] = {}
    for value, key in zip(padded, FIELDS):
        if key is None:
            continue
        value = value.strip()
        record[key] = value or None
    return record


def download_and_flatten(ndjson_path: Path) -> int:
    """全サービス種類の CSV を取得し、統合 NDJSON を書き出す。行数を返す。"""
    rows = 0
    with ndjson_path.open("w", encoding="utf-8") as out:
        for code in SERVICE_CODES:
            for row in _fetch_rows(code):
                if not any(row):
                    continue
                record = _to_record(row)
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                rows += 1
    return rows
