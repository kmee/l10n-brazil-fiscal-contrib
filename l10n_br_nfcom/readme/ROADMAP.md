- Transmission (goal: a contribution to nfelib). nfelib 3.3.0 has the NFCom
  bindings, but not the SOAP bindings (`nfelib/nfcom/soap/v1_0`) nor the
  client (`nfelib/nfcom/client/v1_0`) on top of `brazil_fiscal_client`, as
  already exist for NF-e, CT-e and MDF-e. The WSDL of the services
  `NFComRecepcao`, `NFComConsulta`, `NFComRecepcaoEvento` and
  `NFComStatusServico` are only served with mutual authentication (ICP-Brasil
  certificate) and MOC NFCom 1.00a (item 3.4.1) writes the namespace with a
  different case from the one used in the schemas (`NFCom` x `nfcom`), so the
  name of the `nfcomDadosMsg` element and the namespace of each service must
  be checked in the WSDL before generating the bindings. Reception is
  synchronous and the message is compressed with GZip and encoded in Base64
  (MOC, items 3.4.1 and 4.2); the authorizers are MG, MS, MT and SVRS
  (services page of the NFCom Portal). With the client in nfelib: submission,
  query, protocol (`nfcomProc`) and sending of the cancellation event already
  built by this module.
- NFCom `schema_validation` in nfelib: the `CommonMixin` does not know the
  NFCom XSD path and the module passes the path explicitly.
- Layout: the schemas are those of the package `PL_NFCOM_1.00_NT2026.002
  RTC_1.01` shipped with nfelib 3.3.0. NT 2026.004 v1.01 (production on
  2026-12-14) and NT 2026.005 v1.00 (Simples Nacional) are not in nfelib yet:
  regenerate `l10n_br_nfcom_spec` when they are.
- NT 2026.002 rules that depend on registration data: `CNPJCobrTerc` for items
  with `cClass` of group 110 (third-party billing) and rejection 310 (IBS/CBS
  group required for CRT 3).
- `IBSCBS` group: only `gIBSCBS`; missing are `gEstornoCred`, deferral, tax
  refund, reduction for government procurement and the municipal IBS separate
  from the state one (exported as zero, as in NF-e).
- Billing: groups `gFat` (competence period, due date, barcode, automatic
  debit, PIX), `gFatCentral`, `gCofat`, `gSub` (replacement), `gFidelidade`,
  `pgtoVinc` and `gRespTec`, and recurring billing from contracts.
- Items: `gProcRef`, `gRessarc`, `ICMSUFDest`, FUST, FUNTTEL, withholdings per
  item (`retTrib`), `indSemCST` and validation of the CFOP against the list of
  MOC item 7.7 and of `cClass` against the table of item 7.8.
- Contingency (`tpEmis` 2, `dhCont`, `xJust` and QR Code signature).
- DANFE-COM (Annex II of the MOC).
- Document type 62: move the record to the `l10n_br_fiscal` data and include
  62 in the IBS and CBS tax classifications (`tax_classification`) that apply
  to the NFCom.
- NFCom XML import.
