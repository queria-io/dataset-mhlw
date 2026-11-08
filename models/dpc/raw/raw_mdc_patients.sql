{# DPC 退院患者調査 MDC 別医療機関別件数の生データ。
   main.py が年度ごとの表を long 形式に展開して .queria/dpc_mdc_patients.ndjson に保存する。
   「-」（10 症例未満または 0 件）の欄は書き出していない。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.queria/dpc_mdc_patients.ndjson',
    format='newline_delimited',
    columns={
        'fiscal_year': 'VARCHAR',
        'notification_number': 'VARCHAR',
        'serial_number': 'VARCHAR',
        'mdc': 'VARCHAR',
        'surgery': 'VARCHAR',
        'patients': 'VARCHAR'
    }
)
