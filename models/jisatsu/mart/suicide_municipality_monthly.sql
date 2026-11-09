{# 市区町村別・月別の自殺者数。
   1 行 = 年月 × 集計地（住居地／発見地）× 市区町村 × 性 × 属性区分（総数・年齢階級）× 区分 の自殺者数。 #}

{{ config(materialized='table') }}

select
    year,
    month,
    status,
    location_basis,
    prefecture_code,
    local_gov_code,
    city_code,
    municipality,
    area_level,
    sex,
    attribute,
    category,
    count
from {{ ref('stg_suicide_municipality_monthly') }}
