- Rules I05g-10 (the state allows the group) and I05h-10 (the code is
  valid in the state table), created by NT 2019.001 v1.63 and v1.64, are
  applied by each state at its discretion against its own tables and are
  not checked here.
- The amount is the percentage applied to the ICMS base of the item.
  When the state rule uses another base, change the amount on the line.
- The percentage keeps 2 decimals on the line (the spec field), while
  the layout accepts up to 4.
- The product holds a single code per company; the other groups of an
  item (up to 4) are typed on the line.
- The groups are shown on the fiscal document line form; the invoice
  line form (`l10n_br_account`) does not show them yet.
