- Rules E0398 (the CEP of the venue belongs to the municipality of the
  service location) and E0402 (foreign address when the service location
  is abroad) are not checked: the module chooses between CEP and
  `endExt` by the country of the venue address.
- Rule E0393 refers to a municipality code of the event (`cMun`, only for
  subitems 12.13 and 17.10) that is not in the schema of the DPS 1.01,
  so it is not reported.
- The fields are on the fiscal document form only; the invoice form of
  `l10n_br_account` does not show them.
