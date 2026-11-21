Issuance of the Electronic Passenger Ticket (`BP-e`, `model 63`, layout 1.00)
from the fiscal document (`l10n_br_fiscal.document`) with document type 63 of
`l10n_br_fiscal`, following the pattern of `l10n_br_mdfe`: the layout groups
come from `l10n_br_bpe_spec` and are stacked onto the fiscal document.

The BP-e has been mandatory since 2019-07-01 for intercity, interstate and
international passenger transport by road, water and rail (Ajuste SINIEF
01/17, clause 18-A, as worded by Ajuste SINIEF 22/18).

The module:

- builds the BP-e XML: `ide`, `emit` (from the company), `comp` (from the
  document partner, when provided), `infPassagem` and `infPassageiro`,
  `infViagem`, `infValorBPe` (one `Comp` per fiscal document line), `imp`
  (line ICMS, the `IBSCBS` group and `vTotDFe`), `pag`, `infAdic`,
  `infRespTec` and the `infBPeSupl` QR Code;
- computes IBS and CBS with the OCA fiscal engine (tax classification and
  line taxes) and fills the `IBSCBS` group of NT 2025.001 RTC;
- applies the `vTotDFe` rule of NT 2026.004 v1.01: equal to `vBP` in 2026 and
  `vBP` plus IBS and CBS from 2027, by local issue date;
- generates the access key, signs the XML with the company certificate and
  validates it against the BP-e XSD of `nfelib`;
- transmits the BP-e (synchronous `BPeRecepcao` service, message compressed
  with GZip and encoded in Base64) and records the authorization protocol;
- sends the cancellation (110111) and no-boarding (110115) events.

The transmission uses its own client (`bpe_client`), built on
`brazil_fiscal_client`, following the same pattern as the CT-e and MDF-e
clients of `nfelib`, which does not have a BP-e client yet. It follows MOC
BP-e 1.00b (taxpayer guidance manual, items 3.3 and 3.4): SOAP 1.2, request in
`bpeDadosMsg`, response in `bpeResultMsg`, no SOAP header. The authorizer
addresses (MG, MS, MT, PR, SP and SVRS for the other states) and the QR Code
address are those of the BP-e Portal
(https://dfe-portal.svrs.rs.gov.br/BPe/Servicos).
