- The percentage of ISSQN base adjustment (`pAjusteBCISSQN`, rule E0453)
  is not reported: the fiscal line has a deduction amount only.
- Rules that depend on the municipal parameters or on national
  registries are left to the ADN: E0436 (MEI), E0445 (special tax
  regime), E0448 (municipal exemption benefit), E0437 (IBS/CBS
  classification without taxation), E0449 to E0452 and E0455
  (agreement status of the municipality and Simples Nacional services),
  E0444, E0446, E0447 and E0454 (municipal parameters of the service),
  E0466 (IBGE code), E0478 to E0488 (supplier registration) and E1538
  (NIF of a foreign supplier).
- Only the first line of the NFS-e is reported, as in
  `l10n_br_nfse_nacional`, so the ISSQN deduction is the one of that
  line.
- The fields are on the fiscal document form only; the invoice form of
  `l10n_br_account` does not show them.
