{# 型変換。人数は秘匿セルが既に NULL で入るため、数値でない値は try_cast で NULL になる。 #}

select
    try_cast(year as INTEGER) as year,
    location_basis,
    prefecture_code,
    local_gov_code,
    left(local_gov_code, 5) as city_code,
    municipality,
    area_level,
    sex,
    attribute,
    category,
    parent_category,
    try_cast("count" as BIGINT) as count
from {{ ref('raw_suicide_municipality') }}
