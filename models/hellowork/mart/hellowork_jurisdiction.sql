{# ハローワークの管轄区域。1 行 = 管轄一覧表の 1 行（1 つの公共職業安定所）。
   出張所・分室の管轄は本所の管轄の一部で、本所の行にも同じ区域が含まれる。 #}

{{ config(materialized='table', alias='jurisdiction') }}

select
    prefecture_code,
    prefecture_name,
    name,
    office_name,
    office_kind,
    jurisdiction,
    len(jurisdiction_items) as item_count,
    source_url
from {{ ref('raw_hellowork_jurisdiction') }}
order by prefecture_code, office_kind, office_name
