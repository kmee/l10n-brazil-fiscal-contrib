- The groups are filled by the picking invoicing wizard. Invoices created
  in other ways can call `account.move.line._fill_nfe40_arma()` or have
  the groups typed in.
- The number of groups is not compared with the item quantity: the MOC
  has no such rule.
- The picking invoicing hook is not covered by the tests, which build
  the groups from the serial numbers directly.
