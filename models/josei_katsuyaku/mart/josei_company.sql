{# 女性の活躍推進企業データベースの企業別 女性活躍・両立支援指標。
   1 企業 1 レコード（法人番号で houjin_bangou / gbizinfo と結合可）。
   指標は企業の任意公表のため、開示していない企業は当該列が NULL になる。 #}

{{ config(materialized='table', alias='company') }}

select
    corporate_number,
    company_name,
    industry,
    industry_detail,
    prefecture,
    company_size,
    market_segment,
    securities_code,
    eruboshi_stage,
    kurumin,
    women_in_kakaricho_pct,
    women_in_management_pct,
    women_on_board_pct,
    gender_wage_gap_all_pct,
    gender_wage_gap_regular_pct,
    gender_wage_gap_nonregular_pct,
    wage_gap_period,
    childcare_leave_category,
    childcare_leave_male_pct,
    childcare_leave_female_pct,
    avg_monthly_overtime_hours,
    paid_leave_rate_pct,
    last_updated
from {{ ref('stg_josei_company') }}
