{# 障害福祉サービス等情報公表システムの事業所生データ。
   main.py が全サービス種類の CSV を統合して .queria/shougai_establishment.ndjson に保存する。
   型変換・座標クレンジングは stg 以降で行うため全列 VARCHAR で読む。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.queria/shougai_establishment.ndjson',
    format='newline_delimited',
    columns={
        'local_gov_code': 'VARCHAR',
        'system_no': 'VARCHAR',
        'designating_authority': 'VARCHAR',
        'corporate_name': 'VARCHAR',
        'corporate_name_kana': 'VARCHAR',
        'corporate_number': 'VARCHAR',
        'corporate_address_city': 'VARCHAR',
        'corporate_address_detail': 'VARCHAR',
        'corporate_phone': 'VARCHAR',
        'corporate_fax': 'VARCHAR',
        'corporate_url': 'VARCHAR',
        'service_type': 'VARCHAR',
        'name': 'VARCHAR',
        'name_kana': 'VARCHAR',
        'establishment_number': 'VARCHAR',
        'address_city': 'VARCHAR',
        'address_detail': 'VARCHAR',
        'phone': 'VARCHAR',
        'fax': 'VARCHAR',
        'url': 'VARCHAR',
        'latitude': 'VARCHAR',
        'longitude': 'VARCHAR',
        'hours_weekday': 'VARCHAR',
        'hours_saturday': 'VARCHAR',
        'hours_sunday': 'VARCHAR',
        'hours_holiday': 'VARCHAR',
        'closed_days': 'VARCHAR',
        'available_days_note': 'VARCHAR',
        'capacity': 'VARCHAR'
    }
)
