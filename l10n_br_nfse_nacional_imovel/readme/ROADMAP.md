- The lease total amount (`vTotOper`) starts from the service amount of
  the line, which is the lessor share when the property has several
  owners: change it to the total of the lease in that case, as the
  leiaute asks.
- Rules E0929 (IBGE code of the city) and E0933 (CIB check digit, whose
  algorithm is not in the leiaute) are left to the ADN.
- The condominium subitem 99.05 (rule without code that makes the group
  mandatory) and the debit and credit adjustment NFS-e (`tpNFSeDebito`,
  `tpNFSeCredito`) are not handled: they are not in the schema of the
  DPS 1.01.
- The operation type with real estate (`tpOper`) and the movable goods
  group (`bensMoveis`) of the IBSCBS group are not reported.
- The fields are on the fiscal document form only; the invoice form of
  `l10n_br_account` does not show them.
