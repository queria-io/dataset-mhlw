"""女性の活躍推進企業データベース オープンデータの取得・整形。

女性の活躍推進企業データベース（女性活躍推進法・次世代育成支援対策推進法に基づく
情報公表制度）は、企業が公表する女性活躍・両立支援の指標を全企業まとめた「全体版」
CSV を ZIP で公開している。各行が 1 企業で、236 列に多数の指標が横持ちで並ぶ。
本モジュールは全体版 ZIP を取得して CSV を取り出し、企業属性と主要指標に絞って
英語名へそろえた 1 本の NDJSON に整形する。型変換は dbt（stg / mart）で行う。

配信元は素の User-Agent を持たないリクエストを 403 で弾くため、ブラウザ相当の
User-Agent を付けて取得する。
"""

import csv
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

# 全体版（全企業・全指標）の CSV(ZIP) ダウンロード URL。w=99 が全体版。
ZIP_URL = "https://positive-ryouritsu.mhlw.go.jp/positivedb/opendata/download_b.html?w=99"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# CSV の列インデックス → 出力キー。企業属性と主要指標（企業単位で単一値のもの）に絞る。
# 雇用管理区分ごとに分割される指標のうち、育児休業取得率のみ先頭区分（区分１）を代表値として採る。
# csv の巨大な横持ち（236 列）は主要指標に限定し、詳細は将来拡張に回す。
COLUMNS: dict[int, str] = {
    0: "company_name",                  # 企業名
    1: "corporate_number",             # 法人番号（13 桁）
    3: "industry",                     # 業種
    4: "industry_detail",              # 業種(詳細分類)
    5: "prefecture",                   # 都道府県
    6: "company_size",                 # 企業規模
    8: "market_segment",               # 市場区分
    9: "securities_code",              # 証券コード
    11: "kurumin",                     # 企業認定等-くるみん認定
    18: "eruboshi_stage",              # 企業認定等-えるぼし、または、えるぼしプラス認定
    111: "childcare_leave_category",   # 5.男女別の育児休業取得率-雇用管理区分１
    112: "childcare_leave_male_pct",   # 5.男女別の育児休業取得率-男性(%)（区分１）
    113: "childcare_leave_female_pct",  # 5.男女別の育児休業取得率-女性(%)（区分１）
    128: "avg_monthly_overtime_hours",  # 6.一月当たりの労働者の平均残業時間-平均残業時間(時間)
    142: "paid_leave_rate_pct",        # 8.(1)年次有給休暇の取得率-対象労働者(%)
    155: "women_in_kakaricho_pct",     # 9.係長級にある者に占める女性労働者の割合-割合(%)
    159: "women_in_management_pct",    # 10.管理職に占める女性労働者の割合-割合(%)
    163: "women_on_board_pct",         # 11.役員に占める女性の割合-割合(%)
    205: "gender_wage_gap_all_pct",    # 14.男女の賃金の差異1-全労働者(%)
    206: "gender_wage_gap_regular_pct",     # 14.男女の賃金の差異2-うち正規雇用労働者(%)
    207: "gender_wage_gap_nonregular_pct",  # 14.男女の賃金の差異3-うち非正規雇用労働者(%)
    219: "wage_gap_period",            # 14.対象期間
    235: "last_updated",               # データの最終更新日
}


def _fetch_csv_text() -> str:
    """全体版 ZIP を取得し、同梱 CSV の本文（UTF-8 BOM 付き）を返す。"""
    req = urllib.request.Request(ZIP_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as resp:
        blob = resp.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        name = zf.namelist()[0]
        return zf.read(name).decode("utf-8-sig")


def _to_record(row: list[str]) -> dict[str, str | None]:
    """1 企業の行を、選択した列だけの英語キーのレコードへ変換する。空文字は None にする。"""
    record: dict[str, str | None] = {}
    for idx, key in COLUMNS.items():
        value = row[idx].strip() if idx < len(row) else ""
        record[key] = value or None
    return record


def download_and_flatten(ndjson_path: Path) -> int:
    """全体版 CSV を取得し、主要列に絞った NDJSON を書き出す。行数を返す。"""
    text = _fetch_csv_text()
    # 自由記述欄などにフィールド内改行を含むため、行分割せず csv パーサに
    # ストリームを渡してクオート内改行を正しく扱う。
    csv.field_size_limit(sys.maxsize)
    reader = csv.reader(io.StringIO(text))
    next(reader)  # ヘッダ行を除く
    rows = 0
    with ndjson_path.open("w", encoding="utf-8") as out:
        for row in reader:
            if not any(cell.strip() for cell in row):
                continue
            out.write(json.dumps(_to_record(row), ensure_ascii=False) + "\n")
            rows += 1
    return rows
