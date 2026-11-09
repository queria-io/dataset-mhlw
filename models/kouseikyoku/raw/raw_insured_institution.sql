{# 地方厚生局「コード内容別医療機関一覧表」の生データ。
   main.py が 8 局の一覧を 1 機関 1 行に整形して .queria/kouseikyoku_insured_institution.ndjson に保存する。
   開設者と管理者は個人の氏名を含むので取り込んでいない。 #}

{{ config(materialized='table') }}

select *
from read_json(
    '.queria/kouseikyoku_insured_institution.ndjson',
    format='newline_delimited',
    columns={
        'as_of': 'VARCHAR',
        'bureau': 'VARCHAR',
        'medical_institution_code': 'VARCHAR',
        'prefecture_code': 'VARCHAR',
        'fee_schedule': 'VARCHAR',
        'institution_number': 'VARCHAR',
        'name': 'VARCHAR',
        'address': 'VARCHAR',
        'phone': 'VARCHAR',
        'designated_on': 'VARCHAR',
        'designation_reason': 'VARCHAR',
        'designation_period_start': 'VARCHAR',
        'annex_institution_number': 'VARCHAR',
        'full_time_doctors': 'INTEGER',
        'full_time_dentists': 'INTEGER',
        'full_time_pharmacists': 'INTEGER',
        'part_time_doctors': 'INTEGER',
        'part_time_dentists': 'INTEGER',
        'part_time_pharmacists': 'INTEGER',
        'beds': 'STRUCT(kind VARCHAR, beds INTEGER)[]',
        'departments': 'VARCHAR[]',
        'categories': 'VARCHAR[]',
        'status': 'VARCHAR'
    }
)
