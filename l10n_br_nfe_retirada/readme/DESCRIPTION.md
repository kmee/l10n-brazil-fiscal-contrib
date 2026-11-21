This module fills the pickup address group of the NF-e (group F,
`retirada`), that the layout asks only when the goods leave from an
address other than the issuer address: a branch warehouse, a general
warehouse (armazém geral), a third party plant and so on.

The field already exists in `l10n_br_nfe`, but nothing filled it. Here
it is computed on the outgoing NF-e from the deliveries of the invoice:
when all of them leave from the same warehouse and the address of that
warehouse is not the address of the issuer company, the warehouse
address becomes the pickup address. It can be edited on the fiscal
document (*Delivery* tab).

Before the NF-e is confirmed the module refuses a pickup address in the
NFC-e or in the NF-e with the simplified DANFE (rule F01-10, rejection
669) and a pickup address without CNPJ/CPF, street, number, district or
city, required by the layout.
