{# 型変換。指標値は "-"（該当なし・非公表）が混じるため try_cast で数値化し、
   変換できない値は NULL にする。最終更新日は「YYYY年MM月DD日」形式を DATE へ変換する。
   育児休業取得率は雇用管理区分ごとに分割される指標のうち先頭区分（区分１）の代表値。 #}

select
    company_name,
    corporate_number,
    industry,
    industry_detail,
    prefecture,
    company_size,
    market_segment,
    securities_code,
    kurumin,
    eruboshi_stage,
    childcare_leave_category,
    try_cast(childcare_leave_male_pct as DOUBLE) as childcare_leave_male_pct,
    try_cast(childcare_leave_female_pct as DOUBLE) as childcare_leave_female_pct,
    try_cast(avg_monthly_overtime_hours as DOUBLE) as avg_monthly_overtime_hours,
    try_cast(paid_leave_rate_pct as DOUBLE) as paid_leave_rate_pct,
    try_cast(women_in_kakaricho_pct as DOUBLE) as women_in_kakaricho_pct,
    try_cast(women_in_management_pct as DOUBLE) as women_in_management_pct,
    try_cast(women_on_board_pct as DOUBLE) as women_on_board_pct,
    try_cast(gender_wage_gap_all_pct as DOUBLE) as gender_wage_gap_all_pct,
    try_cast(gender_wage_gap_regular_pct as DOUBLE) as gender_wage_gap_regular_pct,
    try_cast(gender_wage_gap_nonregular_pct as DOUBLE) as gender_wage_gap_nonregular_pct,
    wage_gap_period,
    try_strptime(last_updated, '%Y年%m月%d日')::DATE as last_updated
from {{ ref('raw_josei_company') }}
