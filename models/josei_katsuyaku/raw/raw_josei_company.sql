{# 女性の活躍推進企業データベースの企業別生データ。
   main.py が全体版 CSV を主要列に絞って .queria/josei_katsuyaku_company.ndjson に保存する。
   型変換は stg 以降で行うため全列 VARCHAR で読む。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.queria/josei_katsuyaku_company.ndjson',
    format='newline_delimited',
    columns={
        'company_name': 'VARCHAR',
        'corporate_number': 'VARCHAR',
        'industry': 'VARCHAR',
        'industry_detail': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'company_size': 'VARCHAR',
        'market_segment': 'VARCHAR',
        'securities_code': 'VARCHAR',
        'kurumin': 'VARCHAR',
        'eruboshi_stage': 'VARCHAR',
        'childcare_leave_category': 'VARCHAR',
        'childcare_leave_male_pct': 'VARCHAR',
        'childcare_leave_female_pct': 'VARCHAR',
        'avg_monthly_overtime_hours': 'VARCHAR',
        'paid_leave_rate_pct': 'VARCHAR',
        'women_in_kakaricho_pct': 'VARCHAR',
        'women_in_management_pct': 'VARCHAR',
        'women_on_board_pct': 'VARCHAR',
        'gender_wage_gap_all_pct': 'VARCHAR',
        'gender_wage_gap_regular_pct': 'VARCHAR',
        'gender_wage_gap_nonregular_pct': 'VARCHAR',
        'wage_gap_period': 'VARCHAR',
        'last_updated': 'VARCHAR'
    }
)
