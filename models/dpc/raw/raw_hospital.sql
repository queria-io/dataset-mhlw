{# DPC 退院患者調査 施設概要表の生データ。
   main.py が年度ごとの施設概要表を .queria/dpc_hospital.ndjson に統合する。
   型変換は stg 以降で行うため全列 VARCHAR で読む。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.queria/dpc_hospital.ndjson',
    format='newline_delimited',
    columns={
        'fiscal_year': 'VARCHAR',
        'notification_number': 'VARCHAR',
        'serial_number': 'VARCHAR',
        'city_code': 'VARCHAR',
        'hospital_name': 'VARCHAR',
        'hospital_category': 'VARCHAR',
        'dpc_beds': 'VARCHAR',
        'dpc_basic_fee': 'VARCHAR',
        'dpc_bed_ratio': 'VARCHAR',
        'rehabilitation_beds': 'VARCHAR',
        'community_care_beds': 'VARCHAR',
        'psychiatric_beds': 'VARCHAR',
        'long_term_care_beds': 'VARCHAR',
        'tuberculosis_beds': 'VARCHAR',
        'total_beds': 'VARCHAR',
        'months_submitted': 'VARCHAR'
    }
)
