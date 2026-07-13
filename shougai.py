"""障害福祉サービス等情報公表システム オープンデータの取得・整形。

障害福祉サービス等情報公表システム（WAM NET 配信）は、全国の障害福祉サービス等
事業所をサービス種類別に CSV で公開している（1 サービス種類 = 1 全国 CSV を ZIP 化）。
各 CSV は UTF-8 BOM 付き・同一の 29 列スキーマ。本モジュールは公開ページから最新の
提供時点（YYYYMM）を特定し、全サービス種類の ZIP を取得して CSV を取り出し、列を
英語名へそろえて 1 本の NDJSON に統合する。型変換・座標クレンジングは dbt（stg / mart）
で行う。
"""

import csv
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

INDEX_URL = "https://www.wam.go.jp/content/wamnet/pcpub/top/sfkopendata/"
ZIP_URL = (
    "https://www.wam.go.jp/content/files/pcpub/top/sfkopendata/"
    "{period}/sfkopendata_{period}_{code}.zip"
)

# 障害福祉サービス等のサービス種類コード。公開ページに掲載される全種類。
# 各コードの全国 ZIP を縦結合する（サービス種類は各行の service_type 列に入る）。
SERVICE_CODES = [
    "11", "12", "13", "14", "15",  # 訪問系
    "21", "22", "24",              # 日中活動系
    "32", "33", "34",              # 施設系・居住系
    "41", "42", "45", "46",        # 訓練系・就労系
    "52", "53", "54",              # 相談支援
    "60", "61", "62",              # 就労移行・自立生活・就労定着
    "63", "64", "65", "66", "67", "68", "69", "70",  # 障害児支援
]

# 提供時点フォルダ（YYYYMM）を特定できなかった場合のフォールバック。
FALLBACK_PERIOD = "202603"

# 元 CSV 29 列の並びに対応する出力キー。
FIELDS = [
    "local_gov_code",            # 都道府県コード又は市区町村コード（5 桁）
    "system_no",                 # NO（システム内の固有の番号・連番）
    "designating_authority",     # 指定機関名
    "corporate_name",            # 法人の名称
    "corporate_name_kana",       # 法人の名称_かな
    "corporate_number",          # 法人番号
    "corporate_address_city",    # 法人住所（市区町村）
    "corporate_address_detail",  # 法人住所（番地以降）
    "corporate_phone",           # 法人電話番号
    "corporate_fax",             # 法人FAX番号
    "corporate_url",             # 法人URL
    "service_type",              # サービス種別
    "name",                      # 事業所の名称
    "name_kana",                 # 事業所の名称_かな
    "establishment_number",      # 事業所番号
    "address_city",              # 事業所住所（市区町村）
    "address_detail",            # 事業所住所（番地以降）
    "phone",                     # 事業所電話番号
    "fax",                       # 事業所FAX番号
    "url",                       # 事業所URL
    "latitude",                  # 事業所緯度
    "longitude",                 # 事業所経度
    "hours_weekday",             # 利用可能な時間帯（平日）
    "hours_saturday",            # 利用可能な時間帯（土曜）
    "hours_sunday",              # 利用可能な時間帯（日曜）
    "hours_holiday",             # 利用可能な時間帯（祝日）
    "closed_days",               # 定休日
    "available_days_note",       # 利用可能曜日特記事項（留意事項）
    "capacity",                  # 定員
]


def _latest_period() -> str:
    """公開ページから最新の提供時点フォルダ（YYYYMM）を返す。
    取得・解析に失敗した場合は FALLBACK_PERIOD を返す。"""
    try:
        with urllib.request.urlopen(INDEX_URL) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return FALLBACK_PERIOD
    periods = re.findall(r"sfkopendata/(\d{6})/sfkopendata_", html)
    return max(periods) if periods else FALLBACK_PERIOD


def _fetch_rows(period: str, code: str) -> list[list[str]]:
    """1 サービス種類の ZIP を取得し、CSV のヘッダを除くデータ行を返す。
    未提供のサービス種類（HTTP エラー）は空リストを返す。"""
    url = ZIP_URL.format(period=period, code=code)
    try:
        with urllib.request.urlopen(url) as resp:
            blob = resp.read()
    except urllib.error.HTTPError:
        return []
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        name = zf.namelist()[0]
        text = zf.read(name).decode("utf-8-sig")
    rows = list(csv.reader(text.splitlines()))
    return rows[1:]  # ヘッダ行を除く


def _to_record(row: list[str]) -> dict[str, str | None]:
    """29 列の 1 行を英語キーのレコードへ変換する。空文字は None にする。"""
    padded = row + [""] * (len(FIELDS) - len(row))
    record: dict[str, str | None] = {}
    for value, key in zip(padded, FIELDS):
        value = value.strip()
        record[key] = value or None
    return record


def download_and_flatten(ndjson_path: Path) -> int:
    """全サービス種類の CSV を取得し、統合 NDJSON を書き出す。行数を返す。"""
    period = _latest_period()
    rows = 0
    with ndjson_path.open("w", encoding="utf-8") as out:
        for code in SERVICE_CODES:
            for row in _fetch_rows(period, code):
                if not any(row):
                    continue
                record = _to_record(row)
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                rows += 1
    return rows
