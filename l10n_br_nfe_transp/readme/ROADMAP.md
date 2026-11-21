- The vehicle is not carried from the sale order or the delivery to the
  invoice: it is chosen on the fiscal document (or computed from the
  carrier).
- The optional extension of rule X02-20 to internal operations between
  different cities (at the discretion of each state) is not applied.
- The choice between vehicle/trailers, wagon (`vagao`) and ferry
  (`balsa`) is not handled: wagon and ferry are not filled.
- The freight CFOP of the ICMS retention is not checked against the CFOP
  table of the NF-e portal (rule X16-10, rejection 722).
- The ICMS retention is typed in: it is not computed from the freight
  service purchase.
