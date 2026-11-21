- Only outgoing NF-e linked to deliveries (through
  `stock_picking_invoice_link`) get a computed pickup address. Deliveries
  from several warehouses with different addresses leave the field empty,
  to be filled by hand.
- The pickup address must have its own CNPJ or CPF: a child address that
  relies on the CNPJ of its parent company is refused.
- The CNPJ/CPF registry rules of the pickup address (F02-10, F02-20) are
  checked by the SEFAZ only.
