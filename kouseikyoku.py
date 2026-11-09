"""地方厚生局「コード内容別医療機関一覧表」の取得・整形。

全国の保険医療機関・保険薬局の一覧で、8 つの地方厚生局（四国厚生支局を含む）が管内の分を
毎月上旬に公開している。どの局も同じ帳票（医療機関番号順、1 機関が数行にまたがる）を
Excel で出していて、置き場所（xlsx か zip か、ファイルの分け方）だけが局ごとに異なる。

帳票の列（0 始まり）:
  0 項番 / 1 医療機関番号・併設の番号 / 2 名称 / 3 所在地 / 4 電話番号・職員数 /
  5 開設者 / 6 管理者 / 7 指定年月日・登録理由・指定期間の始め / 8 病床数・診療科 /
  9 種別・状態（現存・休止）
1 機関の最初の行は 0 列に項番、1 列に医療機関番号（例 01,1248,9）を持つ。続く行が次の
機関の最初の行までの続きになる。

開設者と管理者は個人の氏名を含むので取り込まない。
医科併設・歯科併設の一覧は医科・歯科の一覧の一部なので読まない。
"""

import io
import json
import re
import zipfile
from datetime import date
from pathlib import Path

import openpyxl

from shared.fetch import fetch, replacing

BASE_URL = "https://kouseikyoku.mhlw.go.jp"

# 局 → (一覧のページ, 全体の一覧のファイルを選ぶ正規表現, ページの先頭から何件取るか)。
# ページには前月までの一覧や新規・廃止の一覧も並ぶので、局ごとにファイル名か並び順で選ぶ。
BUREAUS: dict[str, tuple[str, str, int | None]] = {
    "hokkaido": ("/hokkaido/gyomu/gyomu/hoken_kikan/code_ichiran.html", r"\.xlsx$", None),
    "tohoku": (
        "/tohoku/gyomu/gyomu/hoken_kikan/itiran.html",
        r"/shitei-touhoku-(ika|shika|yakkyoku)-r\d+\.xlsx$",
        None,
    ),
    "kantoshinetsu": ("/kantoshinetsu/chousa/shitei.html", r"/shitei_(ika|shika|yakkyoku)_r\d+\.zip$", None),
    "tokaihokuriku": ("/tokaihokuriku/newpage_00287.html", r"\.zip$", None),
    "kinki": ("/kinki/tyousa/shinkishitei.html", r"_kikanzentai_(ika|sika|yakkyoku)\.zip$", None),
    # 医科・歯科・薬局の全体の一覧が先頭の 3 件。後ろは月ごとの新規・廃止の一覧
    "chugokushikoku": ("/chugokushikoku/chousaka/iryoukikanshitei.html", r"\.zip$", 3),
    # 医科・歯科・薬局の全体の一覧が先頭の 3 件。後ろは施設基準の名簿など
    "shikoku": ("/shikoku/gyomu/gyomu/hoken_kikan/shitei/index.html", r"\.zip$", 3),
    # 最新月の 8 事務所分が先頭の 8 件。後ろは前月までの一覧
    "kyushu": ("/kyushu/gyomu/gyomu/hoken_kikan/index_00006.html", r"\.zip$", 8),
}

PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県",
    "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県",
    "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府",
    "兵庫県", "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県",
    "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県",
    "鹿児島県", "沖縄県",
]
_PREFECTURE_CODE = {name: f"{i + 1:02d}" for i, name in enumerate(PREFECTURES)}

# 点数表の番号。10 桁の医療機関コードは 都道府県 2 桁 + 点数表 1 桁 + 医療機関番号 7 桁
_TABLE_CODE = {"医科": "1", "歯科": "3", "薬局": "4"}

# 医療機関番号は 7 桁。区切りは局によって 01,1248,9 / 01-1248-9 / 01・1248・3 / 010,006.5 /
# 011 026.5 / 0112489 と異なる
_SEPARATED_DIGITS = r"\d[\d,\-・. ]*\d"
_CODE = re.compile(rf"^(?=(?:\D*\d){{7}}\D*$){_SEPARATED_DIGITS}$")
_ANNEX_CODE = re.compile(rf"^\(({_SEPARATED_DIGITS})\)$")
_HEADER = re.compile(r"(\d+)年\s*(\d+)月\s*(\d+)日現在\s+(\S+)\s+現存/休止")
_ERA = {"明": 1867, "大": 1911, "昭": 1925, "平": 1988, "令": 2018}
_DATE = re.compile(r"^(明|大|昭|平|令)\s*(元|\d+)\.\s*(\d+)\.\s*(\d+)$")
_STAFF = re.compile(r"^(常\s*勤|非常勤)\s*:\s*([\d,]+)$")
_STAFF_DETAIL = re.compile(r"^\((医|歯|薬)\s*([\d,]+)\)$")
# 病床は「一般 352」の 1 行か、「一般（感染）」と次の行の「4」の 2 行で書かれる。
# 数の付かない種類名だけの行もある
_BEDS = re.compile(r"^((?:一般|療養|精神|結核|感染|介護)(?:（[^）]+）)?)(?: (\d+))?$")


def _text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("　", " ")).strip()


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def parse_date(value: str) -> str | None:
    """和暦の「令5. 3. 1」を ISO 8601 にする。日付でなければ None。"""
    match = _DATE.match(value)
    if not match:
        return None
    era, year, month, day = match.groups()
    year = 1 if year == "元" else int(year)
    return date(_ERA[era] + year, int(month), int(day)).isoformat()


def _header(rows: list[list[str]]) -> tuple[str, str | None, str] | None:
    """帳票の見出しから（現在の日付, 都道府県名, 一覧の種類）を返す。見出しが無ければ None。"""
    as_of = kind = prefecture = None
    for values in rows[:12]:
        for cell in values:
            if match := _HEADER.search(cell):
                year, month, day, kind = match.groups()
                as_of = date(_ERA["令"] + int(year), int(month), int(day)).isoformat()
            if match := re.fullmatch(r"\[(\S+?[都道府県])\]", cell):
                prefecture = match.group(1)
    if as_of is None or kind is None:
        return None
    return as_of, prefecture, kind


def _record(lines: list[list[str]], prefecture_code: str, table: str, as_of: str) -> dict:
    first = lines[0]
    code7 = _digits(first[1])
    district, number, check = code7[:2], code7[2:6], code7[6]
    record = {
        "as_of": as_of,
        "medical_institution_code": prefecture_code + _TABLE_CODE[table] + code7,
        "prefecture_code": prefecture_code,
        "fee_schedule": table,
        "institution_number": f"{district}-{number}-{check}",
        "name": first[2],
        "address": first[3],
        "phone": first[4],
        "designated_on": parse_date(first[7]),
    }
    col7 = [v[7] for v in lines[1:] if v[7]]
    record["designation_reason"] = col7[0] if col7 and parse_date(col7[0]) is None else None
    record["designation_period_start"] = next((parse_date(v) for v in col7 if parse_date(v)), None)

    annex = [_digits(m.group(1)) for v in lines[1:] if (m := _ANNEX_CODE.match(v[1]))]
    annex = [a for a in annex if len(a) == 7]
    record["annex_institution_number"] = f"{annex[0][:2]}-{annex[0][2:6]}-{annex[0][6]}" if annex else None

    staff: dict[str, int] = {}
    current = None
    for v in lines[1:]:
        if match := _STAFF.match(v[4]):
            current = "full_time" if match.group(1).replace(" ", "") == "常勤" else "part_time"
        elif (match := _STAFF_DETAIL.match(v[4])) and current:
            role = {"医": "doctors", "歯": "dentists", "薬": "pharmacists"}[match.group(1)]
            staff[f"{current}_{role}"] = int(match.group(2).replace(",", ""))
        elif v[4]:
            raise ValueError(f"{record['medical_institution_code']}: 職員数の欄が想定外: {v[4]!r}")
    record.update(staff)

    departments: list[str] = []
    beds: list[list] = []
    for v in [first] + lines[1:]:
        if not v[8]:
            continue
        if match := _BEDS.match(v[8]):
            beds.append({"kind": match.group(1), "beds": int(match.group(2)) if match.group(2) else None})
        elif v[8].isdigit() and beds and beds[-1]["beds"] is None:
            beds[-1]["beds"] = int(v[8])
        else:
            departments.extend(re.split(r"[ 、]", v[8]))
    # 数の無い種類だけの行（帳票の余白に種類名だけが並ぶもの）は病床ではない
    record["beds"] = [b for b in beds if b["beds"] is not None]
    record["departments"] = departments

    # 9 列は 種別（病院・診療所・薬局、特定機能・地域支援・総合病院・療養病床）と、最後の行に状態
    # （現存・休止・辞退）。特定機能病院などは「特定機能」「病院」の順に並ぶ局と、「特定機能」
    # だけの局がある
    col9 = [v[9] for v in [first] + lines[1:] if v[9]]
    if len(col9) < 2:
        raise ValueError(f"{record['medical_institution_code']}: 種別と状態が無い: {col9}")
    record["categories"] = col9[:-1]
    record["status"] = col9[-1]
    return record


def parse_sheet(rows: list[list[str]], default_prefecture: str | None) -> list[dict]:
    """1 シートを読み、機関ごとの dict を返す。見出しの無いシート・併設の一覧は空を返す。"""
    records: list[dict] = []
    as_of = prefecture = table = None
    block: list[list[str]] = []

    def flush() -> None:
        if block:
            records.append(_record(block, _PREFECTURE_CODE[prefecture], table, as_of))
            block.clear()

    for i, values in enumerate(rows):
        # 帳票はページごとに見出しを繰り返す。都道府県が途中で変わる局もあるので毎回読む
        if any("コード内容別医療機関一覧表" in v for v in values):
            header = _header(rows[i : i + 12])
            if header:
                flush()
                as_of, prefecture, table = header
                prefecture = prefecture or default_prefecture
                if table not in _TABLE_CODE:
                    return []  # 医科併設・歯科併設
                if prefecture not in _PREFECTURE_CODE:
                    raise ValueError(f"都道府県が分からない: {values}")
            continue
        if as_of is None:
            continue
        if _CODE.match(values[1]) and values[0].isdigit():
            flush()
            block.append(values)
        elif block and any(values):
            block.append(values)
    flush()
    return records


def _sheets(content: bytes) -> list[list[list[str]]]:
    book = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    sheets = []
    for sheet in book.worksheets:
        rows = [[_text(c) for c in row] for row in sheet.iter_rows(values_only=True)]
        sheets.append([(r + [""] * 10)[:10] for r in rows])
    return sheets


def _workbooks(url: str) -> list[tuple[str, bytes]]:
    content = fetch(url)
    if not url.endswith(".zip"):
        return [(url, content)]
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        return [
            (f"{url}#{name}", archive.read(name))
            for name in archive.namelist()
            if name.lower().endswith(".xlsx")
        ]


def discover(bureau: str) -> list[str]:
    page, pattern, limit = BUREAUS[bureau]
    html = fetch(BASE_URL + page).decode("utf-8", errors="replace")
    links = re.findall(r'href="([^"]+\.(?:xlsx|zip))"', html)
    links = [link if link.startswith("http") else BASE_URL + link for link in links]
    links = [link for link in dict.fromkeys(links) if re.search(pattern, link)]
    links = links[:limit] if limit else links
    if not links:
        raise RuntimeError(f"{bureau}: 一覧のファイルが見つからない")
    return links


def _default_prefecture(bureau: str, name: str) -> str | None:
    """見出しに都道府県名が無い帳票の都道府県。北海道厚生局は管内が北海道だけ。"""
    if bureau == "hokkaido":
        return "北海道"
    return next((p for p in PREFECTURES if p.removesuffix("県").removesuffix("府").removesuffix("都") in name), None)


def download_and_flatten(path: Path) -> int:
    """全局の一覧を取得し、1 機関 1 行の NDJSON を書き出す。行数を返す。"""
    seen: dict[str, str] = {}
    rows = 0
    with replacing(path) as partial, partial.open("w", encoding="utf-8") as out:
        for bureau in BUREAUS:
            for url in discover(bureau):
                for name, content in _workbooks(url):
                    for sheet in _sheets(content):
                        for record in parse_sheet(sheet, _default_prefecture(bureau, name)):
                            code = record["medical_institution_code"]
                            if code in seen:
                                raise ValueError(f"{code} が 2 か所にある: {seen[code]} / {name}")
                            seen[code] = name
                            record["bureau"] = bureau
                            out.write(json.dumps(record, ensure_ascii=False) + "\n")
                            rows += 1
        prefectures = {code[:2] for code in seen}
        missing = sorted(set(_PREFECTURE_CODE.values()) - prefectures)
        if missing:
            raise RuntimeError(f"コード内容別医療機関一覧表: 都道府県 {missing} の行が無い")
    return rows
