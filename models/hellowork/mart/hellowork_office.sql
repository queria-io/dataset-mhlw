{# ハローワークの施設。1 行 = 所在地一覧の 1 行。
   本所・出張所・分室のほか、庁舎（本庁舎・分庁舎）やハローワークプラザ・マザーズハローワークなども 1 行ずつ持つ。
   管轄一覧表に同じ office_name と office_kind の行があれば has_jurisdiction が true。 #}

{{ config(materialized='table', alias='office') }}

with jurisdiction as (
    select distinct prefecture_code, office_name, office_kind
    from {{ ref('raw_hellowork_jurisdiction') }}
)

select
    o.prefecture_code,
    o.prefecture_name,
    o.name,
    o.office_name,
    o.office_kind,
    j.office_name is not null as has_jurisdiction,
    o.postal_code,
    o.address,
    case
        when starts_with(o.address, o.prefecture_name) then o.address
        else o.prefecture_name || o.address
    end as full_address,
    o.phone,
    o.fax,
    o.phone_text,
    o.guide_url,
    o.source_url
from {{ ref('raw_hellowork_office') }} o
left join jurisdiction j using (prefecture_code, office_name, office_kind)
order by o.prefecture_code, o.source_url, o.name
