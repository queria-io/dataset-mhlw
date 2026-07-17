{# 型変換。人数は集計結果 10 未満のマスク（「‐」等）が既に NULL で入るため、
   数値でない値は try_cast で NULL になる。年度は整数へ。 #}

select
    try_cast(fiscal_year as INTEGER) as fiscal_year,
    test_item,
    unit,
    prefecture_code,
    prefecture,
    value_class,
    sex,
    age_class,
    try_cast("count" as BIGINT) as count
from {{ ref('raw_health_checkup') }}
