- The commitment note and the contract are typed in: there is no link
  with a public procurement or contract model (for instance the OCA
  `contract` module).
- The fields are on the fiscal document form, not on the invoice form.
- Importing an incoming NF-e keeps the `compra` group in the
  `nfe40_compra` record, but does not fill the three fields of the
  document.
- Rules ZB02-20 and ZB02-30 (commitment note invalid or unknown in the
  state) depend on the registry of each state and are not checked.
