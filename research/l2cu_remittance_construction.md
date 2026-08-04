# L2CU Remittance Construction

The household-round remittance treatment is built from two verified components: member-migrant remittances (`mig_living_remittance`) and external non-household remittances from abroad (`remittance_hh`).

`uzb_any_remittance` equals 1 if either verified component is positive. It equals 0 only when both components establish non-receipt, including the structural no-migrant case for the member-migrant component. Amounts are preserved separately and are only summed when observed currencies are not conflicting.
