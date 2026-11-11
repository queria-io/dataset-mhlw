"""公共職業安定所（ハローワーク）の所在地と管轄区域の取得・整形。

厚生労働省の「都道府県労働局（労働基準監督署、公共職業安定所）所在地一覧」から取る。
都道府県ごとに 2 ページあり、どちらも同じ作りの HTML（Shift_JIS。都道府県の一覧のページだけ UTF-8）:

- <都道府県>/            : 「公共職業安定所」の節（id="antei"）の表。列は 地方機関・郵便番号・所在地・電話。
                           地方機関の欄に名前と、労働局のサイトの案内図へのリンクがある
- <都道府県>/antei.html  : 管轄一覧表。列は 公共職業安定所・管轄区域

所在地の表には、管轄一覧表に無い施設（マザーズハローワーク、分室、相談窓口など）も並ぶ。
管轄一覧表は出張所の管轄を【】で囲んで書く（本所の管轄の一部を受け持つ）。

名前は 2 つのページで書き方が違う（笠間(出) / 笠間［出］、龍ケ崎 / 龍ヶ崎）ので、NFKC で畳み、
括弧の種類とヶ・ケをそろえてから突き合わせる。
"""

import html
import json
import re
import unicodedata
from pathlib import Path

from shared.fetch import fetch, replacing

INDEX_URL = "https://www.mhlw.go.jp/kouseiroudoushou/shozaiannai/roudoukyoku/"

PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県",
    "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県",
    "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府",
    "兵庫県", "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県",
    "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県",
    "鹿児島県", "沖縄県",
]  # fmt: skip

_PREF_LINK = re.compile(r'href="[^"]*/shozaiannai/roudoukyoku/([a-z]+)/"[^>]*>\s*(\d{2})\s')
_POSTAL = re.compile(r"(\d{3})\s*[-‐－ー−]\s*(\d{4})")
_PHONE = re.compile(r"(?:電話|TEL)?\s*([\d\-()（）]{10,}(?:～\d+)?)")
_FAX = re.compile(r"FAX\s*:?\s*([\d\-()（）]{10,})")
# 名前の後ろの種類の印。(出)=出張所、(分)=分室
_KIND = {"出": "branch", "分": "annex"}
_KIND_MARK = re.compile(r"[\(\[](出|分)[\)\]]")


def _decode(body: bytes) -> str:
    """一覧のページは UTF-8、都道府県のページは Shift_JIS。meta の charset で決める。"""
    sjis = re.search(rb"charset=[\"']?(shift_jis|sjis|x-sjis)", body[:2048], re.I)
    return body.decode("cp932" if sjis else "utf-8")


def _text(cell: str) -> str:
    cell = re.sub(r"<br\s*/?>", "\n", cell)
    cell = html.unescape(re.sub(r"<[^>]+>", "", cell))
    return "\n".join(re.sub(r"[ \t　]+", " ", line).strip() for line in cell.splitlines()).strip()


def _cells(table: str) -> list[list[str]]:
    return [re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S) for tr in re.findall(r"<tr.*?</tr>", table, re.S)]


def office_key(name: str) -> tuple[str, str]:
    """名前を (本体の名前, 種類) にする。2 つのページの名前はこの形で突き合わせる。

    「笠間(出)」「庄原〔出〕」「笠間［出］」は (笠間, branch)。「横浜（本庁舎）」「船橋 （第一庁舎）」
    「横手公共職業安定所 （マザーズコーナー横手）」のような庁舎や窓口の添え書きは落とす。
    """
    s = unicodedata.normalize("NFKC", name).replace("ヶ", "ケ")
    s = re.sub(r"[〔［【]", "[", re.sub(r"[〕］】]", "]", s))
    m = _KIND_MARK.search(s)
    kind = _KIND[m.group(1)] if m else "main"
    s = _KIND_MARK.sub("", s).replace("公共職業安定所", "").strip()
    s = re.split(r"\s", s, maxsplit=1)[0]
    base = re.sub(r"\(.*?\)", "", s).strip()
    return (base or s), kind


def prefectures(index: str) -> list[tuple[str, str]]:
    """一覧のページから (都道府県コード, ページの名前) を返す。"""
    found = sorted({(code, slug) for slug, code in _PREF_LINK.findall(index)})
    if [code for code, _ in found] != [f"{i:02d}" for i in range(1, 48)]:
        raise RuntimeError(f"所在地一覧: 47 都道府県のリンクがそろわない: {[c for c, _ in found]}")
    return found


def parse_offices(page: str) -> list[dict]:
    """都道府県のページの「公共職業安定所」の節を読む。"""
    start = page.find('id="antei"')
    if start < 0:
        raise RuntimeError("公共職業安定所の節が無い")
    section = page[start : page.find("<!-- /.section -->", start)]
    tables = re.findall(r"<table.*?</table>", section, re.S)
    if len(tables) != 1:
        raise RuntimeError(f"公共職業安定所の表が {len(tables)} 個ある")
    heads = [_text(h) for h in re.findall(r"<th[^>]*>(.*?)</th>", tables[0], re.S)]
    if heads[1:] != ["郵便番号", "所在地", "電話"]:
        raise RuntimeError(f"公共職業安定所の表の見出しが想定と違う: {heads}")
    offices = []
    for cells in _cells(tables[0]):
        if not cells:
            continue
        # 名前の欄の右に「案内図」のリンクがある。神奈川の港北は名前と郵便番号が 1 つの欄にある
        first = re.sub(r'<span class="fl-right">.*?</span>', "", cells[0], flags=re.S)
        links = re.findall(r'href="([^"]+)"', cells[0])
        lines = [line for line in _text(first).splitlines() if line and line != "案内図"]
        rest = [_text(c) for c in cells[1:]]
        if len(rest) == 2 and _POSTAL.search(rest[0]):
            # 東京の分庁舎は、電話の欄を本庁舎の行と結合している (rowspan)
            rest = [*rest, ""]
        elif len(rest) == 2:
            # 神奈川の港北は、名前と郵便番号が 1 つの欄にある
            rest = [next(line for line in lines if _POSTAL.search(line)), *rest]
            lines = [line for line in lines if not _POSTAL.search(line)]
        if len(rest) != 3:
            raise RuntimeError(f"公共職業安定所の行の欄の数が想定と違う: {lines} {rest}")
        name = re.sub(r"\s*案内図$", "", " ".join(lines)).strip()
        postal, address, phones = rest
        address = re.sub(r"^注\d+[)）]", "", address)
        m = _POSTAL.search(postal)
        if not name or not m:
            raise RuntimeError(f"公共職業安定所の行が読めない: {name!r} {postal!r}")
        fax = _FAX.search(phones)
        tel = _PHONE.search(_FAX.sub("", phones))
        offices.append(
            {
                "name": name,
                "postal_code": m.group(1) + m.group(2),
                "address": re.sub(r"\s+", " ", address).strip(),
                "phone": tel.group(1) if tel else None,
                "fax": fax.group(1) if fax else None,
                "phone_text": phones.replace("\n", " / ") or None,
                "guide_url": links[0] if links else None,
            }
        )
    return offices


def parse_jurisdictions(page: str) -> list[tuple[str, str]]:
    """管轄一覧表を (公共職業安定所の名前, 管轄区域) の並びにする。"""
    tables = re.findall(r"<table.*?</table>", page, re.S)
    if len(tables) != 1:
        raise RuntimeError(f"管轄一覧表が {len(tables)} 個ある")
    heads = [_text(h) for h in re.findall(r"<th[^>]*>(.*?)</th>", tables[0], re.S)]
    if heads != ["公共職業安定所", "管轄区域"]:
        raise RuntimeError(f"管轄一覧表の見出しが想定と違う: {heads}")
    rows = []
    for cells in _cells(tables[0]):
        if len(cells) != 2:
            continue
        name, area = (_text(c).replace("\n", "") for c in cells)
        rows.append((name, area))
    return rows


def split_area(area: str) -> list[str]:
    """管轄区域を、括弧の外の読点で区切った項目にする。出張所の【】は外す。"""
    s = area.strip()
    if s[:1] in "【［[" and s[-1:] in "】］]":
        s = s[1:-1]
    items, depth, buf = [], 0, ""
    for ch in s:
        if ch in "（(《":
            depth += 1
        elif ch in "）)》":
            depth -= 1
        if ch in "、，,､" and depth == 0:
            items.append(buf.strip())
            buf = ""
        else:
            buf += ch
    items.append(buf.strip())
    return [item for item in items if item]


def records(prefecture_code: str, offices: list[dict], jurisdictions: list[tuple[str, str]], source: str) -> tuple[list[dict], list[dict]]:
    """所在地の表を 1 施設 1 行に、管轄一覧表を 1 安定所 1 行にする。2 つは office_name と office_kind で結べる。"""
    prefecture = {"prefecture_code": prefecture_code, "prefecture_name": PREFECTURES[int(prefecture_code) - 1]}
    office_rows = [
        {**prefecture, **dict(zip(("office_name", "office_kind"), office_key(o["name"]))), **o, "source_url": source}
        for o in offices
    ]
    area_rows = [
        {
            **prefecture,
            "name": name,
            **dict(zip(("office_name", "office_kind"), office_key(name))),
            "jurisdiction": area,
            "jurisdiction_items": split_area(area),
            "source_url": f"{source}antei.html",
        }
        for name, area in jurisdictions
    ]
    return office_rows, area_rows


def download_and_flatten(office_path: Path, jurisdiction_path: Path) -> tuple[int, int]:
    """47 都道府県のページを取得し、所在地と管轄区域の NDJSON を書き出す。行数を返す。"""
    office_count = area_count = 0
    with replacing(office_path) as p1, replacing(jurisdiction_path) as p2:
        with p1.open("w", encoding="utf-8") as out1, p2.open("w", encoding="utf-8") as out2:
            for code, slug in prefectures(_decode(fetch(INDEX_URL))):
                url = f"{INDEX_URL}{slug}/"
                offices = parse_offices(_decode(fetch(url)))
                jurisdictions = parse_jurisdictions(_decode(fetch(f"{url}antei.html")))
                if not offices or not jurisdictions:
                    raise RuntimeError(f"{slug}: 所在地 {len(offices)} 件、管轄 {len(jurisdictions)} 件")
                office_rows, area_rows = records(code, offices, jurisdictions, url)
                for row in office_rows:
                    out1.write(json.dumps(row, ensure_ascii=False) + "\n")
                for row in area_rows:
                    out2.write(json.dumps(row, ensure_ascii=False) + "\n")
                office_count += len(office_rows)
                area_count += len(area_rows)
    return office_count, area_count
