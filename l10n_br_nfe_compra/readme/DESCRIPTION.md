This module fills the purchase information group of the NF-e (group ZB,
`compra`): the commitment note of a public procurement (`xNEmp`), the
purchase order (`xPed`) and the contract (`xCont`). The group is typical
of sales to public administration bodies, that pay against a commitment
note (nota de empenho).

The three values are fields of the fiscal document (*Others* tab):

- commitment note: typed in (up to 22 characters);
- customer purchase order: computed from the purchase order of the
  document lines (`partner_order`, also reported per item in `xPed`)
  when all of them have the same one, otherwise from the reference of
  the customer invoice (where Odoo copies the customer reference of the
  sale order); it can be edited;
- contract: typed in.

The group is not written in the NFC-e nor in the NF-e with the
simplified DANFE (rule ZB01-10, rejection 762).

Before the NF-e is confirmed the module refuses an NF-e with ICMS relief
for a sale to a public body (`motDesICMS` 8) without the commitment note
(rule ZB02-10, rejection 359, applied at the discretion of each state).
