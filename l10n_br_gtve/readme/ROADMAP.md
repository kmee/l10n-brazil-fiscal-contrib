- The document type 64 is created by this module. When
  `l10n_br_fiscal` gets it, the record has to move there.
- `erpbrasil.base` does not list the model 64 yet, so the module
  generates the access key with validation off and checks the model
  and the check digit itself.
- The success code of the `CTeRecepcaoGTVe` web service is taken as the
  usual `100`: the MOC 4.00 (Visão Geral, item 4.4) does not state it
  for the GTV-e. To be confirmed with a GTV-e issued in homologation.
- The offline contingency (`tpEmis` 2, Ajuste SINIEF 03/20, clause 11)
  is not supported: it needs `dhCont`, `xJust` and the signed QR Code
  (`sign` parameter, MOC 4.00, Visão Geral, item 9.4).
- The SEFAZ checks of the cancellation are not anticipated: 45 days
  limit (rule O07, rejection 876) and no cancellation after the CT-e OS
  that references the GTV-e is authorized (rule Q18, rejection 888).
- The fiscal events 240180 and 240181 (CT-e OS authorized or cancelled)
  are not read back into the GTV-e.
- The `tomaTerceiro` rule I53 (rejection 799, third party taker equal
  to the sender or recipient) and the IE rules I13 to I15 are left to
  the SEFAZ.
- Not filled yet: `compl` (observations), `origem` and `destino`
  addresses and `infRespTec`.
- There is no DACTE for the GTV-e, and importing a GTV-e XML is not
  supported.
- The GTV-e is not linked to the CT-e OS (`infGTVe` group of the CT-e
  OS, rule H045a).
