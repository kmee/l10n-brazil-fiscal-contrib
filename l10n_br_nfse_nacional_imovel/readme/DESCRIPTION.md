This module reports the real estate group (`IBSCBS/imovel`,
TCRTCInfoImovel) that the tax reform added to the NFS-e Nacional DPS
and that `l10n_br_nfse_nacional` does not fill:

- `cMun`: city of the property, taken from the address of the first
  unit or, lacking it, from the ISSQN city of the service line;
- `gLocacao` (TCRTCLocacaoImovel): the lease data of subitem 99.03,
  with the co-ownership share, the lease total amount and discounts
  (taken from the service line and editable) and the original due date;
- `gUnidImob` (TCRTCUnidadesImobiliarias): the real estate units, each
  identified by its CIB or by its address, with the municipal real
  estate registration and the amounts included in the rent that are not
  part of the IBS/CBS base (`gAjusteBCLocImoveis`,
  TCRTCValoresBCImoveis).

The group is part of the IBSCBS group, so it is reported only when the
NFS-e carries the tax reform data of `l10n_br_nfse_nacional`.

The module follows the rules of the group in Anexo VI of the NFS-e
Nacional (leiaute 1.04.01 published with NT 009): the group is reported
for the real estate operation indicators (020101, 020201, 020202,
020301 and 020401) outside the construction services, as rules E0928,
E0931 and E0932 require; the lease data goes along for subitem 99.03
only (E0936 and E0937). It refuses to build the DPS without units for
the indicators 020101, 020201 and 020301 (E0938), with unit adjustments
outside subitem 99.03 (E0939), with the social reducer outside the
residential lease NBS 1.1002.10.00 (E0944) or with an adjustment above
the lease total amount (E0966). The co-ownership share goes from 0 to
100% (E0940) and only the adjustment type 99 takes a description (E0949
and E0954).
