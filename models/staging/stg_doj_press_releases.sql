with source as (
    select * from {{ source('doj', 'raw_doj_press_releases') }}
),

cleaned as (
    select
        uuid                                       as release_id,
        'DOJ'                                      as source_agency,
        title,
        to_timestamp(date_epoch)::date             as release_date,
        url,
        regexp_replace(body, '<[^>]+>', ' ', 'g')  as body_text,
        fetched_at
    from source
)

select
    *,
    regexp_matches(
        body_text,
        '\b(aml|bsa|fincen|money laundering|bank secrecy|sanctions|fraud)\b',
        'i'
    ) as is_fincrime_candidate
from cleaned