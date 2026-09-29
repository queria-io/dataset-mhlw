"""地域における自殺の基礎資料（市区町村別・年計）の取得・整形。

厚生労働省自殺対策推進室が警察庁の自殺統計を再集計した「地域における自殺の基礎資料」の
確定値のうち、年計の「自殺日集計」ZIP を取得し、市区町村別の 2 表を縦持ち（long 形式）の
NDJSON に統合する。

- A7 表: 市区町村 × 自殺日 × 住居地（自殺者の住居があった市区町村で集計）
- A8 表: 市区町村 × 自殺日 × 発見地（自殺死体が発見された市区町村で集計）

各表は 総数・男・女 の 3 シートで、行が市区町村、列が属性（年齢階級・同居人の有無・職業・
場所・手段・時間帯・曜日・原因動機・自殺未遂歴）ごとの自殺者数になっている。
本モジュールは 1 行 = 1 セルの long 形式に展開する。

取り込むのは令和 4 年（2022 年）以降。令和 4 年 1 月分から自殺統計原票の見直しで
職業・原因動機の区分が変わり、それ以前の年とは列が対応しない。
"""

import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

import xlrd

# 年 → 年計「自殺日集計」ZIP。令和 4 年だけは「確定値その１」に A 表（自殺日集計）が入る。
# 出典ページ: https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000140901.html
ANNUAL_ZIP_URLS = {
    2022: "https://www.mhlw.go.jp/content/R4KAKUTEI-CHIIKI01.zip",
    2023: "https://www.mhlw.go.jp/content/12200000/001236396.zip",
    2024: "https://www.mhlw.go.jp/content/001464821.zip",
    2025: "https://www.mhlw.go.jp/content/001680831.zip",
}

_TABLES = {"A7": "住居地", "A8": "発見地"}
_SHEET_SEX = {0: "総数", 1: "男", 2: "女"}

_HEADER_GROUP_ROW = 4
_HEADER_ROW = 7
_DATA_START_ROW = 8
_NCOLS = 74

# 列位置（0 始まり）→ (属性区分, 区分, 親区分)。親区分は内数の上位区分で、
# 同じ属性区分の中で親区分が NULL の区分だけを足すと総数になる（原因・動機を除く）。
# 見出しの表記は年で揺れる（令和 4 年「飛降り」→ 令和 5 年以降「飛び降り」など）ため、
# 区分名は固定で持ち、列位置は属性区分の見出し行で検証する。
_COLUMNS: dict[int, tuple[str, str, str | None]] = {4: ("総数", "総数", None)}


def _add(group: str, start: int, categories: list[str | tuple[str, str]]) -> None:
    for offset, cat in enumerate(categories):
        name, parent = (cat, None) if isinstance(cat, str) else cat
        _COLUMNS[start + offset] = (group, name, parent)


_add("年齢階級", 7, ["20歳未満", "20-29歳", "30-39歳", "40-49歳", "50-59歳", "60-69歳", "70-79歳", "80歳以上", "不詳"])
_add("同居人の有無", 16, ["あり", "なし", "不詳"])
_add(
    "職業",
    19,
    [
        "有職",
        "無職",
        ("学生・生徒等", "無職"),
        ("無職者", "無職"),
        ("主婦・主夫", "無職者"),
        ("失業者", "無職者"),
        ("年金・雇用保険等生活者", "無職者"),
        ("その他の無職者", "無職者"),
        "不詳",
    ],
)
_add("場所", 28, ["自宅等", "高層ビル", "乗物", "海（湖）・河川等", "山", "その他", "不詳"])
_add("手段", 35, ["首つり", "服毒", "練炭等", "飛び降り", "飛び込み", "その他", "不詳"])
_add(
    "時間帯",
    42,
    ["0-2時", "2-4時", "4-6時", "6-8時", "8-10時", "10-12時", "12-14時", "14-16時", "16-18時", "18-20時", "20-22時", "22-24時", "不詳"],
)
_add("曜日", 55, ["日曜", "月曜", "火曜", "水曜", "木曜", "金曜", "土曜", "不詳"])
_add("原因・動機", 63, ["家庭問題", "健康問題", "経済・生活問題", "勤務問題", "交際問題", "学校問題", "その他", "不詳"])
_add("自殺未遂歴", 71, ["あり", "なし", "不詳"])

# 属性区分の見出し行（行 5）に現れる見出しと列位置。レイアウトが変わったら止める。
_EXPECTED_GROUP_HEADERS = {
    7: "年齢階級",
    16: "同居人の有無",
    19: "職業",
    28: "場所別",
    35: "手段別",
    42: "自殺の時間帯別",
    55: "自殺の曜日別",
    63: "原因・動機別",
    71: "自殺未遂歴の有無",
}

_UNKNOWN_CODE = 999999


def _check_layout(sheet: xlrd.sheet.Sheet, label: str) -> None:
    if sheet.ncols != _NCOLS:
        raise ValueError(f"{label}: 列数が {sheet.ncols}（想定 {_NCOLS}）")
    groups = {c: str(v).strip() for c, v in enumerate(sheet.row_values(_HEADER_GROUP_ROW)) if str(v).strip()}
    if groups != _EXPECTED_GROUP_HEADERS:
        raise ValueError(f"{label}: 属性区分の見出しが想定と異なる: {groups}")
    if str(sheet.cell_value(_HEADER_ROW, 4)).strip() != "自殺者数":
        raise ValueError(f"{label}: 自殺者数の列が見つからない")


def _to_count(value: object) -> int | None:
    """セルを人数へ。秘匿（空白）は NULL。"""
    if isinstance(value, float):
        return int(value)
    return None


def _area_level(code: int, name: str, ward: str, totals: set[int]) -> str:
    """行の種別。市区町村コードだけでは区別できない行があるため、名称と併せて決める。

    - 市区町村: 通常の市町村と、政令指定都市・東京都特別区の「（計）」行
    - 区: 政令指定都市の区と東京都の特別区（上の「（計）」の内数）
    - 区不詳: 政令指定都市内で区が分からないもの。「（計）」と同じ市コードで、名称に「（計）」が付かない
    - 市区町村不詳: 都道府県は分かるが市区町村が分からないもの（元データのコード XX9999）
    - 都道府県不詳: 都道府県も分からないもの（元データのコード 999999）
    """
    if code == _UNKNOWN_CODE:
        return "都道府県不詳"
    if code % 10000 == 9999:
        return "市区町村不詳"
    if ward:
        return "区"
    if code in totals and not name.endswith("（計）"):
        return "区不詳"
    return "市区町村"


def _flatten_sheet(sheet: xlrd.sheet.Sheet, year: int, basis: str, sex: str) -> list[dict]:
    rows = [sheet.row_values(r) for r in range(_DATA_START_ROW, sheet.nrows)]
    rows = [v for v in rows if isinstance(v[1], float)]
    totals = {int(v[1]) for v in rows if str(v[2]).strip().endswith("（計）")}

    records: list[dict] = []
    for values in rows:
        code = int(values[1])
        ward = str(values[3]).strip()
        name = str(values[2]).strip()
        level = _area_level(code, name, ward, totals)
        municipality = ward or re.sub(r"\s*（計）$", "", name)
        if level == "区不詳":
            municipality += "（区不詳）"
        records.extend(
            {
                "year": year,
                "location_basis": basis,
                "prefecture_code": None if level == "都道府県不詳" else f"{code:06d}"[:2],
                "local_gov_code": f"{code:06d}" if level in ("市区町村", "区") else None,
                "municipality": municipality,
                "area_level": level,
                "sex": sex,
                "attribute": group,
                "category": category,
                "parent_category": parent,
                "count": _to_count(values[col]),
            }
            for col, (group, category, parent) in _COLUMNS.items()
        )
    return records


def flatten_zip(zip_bytes: bytes, year: int, out) -> int:
    """年計 ZIP の A7・A8 表を long 形式で書き出す。行数を返す。"""
    rows = 0
    found = set()
    with zipfile.ZipFile(io.BytesIO(zip_bytes), metadata_encoding="cp932") as zf:
        for name in sorted(zf.namelist()):
            m = re.search(r"_(A[78])表", name)
            if not m:
                continue
            table = m.group(1)
            found.add(table)
            book = xlrd.open_workbook(file_contents=zf.read(name))
            for index, sex in _SHEET_SEX.items():
                sheet = book.sheet_by_index(index)
                _check_layout(sheet, f"{year} {table} {sex}")
                for record in _flatten_sheet(sheet, year, _TABLES[table], sex):
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    rows += 1
    if found != set(_TABLES):
        raise ValueError(f"{year}: A7・A8 表が揃っていない: {sorted(found)}")
    return rows


def download_and_flatten(ndjson_path: Path) -> int:
    """全年の年計 ZIP を取得し、統合 NDJSON を書き出す。行数を返す。"""
    rows = 0
    with ndjson_path.open("w", encoding="utf-8") as out:
        for year, url in ANNUAL_ZIP_URLS.items():
            with urllib.request.urlopen(url) as resp:
                rows += flatten_zip(resp.read(), year, out)
    return rows
