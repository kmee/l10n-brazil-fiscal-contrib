This module reports the fuel group of the NF-e items (group LA, `comb`)
and checks it against the SEFAZ validation rules.

The ANP product code (`cProdANP`) and description (`descANP`), the LPG
percentages and starting value (`pGLP`, `pGNn`, `pGNi`, `vPart`), the
CODIF, the biodiesel percentage (`pBio`) and the fuel origin
(`origComb`) are set once on the product and the fiscal document lines
of that product point to them. The group can be replaced on each line,
for instance to add the CIDE, the pump meter (`encerrante`) or the
quantity at ambient temperature (`qTemp`).

The consumption state (`UFCons`) is the state of the fuel group when it
is set, otherwise the state of the delivery address of the document
(`EX` for a foreign customer).

The LPG percentages are written with two decimals, so that their sum is
exactly 100. The ANP code is checked against the layout (9 digits) and
each origin percentage must be greater than 0.

Before the NF-e is confirmed the module refuses the data the SEFAZ
would reject:

- rule LA03c-10 (rejection 461, NT 2016.002): LPG percentages for an
  ANP code other than 210203001;
- rule LA03c-20 (rejection 855, NT 2016.002): LPG percentages that do
  not add up to 100;
- rule LA11-20 (rejection 379, NT 2015.002): pump meter in an NF-e
  (model 55) with a CFOP other than 5656 and 5667;
- rule LA16-10 (rejection 380, NT 2015.002): pump meter at the end not
  greater than at the start;
- rule LA18-20 (rejection 909, NT 2023.001): LPG with natural gas and
  no fuel origin, except for final consumers, complementary and return
  NF-e and the CFOP 5922 and 6922;
- rules LA21-10 and LA21-20 (rejection 958, NT 2023.001): origin
  percentages that do not add up to 100 (separately for national and
  imported origin in the LPG codes 210203001, 210203003, 210203004 and
  210203005), with a tolerance of 0.1.
