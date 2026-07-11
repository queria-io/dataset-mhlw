{# 介護サービス情報公表システムの事業所生データ。
   main.py が全サービス種類の CSV を統合して .fdl/kaigo_establishment.ndjson に保存する。
   型変換・座標クレンジングは stg 以降で行うため全列 VARCHAR で読む。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.fdl/kaigo_establishment.ndjson',
    format='newline_delimited',
    columns={
        'local_gov_code': 'VARCHAR',
        'prefecture': 'VARCHAR',
        'city': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'service_type': 'VARCHAR',
        'address': 'VARCHAR',
        'address_note': 'VARCHAR',
        'latitude': 'VARCHAR',
        'longitude': 'VARCHAR',
        'phone': 'VARCHAR',
        'fax': 'VARCHAR',
        'corporate_number': 'VARCHAR',
        'corporate_name': 'VARCHAR',
        'establishment_number': 'VARCHAR',
        'available_days': 'VARCHAR',
        'available_days_note': 'VARCHAR',
        'capacity': 'VARCHAR',
        'url': 'VARCHAR',
        'shared_with_disability': 'VARCHAR',
        'meets_ltci_standard': 'VARCHAR',
        'meets_disability_welfare_standard': 'VARCHAR',
        'note': 'VARCHAR'
    }
)
