{# ハローワークの管轄区域を、管轄一覧表の読点で区切った項目ごとに 1 行にしたもの。
   「水戸市」「東海村」のように項目が市区町村・郡の名前だけなら name_only が true。
   「稲敷郡のうち阿見町」「青森市（黒石公共職業安定所の管轄区域を除く。）」「松前郡（松前町、福島町）」の
   ように絞り込みや内訳が付いていれば false。
   municipality_name は、name_only の項目と「Xのうち…」「X（…）」の形の項目の X。
   「長岡市のうち川口相川、川口荒谷」の「川口荒谷」のように町・字だけが続く項目は、字の名前が
   「児島柳田町」「伊沢市」のように市区町村と同じ語尾を持つことがあり判定できないので NULL にする。
   同じ理由で、「Xのうち」の項目より後ろにある name_only の項目は、市区町村ではなく X の中の町・字の
   ことがある（「倉敷市のうち児島稗田町、児島柳田町」の「児島柳田町」）。after_partial が true の行がそれで、
   市区町村の一覧と照合して確かめる。 #}

{{ config(materialized='table', alias='jurisdiction_area') }}

with items as (
    select
        prefecture_code,
        prefecture_name,
        office_name,
        office_kind,
        unnest(jurisdiction_items) as area_text,
        unnest(generate_series(1, len(jurisdiction_items))) as item_order
    from {{ ref('raw_hellowork_jurisdiction') }}
)

select
    prefecture_code,
    prefecture_name,
    office_name,
    office_kind,
    item_order,
    area_text,
    case when name_only or qualified then own_municipality end as municipality_name,
    name_only,
    coalesce(bool_or(contains(area_text, 'のうち')) over (
        partition by prefecture_code, office_name, office_kind order by item_order
        rows between unbounded preceding and 1 preceding
    ), false) as after_partial
from (
    select
        *,
        nullif(regexp_extract(area_text, '^(.+?(?:市|区|町|村|郡))(?:のうち|[（(《]|$)', 1), '') as own_municipality,
        regexp_full_match(area_text, '[^（()）《》]+?(市|区|町|村|郡)')
            and not contains(area_text, 'のうち') as name_only,
        regexp_matches(area_text, '^[^（()）《》]+?(市|区|町|村|郡)(のうち|[（(《])') as qualified
    from items
)
order by prefecture_code, office_kind, office_name, item_order
