This module reports the firearm groups of the NF-e items (group L,
`arma`) from the serial numbers of the stock.

The firearm type (permitted or restricted use) and its full description
(caliber, brand, capacity, action type, length...) are set once on the
product. Each firearm is a serial number of the product: its name is
the firearm serial number, and it holds the barrel serial number.

When an invoice is created from a delivery (picking invoicing), the
invoice line of a firearm gets one firearm group per serial number
shipped. The groups can be edited on the invoice line and on the fiscal
document line (*Firearms* tab).

Before the NF-e is confirmed the module refuses a group with an empty
field (all four are required by the layout), more than 500 groups in
one item (layout limit) and the groups in the NFC-e (rule L01-10,
rejection 738, NT 2013/005).
