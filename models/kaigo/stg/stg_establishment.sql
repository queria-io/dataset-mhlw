{# 型変換と座標クレンジング。
   緯度経度は 0.0（欠測）や日本国外の明らかな誤登録値が混在するため、
   日本の bbox（緯度 20〜46 / 経度 122〜154）に収まる値のみ採用し、それ以外は NULL にする。
   全国地方公共団体コード（6 桁 = 5 桁自治体コード + チェックデジット）から
   都道府県コード（上 2 桁）・市区町村コード（上 5 桁）を導出する。 #}

with typed as (
    select
        local_gov_code,
        substr(local_gov_code, 1, 2) as prefecture_code,
        substr(local_gov_code, 1, 5) as city_code,
        prefecture,
        city,
        name,
        name_kana,
        service_type,
        address,
        address_note,
        try_cast(latitude as DOUBLE) as latitude_raw,
        try_cast(longitude as DOUBLE) as longitude_raw,
        phone,
        fax,
        corporate_number,
        corporate_name,
        establishment_number,
        available_days,
        available_days_note,
        try_cast(capacity as INTEGER) as capacity,
        url,
        shared_with_disability,
        meets_ltci_standard,
        meets_disability_welfare_standard,
        note
    from {{ ref('raw_establishment') }}
)

select
    * exclude (latitude_raw, longitude_raw),
    case
        when latitude_raw between 20 and 46 and longitude_raw between 122 and 154
        then latitude_raw
    end as latitude,
    case
        when latitude_raw between 20 and 46 and longitude_raw between 122 and 154
        then longitude_raw
    end as longitude
from typed
