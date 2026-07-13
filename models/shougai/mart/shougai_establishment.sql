{# 全国の障害福祉サービス等事業所。緯度経度が有効な事業所には POINT ジオメトリを付与する。 #}

{{ config(materialized='table', alias='establishment') }}

select
    establishment_number,
    service_type,
    name,
    name_kana,
    local_gov_code,
    prefecture_code,
    city_code,
    designating_authority,
    address_city,
    address_detail,
    latitude,
    longitude,
    case
        when latitude is not null and longitude is not null
        then ST_Point(longitude, latitude)
    end as geometry,
    phone,
    fax,
    url,
    corporate_number,
    corporate_name,
    corporate_name_kana,
    corporate_address_city,
    corporate_address_detail,
    capacity,
    hours_weekday,
    hours_saturday,
    hours_sunday,
    hours_holiday,
    closed_days,
    available_days_note,
    system_no
from {{ ref('stg_shougai_establishment') }}
