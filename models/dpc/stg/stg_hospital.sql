{# 型変換と施設類型の付与。
   施設類型は告示番号の先頭の桁で決まる（集計条件の「集計対象施設数」の内訳と一致する）。
   平成 30 年度に Ⅰ群・Ⅱ群・Ⅲ群 から 大学病院本院群・DPC 特定病院群・DPC 標準病院群 へ改称された。 #}

select
    try_cast(fiscal_year as INTEGER) as fiscal_year,
    notification_number,
    nullif(serial_number, '-') as serial_number,
    hospital_name,
    case left(notification_number, 1)
        when '1' then if(try_cast(fiscal_year as INTEGER) < 2018, 'DPC対象病院Ⅰ群', '大学病院本院群')
        when '2' then if(try_cast(fiscal_year as INTEGER) < 2018, 'DPC対象病院Ⅱ群', 'DPC特定病院群')
        when '3' then if(try_cast(fiscal_year as INTEGER) < 2018, 'DPC対象病院Ⅲ群', 'DPC標準病院群')
        when '9' then 'DPC準備病院'
        when '0' then '出来高算定病院'
    end as facility_group,
    nullif(hospital_category, '') as hospital_category,
    left(city_code, 2) as prefecture_code,
    city_code,
    {{ local_government_code('city_code') }} as local_gov_code,
    try_cast(dpc_beds as INTEGER) as dpc_beds,
    nullif(dpc_basic_fee, '') as dpc_basic_fee,
    try_cast(dpc_bed_ratio as DOUBLE) as dpc_bed_ratio,
    try_cast(rehabilitation_beds as INTEGER) as rehabilitation_beds,
    try_cast(community_care_beds as INTEGER) as community_care_beds,
    try_cast(psychiatric_beds as INTEGER) as psychiatric_beds,
    try_cast(long_term_care_beds as INTEGER) as long_term_care_beds,
    try_cast(tuberculosis_beds as INTEGER) as tuberculosis_beds,
    try_cast(total_beds as INTEGER) as total_beds,
    try_cast(months_submitted as INTEGER) as months_submitted
from {{ ref('raw_hospital') }}
