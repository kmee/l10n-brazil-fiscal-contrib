Issuance of the Electronic Electricity Bill (`NF3e`, `model 66`), mandatory
for electricity distributors and licensees (Ajuste SINIEF 01/19), from the
`l10n_br_fiscal` fiscal document with document type 66.

The module injects the `l10n_br_nf3e_spec` models into the fiscal document and
its lines (`spec_driven_model` stacking, following the same pattern as
`l10n_br_mdfe` and `l10n_br_cte`) and:

- numbers the document by series and builds the NF3e access key (MOC NF3e
  1.00a, Overview, item 2.1: 7-digit numeric code, issuance type and
  authorizer site), with a modulo 11 check digit, including for alphanumeric
  CNPJ;
- generates the XML with the groups `ide`, `emit`, `dest`, `acessante`
  (consumer unit), `gMed` (meters), `NFdet` (items with `prod` and `imposto`),
  `total`, `gFat` (invoice), `gANEEL` (billing history), `infAdic` and the
  `infNF3eSupl` QR Code (MOC NF3e 1.00a, Overview, item 9.2);
- carries into the XML the taxes computed by the OCA fiscal engine: ICMS
  (group chosen by the CST), PIS, COFINS, withholdings and the item `IBSCBS`
  group with the `IBSCBSTot` total (NT 2025.001 RTC v1.14a);
- computes `vNF` (MOC, rule G157) and `vTotDFe`, which repeats `vNF` in 2026
  and adds IBS and CBS from 2027, by issue date (NT 2025.001 RTC v1.14a,
  item 9, rules 360 and 365, and NT 2026.004 v1.01);
- signs the XML with the company certificate, validates it against the
  `nfelib` XSD and stores the signed XML in the authorization event of the
  document;
- builds, signs and validates the XML of the cancellation event (110111).

Transmission to the authorizer is not available yet: see the roadmap.
