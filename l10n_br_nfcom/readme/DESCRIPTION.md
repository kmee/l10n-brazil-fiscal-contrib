Issuance of the Electronic Communication Services Invoice (`NFCom`,
`model 62`) from the Odoo fiscal document (`l10n_br_fiscal.document`),
following the same pattern as `l10n_br_nfe` and `l10n_br_mdfe`: the
`l10n_br_nfcom_spec` models are stacked onto the document and the line
(`spec_driven_model`) and the XML is built with the nfelib bindings.

The NFCom replaces models 21 (NFSC) and 22 (NFST) for communication and
telecommunication services (Ajuste SINIEF 7/22) and has been mandatory since
2025-11-01 (Ajuste SINIEF 34/24). The `IBSCBS` group of the tax reform follows
NT 2025.001 RTC.

The module:

- creates fiscal document type 62, which `l10n_br_fiscal` does not have yet;
- generates the access key in the NFCom format (MOC NFCom 1.00a, item 2.1.3:
  `cUF`, `AAMM`, `CNPJ`, `mod`, `serie`, `nNF`, `tpEmis`, `nSiteAutoriz`, 7-digit
  `cNF` and `cDV` in modulo 11, item 7.3);
- builds the groups `ide`, `emit`, `dest`, `assinante`, `det` (`prod` and
  `imposto`), `total` and `infAdic`, and the `infNFComSupl` with the QR Code
  URL of the state authorizer (services page of the NFCom Portal);
- carries ICMS (groups `ICMS00`, `ICMS20`, `ICMS40`, `ICMS51`, `ICMS90` and
  `ICMSSN`, by CST and company regime), PIS, COFINS and IBS and CBS (`IBSCBS`
  on the item and `IBSCBSTot` on the total) computed by the `l10n_br_fiscal`
  fiscal engine;
- computes the item `vProd` and `vNF` by rules G86 and G137 of Annex I of the
  MOC;
- signs the XML with the company certificate and validates it against the
  nfelib XSD when the document is confirmed, storing the signed XML in the
  authorization event;
- builds and signs the cancellation event (`110111`, MOC item 6.1), validated
  against the XSD.

Transmission to the authorizer is not in the module yet (see the roadmap): on
sending, the document warns that transmission is not available.
