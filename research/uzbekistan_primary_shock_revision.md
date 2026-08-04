# Uzbekistan primary shock revision

`uzb_any_verified_shock` is retained as constructed. No coding error was found.

## Included source variables

- `work_lost_hh`: household member lost job/stopped working over the past month; contributes through `uzb_work_loss_shock`.
- `change_important_type`: major illness, major injury, or death; contributes through `uzb_major_health_or_death_shock`.

## Excluded variables

- Service disruption variables including water, gas, and heat disruption are retained separately and are not climate shocks.
- National economic challenge opinion variables are excluded because they are not household shocks.
- Ordinary employment status and unverified shock fields are not included.

## Coding, missingness, and coexistence

The broad-shock indicator equals 1 when either verified component is observed as present. It equals 0 when verified components indicate no event or when only excluded service disruption is observed. Missing work-loss with a verified health/death shock can still yield a broad-shock value of 1. Multiple shock types may coexist.

## Comparison with Kyrgyzstan

Kyrgyzstan `lik_any_shock` is a 12-month household shock exposure from an event roster. Uzbekistan `uzb_any_verified_shock` is a past-month household-round indicator covering work loss and major health/injury/death events. Both are household-level exposure concepts, but recall period, survey unit, and included shock domains differ.
