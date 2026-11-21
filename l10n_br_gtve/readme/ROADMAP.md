- O tipo de documento 64 é criado por este módulo. Quando o
  `l10n_br_fiscal` o trouxer, o registro precisa migrar para lá.
- O `erpbrasil.base` ainda não lista o modelo 64, então o módulo gera a
  chave de acesso com a validação desligada e confere o modelo e o
  dígito verificador por conta própria.
- O código de sucesso do web service `CTeRecepcaoGTVe` é tomado como o
  usual `100`: o MOC 4.00 (Visão Geral, item 4.4) não o informa para a
  GTV-e. A confirmar com uma GTV-e emitida em homologação.
- A contingência offline (`tpEmis` 2, Ajuste SINIEF 03/20, cláusula 11)
  não é suportada: exige `dhCont`, `xJust` e o QR Code assinado
  (parâmetro `sign`, MOC 4.00, Visão Geral, item 9.4).
- As conferências da SEFAZ no cancelamento não são antecipadas: limite
  de 45 dias (regra O07, rejeição 876) e nenhum cancelamento depois que
  o CT-e OS que referencia a GTV-e é autorizado (regra Q18, rejeição
  888).
- Os eventos fiscais 240180 e 240181 (CT-e OS autorizado ou cancelado)
  não são lidos de volta na GTV-e.
- A regra I53 do `tomaTerceiro` (rejeição 799, tomador terceiro igual ao
  remetente ou ao destinatário) e as regras de IE I13 a I15 ficam a
  cargo da SEFAZ.
- Ainda não são preenchidos: `compl` (observações), endereços `origem` e
  `destino` e `infRespTec`.
- Não há DACTE para a GTV-e, e a importação de XML de GTV-e não é
  suportada.
- A GTV-e não é vinculada ao CT-e OS (grupo `infGTVe` do CT-e OS, regra
  H045a).
