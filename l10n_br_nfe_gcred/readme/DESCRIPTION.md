This module reports the ICMS presumed credit of the NF-e items in the
`gCred` group of the product (fields `cCredPresumido`, `pCredPresumido`
and `vCredPresumido`, up to 4 groups per item), created by NT 2019.001
v1.60 and named `gCred` (I05g) by v1.62.

The benefit code and the percentage are set on the product, per company
(each company belongs to one state, and the code is the one granted by
that state, the same code used in the EFD). The fiscal document lines of
the product get one group with that code and percentage, and the amount
is the percentage applied to the ICMS base of the line. The group is
updated when the product or the ICMS base of the line changes, and other
groups can be typed on the line. Incoming NF-e keep the groups of the
supplier XML.

Before the NF-e is issued, the module refuses what the schema rejects:
more than 4 groups per item, a code that is not 8 or 10 characters long
without spaces, or a percentage out of the 0 to 999 range.
