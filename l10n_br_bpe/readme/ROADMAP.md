- Move the BP-e web service client (`bpe_client`) to `nfelib`, in
  `nfelib/bpe/client/v1_0`, next to the CT-e and MDF-e clients, with the SOAP
  classes generated from the WSDL (the WSDL is only served with a client
  certificate, so the classes were declared by hand).
- Check three homologation addresses on the BP-e Portal that seem swapped on
  the services page (MG: Consulta points to production and StatusServico to
  BPeConsulta; MS: Consulta points to MG). They were kept as published.
- BP-e TM (metropolitan transport, `BPeRecepcaoTM` service) and BP-e TA (air
  transport, `BPeRecepcaoTA`, NT 2025.002): the models are in
  `l10n_br_bpe_spec`, but their issuance has its own structure (TM groups the
  trips by turnstile in `detBPeTM`) and was not implemented.
- Offline contingency (`tpEmis` 2): QR Code with the `sign` parameter (MOC
  item 10.2), `dhCont` and `xJust`.
- Replacement BP-e (`tpBPe` 3, `infBPeSub`) and the seat change and excess
  baggage events.
- `ICMSUFFim` group (ICMS sharing with the destination state for final
  consumers), `agencia` group, `autXML`, ICMS CST 60 and deferral, reduction
  and monophasic treatment of IBS and CBS beyond `gRed`.
- Payment linking (`pgtoVinc`, NT 2026.001) and the NT 2026.005 rules for
  Simples Nacional.
- DABPE (auxiliary PDF document) and BP-e XML import.
