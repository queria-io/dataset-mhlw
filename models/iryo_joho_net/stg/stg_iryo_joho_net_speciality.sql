{{ config(materialized='ephemeral') }}

-- raw_iryo_joho_net_speciality を mart から読むための stg。列は raw のまま
SELECT * FROM {{ ref('raw_iryo_joho_net_speciality') }}
