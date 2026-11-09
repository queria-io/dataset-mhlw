{# 型変換と座標クレンジング。
   市区町村コードは元データでは都道府県コードを除いた 3 桁なので、都道府県コードと合わせて 5 桁にする。
   緯度経度は日本の bbox（緯度 20〜46 / 経度 122〜154）に収まる値のみ採用し、それ以外は NULL にする。 #}

with typed as (
    select
        id,
        case facility_type_code
            when '1' then '病院'
            when '2' then '診療所'
            when '3' then '歯科診療所'
            when '4' then '助産所'
            when '5' then '薬局'
        end as facility_type,
        name,
        name_kana,
        short_name,
        short_name_kana,
        name_en,
        prefecture_code,
        prefecture_code || municipality_code as city_code,
        address,
        try_cast(latitude as DOUBLE) as latitude_raw,
        try_cast(longitude as DOUBLE) as longitude_raw,
        url,
        try_cast(general_beds as INTEGER) as general_beds,
        try_cast(long_term_care_beds as INTEGER) as long_term_care_beds,
        try_cast(long_term_care_medical_insurance_beds as INTEGER) as long_term_care_medical_insurance_beds,
        try_cast(long_term_care_ltci_beds as INTEGER) as long_term_care_ltci_beds,
        try_cast(psychiatric_beds as INTEGER) as psychiatric_beds,
        try_cast(tuberculosis_beds as INTEGER) as tuberculosis_beds,
        try_cast(infectious_beds as INTEGER) as infectious_beds,
        try_cast(total_beds as INTEGER) as total_beds,
        cast(as_of as DATE) as as_of
    from {{ ref('raw_iryo_joho_net_facility') }}
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
