{# 市区町村別・年別の自殺者数。
   1 行 = 年 × 集計地（住居地／発見地）× 市区町村 × 性 × 属性区分 × 区分 の自殺者数。 #}

{{ config(materialized='table') }}

select
    year,
    location_basis,
    prefecture_code,
    local_gov_code,
    city_code,
    municipality,
    area_level,
    sex,
    attribute,
    category,
    parent_category,
    count
from {{ ref('stg_suicide_municipality') }}
