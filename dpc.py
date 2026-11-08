"""DPC 導入の影響評価に係る調査「退院患者調査」の取得・整形。

中医協 DPC 評価分科会が年度ごとに公表する「退院患者調査」の結果報告から、次の 2 表を取得する。

- 施設概要表: 調査に参加した病院ごとの所在市町村・病床数・入院基本料など
- 参考資料（２）MDC 別医療機関別件数: 病院 × MDC（主要診断群 18 区分）× 手術の有無 の退院患者数

どちらも 1 年度 1 ファイルで、平成 28 年度から同じ表の構成で公表されている。
施設概要表は 1 行目が見出しで、平成 28 年度だけ「都道府県」の列が無い。列は見出しの名前で
対応づける。MDC 別件数は「件数」シートの 2 行目が見出し、4 行目からが本体で、
1 つの病院が手術「無し」「有り」の 2 行を持つ（2 行目の告示番号・施設名は空欄）。
症例数が 10 未満の欄と 0 件の欄は「-」で公表されていないので、その欄は書き出さない。
"""

import io
import json
import re
from pathlib import Path

import openpyxl
import xlrd

from shared.fetch import fetch, replacing

BASE_URL = "https://www.mhlw.go.jp"

# 年度 → (施設概要表, MDC 別医療機関別件数)。
# 出典ページ: 平成 28〜令和 3 年度 /stf/shingi2/0000196043*.html、
# 令和 4 年度 /stf/shingi2/newpage_39119.html、令和 5 年度 /stf/shingi2/newpage_00137.html
FILES = {
    2016: (
        "/file/05-Shingikai-12404000-Hokenkyoku-Iryouka/0000196159.xls",
        "/file/05-Shingikai-12404000-Hokenkyoku-Iryouka/0000196179.xls",
    ),
    2017: ("/content/12404000/001531342.xls", "/content/12404000/001531398.xls"),
    2018: ("/content/12404000/001351720.xlsx", "/content/12404000/001351777.xlsx"),
    2019: ("/content/12404000/001350398.xlsx", "/content/12404000/001350436.xlsx"),
    2020: ("/content/12404000/001348984.xlsx", "/content/12404000/001349010.xlsx"),
    2021: ("/content/12404000/001348829.xlsx", "/content/12404000/001348857.xlsx"),
    2022: ("/content/12404000/001234038.xlsx", "/content/12404000/001234081.xlsx"),
    2023: ("/content/12404000/001468611.xlsx", "/content/12404000/001468867.xlsx"),
}

# 施設概要表の見出し（改行と注記「※n」を除いたもの）の先頭 → 出力の列名。
# 見出しの細部は年度で揺れる（「回復期リハビリテーション病棟入院料等病床数」など）ため前方一致で引く。
_HOSPITAL_COLUMNS = [
    ("告示番号", "notification_number"),
    ("通番", "serial_number"),
    ("市町村番号", "city_code"),
    ("施設名", "hospital_name"),
    ("病院類型", "hospital_category"),
    ("DPC算定病床数", "dpc_beds"),
    ("DPC算定病床の入院基本料", "dpc_basic_fee"),
    ("DPC算定病床割合", "dpc_bed_ratio"),
    ("回復期リハビリテーション病棟", "rehabilitation_beds"),
    ("地域包括ケア病棟", "community_care_beds"),
    ("精神病床数", "psychiatric_beds"),
    ("療養病床数", "long_term_care_beds"),
    ("結核病床数", "tuberculosis_beds"),
    ("病床総数", "total_beds"),
]
_MONTHS_HEADER = re.compile(r"年度提出月数$")

_MDC_HEADER = ["告示番号", "通番", "施設名", "手術"] + [f"{i:02d}" for i in range(1, 19)]
_MDC_HEADER_ROW = 1
_MDC_DATA_START_ROW = 3
_SUPPRESSED = "-"


def _read_rows(content: bytes, path: str) -> list[list]:
    """先頭シートの全行を返す。.xls は xlrd、.xlsx は openpyxl で読む。"""
    if path.endswith(".xls"):
        sheet = xlrd.open_workbook(file_contents=content).sheet_by_index(0)
        return [sheet.row_values(r) for r in range(sheet.nrows)]
    book = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    return [list(row) for row in book.worksheets[0].iter_rows(values_only=True)]


def _text(value: object) -> str:
    """セルを文字列へ。xlrd が数値を float で返すので、整数の値は小数点を付けない。"""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _normalize_header(value: object) -> str:
    return re.sub(r"※\d*|\s", "", _text(value))


def _is_hospital_code(value: object) -> bool:
    return re.fullmatch(r"\d{5}", _text(value)) is not None


def _hospital_column_index(header: list) -> dict[str, int]:
    names = [_normalize_header(h) for h in header]
    index: dict[str, int] = {}
    for prefix, column in _HOSPITAL_COLUMNS:
        matches = [i for i, name in enumerate(names) if name.startswith(prefix)]
        if len(matches) != 1:
            raise ValueError(f"施設概要表: 見出し「{prefix}」が {len(matches)} 列ある: {names}")
        index[column] = matches[0]
    months = [i for i, name in enumerate(names) if _MONTHS_HEADER.search(name)]
    if len(months) != 1:
        raise ValueError(f"施設概要表: 提出月数の列が見つからない: {names}")
    index["months_submitted"] = months[0]
    return index


def flatten_hospitals(rows: list[list], fiscal_year: int) -> list[dict]:
    index = _hospital_column_index(rows[0])
    records = []
    for values in rows[1:]:
        # 表の下には注記の行が続く。告示番号が 5 桁の数字の行だけが病院。
        if not _is_hospital_code(values[index["notification_number"]]):
            continue
        record = {"fiscal_year": fiscal_year}
        record.update({column: _text(values[i]) for column, i in index.items()})
        records.append(record)
    return records


def flatten_mdc(rows: list[list], fiscal_year: int) -> list[dict]:
    header = [_text(v) for v in rows[_MDC_HEADER_ROW][: len(_MDC_HEADER)]]
    if header != _MDC_HEADER:
        raise ValueError(f"MDC 別件数 {fiscal_year}: 見出しが想定と異なる: {header}")
    records = []
    notification = serial = None
    for values in rows[_MDC_DATA_START_ROW:]:
        if _is_hospital_code(values[0]):
            notification, serial = _text(values[0]), _text(values[1])
        surgery = _text(values[3])
        if surgery not in ("有り", "無し") or notification is None:
            raise ValueError(f"MDC 別件数 {fiscal_year}: 想定外の行: {values[:5]}")
        for offset, mdc in enumerate(_MDC_HEADER[4:]):
            patients = _text(values[4 + offset])
            if patients in (_SUPPRESSED, ""):
                continue
            records.append(
                {
                    "fiscal_year": fiscal_year,
                    "notification_number": notification,
                    "serial_number": serial,
                    "mdc": mdc,
                    "surgery": surgery,
                    "patients": patients,
                }
            )
    return records


def download_and_flatten(hospital_path: Path, mdc_path: Path) -> tuple[int, int]:
    """全年度の施設概要表と MDC 別件数を取得し、2 本の NDJSON を書き出す。行数を返す。"""
    hospital_rows = mdc_rows = 0
    with replacing(hospital_path) as hospital_partial, replacing(mdc_path) as mdc_partial:
        with hospital_partial.open("w", encoding="utf-8") as hospital_out, mdc_partial.open(
            "w", encoding="utf-8"
        ) as mdc_out:
            for fiscal_year, (hospital_file, mdc_file) in FILES.items():
                hospitals = flatten_hospitals(
                    _read_rows(fetch(BASE_URL + hospital_file), hospital_file), fiscal_year
                )
                mdc = flatten_mdc(_read_rows(fetch(BASE_URL + mdc_file), mdc_file), fiscal_year)
                codes = {(h["notification_number"], h["serial_number"]) for h in hospitals}
                unmatched = {(m["notification_number"], m["serial_number"]) for m in mdc} - codes
                if unmatched:
                    raise ValueError(f"{fiscal_year}: 施設概要表に無い病院が MDC 別件数にある: {sorted(unmatched)[:5]}")
                for record in hospitals:
                    hospital_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                for record in mdc:
                    mdc_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                hospital_rows += len(hospitals)
                mdc_rows += len(mdc)
        if hospital_rows == 0 or mdc_rows == 0:
            raise RuntimeError("DPC 退院患者調査: 0 件")
    return hospital_rows, mdc_rows
