This module adds the multimodal transport modal (modal `06`) to the
CT-e 4.00. The `l10n_br_cte` module already lets the user choose
"Multimodal" as the transport modal, but it only serializes the road,
air, waterway, railway and pipeline modals: with modal `06` the
`infModal` group was left empty.

The module fills the `multimodal` group of the `infModal` (schema
`cteMultiModal_v4.00.xsd`, layout 3.6 of the Annex I of the CT-e
Taxpayer Guidance Manual, MOC 4.00):

- `COTM`: number of the certificate of the multimodal transport
  operator;
- `indNegociavel`: negotiable indicator (0 not negotiable, 1
  negotiable);
- `seg`: optional insurance group, with the insurance company name and
  CNPJ (`infSeg/xSeg`, `infSeg/CNPJ`), the policy number (`nApol`) and
  the endorsement number (`nAver`).

The SEFAZ validates the XML of the modal against its own schema and
rejects the CT-e with code 580 when it fails (MOC 4.00 Annex I, rule
G026). Since the CT-e schema does not check the modal (`xs:any` with
`processContents="skip"`), the module refuses to export a multimodal
CT-e without the required elements: `COTM` and `indNegociavel`, and
the insurance company name, policy and endorsement when any insurance
field is filled. The insurance company CNPJ may be empty, as the layout
allows (`TCnpjOpc`).
