{# 全国の介護サービス事業所。緯度経度が有効な事業所には POINT ジオメトリを付与する。 #}

{{ config(materialized='table') }}

select
    establishment_number,
    service_type,
    name,
    name_kana,
    local_gov_code,
    prefecture_code,
    city_code,
    prefecture,
    city,
    address,
    address_note,
    latitude,
    longitude,
    case
        when latitude is not null and longitude is not null
        then ST_Point(longitude, latitude)
    end as geometry,
    phone,
    fax,
    corporate_number,
    corporate_name,
    capacity,
    available_days,
    available_days_note,
    url,
    shared_with_disability,
    meets_ltci_standard,
    meets_disability_welfare_standard,
    note
from {{ ref('stg_establishment') }}
