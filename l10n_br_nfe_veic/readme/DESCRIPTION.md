This module reports the new vehicle group of the NF-e items (group JA,
`veicProd`) from the serial numbers of the stock.

The data shared by the vehicles of a model (color, power, displacement,
weights, fuel type, RENAVAM and DENATRAN codes, operation type and so
on) is set once on the product (*New Vehicle Model*). Each vehicle is a
serial number of the product: its name is the chassis (VIN), and it
holds the vehicle serial and the engine number.

When an invoice is created from a delivery (picking invoicing), the
invoice line of a vehicle gets its own new vehicle group: the vehicle
model of the product completed with the chassis, serial and engine
number of the serial number shipped. The group describes one vehicle,
so it is only filled when the line has a single serial number. It can
be edited on the invoice line and on the fiscal document line (*New
Vehicle* tab).

The chassis is checked against the layout (17 capital letters or
digits). Before the NF-e is confirmed the module refuses an item whose
group misses a field required by the layout, and refuses the group in
the NFC-e (rule J01-10, rejection 736, NT 2013/005).
