- Rule E0373 (the CIB is 7 characters and a check digit) is checked by
  the ADN only: the module checks the length of the schema, not the
  check digit, whose algorithm is not in the leiaute.
- Rule E0380 (the CEP of the site belongs to the municipality of the
  service location) is not checked: the module has no CEP to
  municipality table.
- Rule E0384 asks for the foreign address group (`endExt`) when the
  service location is abroad (`cPaisPrestacao`). The module chooses
  between CEP and `endExt` by the country of the site address.
- The fields are on the fiscal document form only; the invoice form of
  `l10n_br_account` does not show them.
