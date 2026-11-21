- The groups are filled by the picking invoicing wizard. Invoices created
  in other ways can call `account.move.line._fill_nfe40_veicprod()` or
  have the group typed in.
- An invoice line with several vehicles (several serial numbers) gets
  no group: it is not split into one line per vehicle.
- The total of the NF-e of a direct billing (`tpOp` 2, rule W16-10) and
  the exceptions of rules N12-70, N16-04 and N16-20 for vehicles are
  not handled by this module.
- The picking invoicing hook is not covered by the tests, which build
  the group from the serial number directly.
