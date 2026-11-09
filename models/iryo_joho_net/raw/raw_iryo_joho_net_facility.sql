{# 医療情報ネット オープンデータの施設票の生データ。
   main.py が 5 種類の施設票の共通の列を .queria/iryo_joho_net_facility.ndjson に統合する。
   型変換は stg 以降で行うため全列 VARCHAR で読む。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.queria/iryo_joho_net_facility.ndjson',
    format='newline_delimited',
    columns={
        'as_of': 'VARCHAR',
        'id': 'VARCHAR',
        'facility_type_code': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'short_name': 'VARCHAR',
        'short_name_kana': 'VARCHAR',
        'name_en': 'VARCHAR',
        'prefecture_code': 'VARCHAR',
        'municipality_code': 'VARCHAR',
        'address': 'VARCHAR',
        'latitude': 'VARCHAR',
        'longitude': 'VARCHAR',
        'url': 'VARCHAR',
        'general_beds': 'VARCHAR',
        'long_term_care_beds': 'VARCHAR',
        'long_term_care_medical_insurance_beds': 'VARCHAR',
        'long_term_care_ltci_beds': 'VARCHAR',
        'psychiatric_beds': 'VARCHAR',
        'tuberculosis_beds': 'VARCHAR',
        'infectious_beds': 'VARCHAR',
        'total_beds': 'VARCHAR'
    }
)
