{# 型変換と座標クレンジング。
   緯度経度は 0.0（欠測）や日本国外の明らかな誤登録値が混在しうるため、
   日本の bbox（緯度 20〜46 / 経度 122〜154）に収まる値のみ採用し、それ以外は NULL にする。
   都道府県コード又は市区町村コードは 5 桁の全国地方公共団体コード（チェックデジットなし）で、
   上 2 桁が都道府県コード。市区町村コードはそのまま 5 桁を用いる。 #}

with typed as (
    select
        local_gov_code,
        substr(local_gov_code, 1, 2) as prefecture_code,
        local_gov_code as city_code,
        system_no,
        designating_authority,
        corporate_name,
        corporate_name_kana,
        corporate_number,
        corporate_address_city,
        corporate_address_detail,
        corporate_phone,
        corporate_fax,
        corporate_url,
        service_type,
        name,
        name_kana,
        establishment_number,
        address_city,
        address_detail,
        phone,
        fax,
        url,
        try_cast(latitude as DOUBLE) as latitude_raw,
        try_cast(longitude as DOUBLE) as longitude_raw,
        hours_weekday,
        hours_saturday,
        hours_sunday,
        hours_holiday,
        closed_days,
        available_days_note,
        try_cast(capacity as INTEGER) as capacity
    from {{ ref('raw_shougai_establishment') }}
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
