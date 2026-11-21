This module issues the Electronic Valuables Transport Guide (Guia de
Transporte de Valores Eletrônica, GTV-e, model 64), mandatory since
01/03/2023 for the ICMS taxpayers that transport valuables (Ajuste
SINIEF 03/20 and 44/22). The GTV-e is part of the CT-e 4.00 project: it
is authorized by the CT-e authorizer and later consolidated in a CT-e
OS.

The module adds the document type 64 and builds the GTV-e from the
`l10n_br_fiscal.document`, reusing the CT-e module (`l10n_br_cte`): the
spec models of the GTV-e from `l10n_br_cte_spec`, the issuer and
partner mappings, the persons authorized to download the XML
(`autXML`), the signature, the QR Code and the events.

- The `infCte` of the GTV-e is stacked in its own model, because its
  tags have the same `cte40_` names as the CT-e ones with other
  contents.
- The XML is signed and validated against `GTVe_v4.00.xsd` when the
  document is confirmed.
- The transmission uses the synchronous `CTeRecepcaoGTVe` web service,
  with the GTV-e compressed in GZip and Base64 (MOC 4.00, Visão Geral,
  items 3.4.1 and 4.4). When authorized, the `GTVeProc` (GTV-e with its
  protocol) is stored in the authorization event.
- The cancellation is the event 110111 through `CTeRecepcaoEvento`
  (MOC 4.00, Visão Geral, item 3.7.1).

Rules of the MOC 4.00 checked by the module before the SEFAZ:

- Annex I, chapter 6: sender, recipient, CFOP, departure and arrival
  dates, at least one transported species and one vehicle; modal road
  (01) or multimodal (06).
- Annex I, rule I04 (rejection 670): series 890 to 899 are not allowed.
- Annex I, rules I02 and I03 (rejections 646 and 649): in homologation
  the names of sender and recipient are replaced by the mandatory text.
- Annex I, rules I10 and I12 (rejections 875 and 253): the access key
  carries the model 64 and a valid check digit.
- Annex I, rule I70 (rejection 850): the QR Code (`infCTeSupl`) is
  always sent.
- Visão Geral, item 5 (rejection 595): the GTV-e has no correction
  letter.

The GTV-e has no IBS/CBS group: the tax reform technical notes of the
CT-e (NT 2025.001 and 2026.002) apply only to the models 57 and 67.
