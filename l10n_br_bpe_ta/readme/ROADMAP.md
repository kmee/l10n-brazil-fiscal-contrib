- BP-e TA de substituição (`tpBPe` 3, `infBPeSub` com os tipos de
  substituição do aéreo) e contingência off-line (`tpEmis` 2, `dhCont`,
  `xJust` e o parâmetro `sign` do QR Code).
- Eventos de não fornecimento (112140) e de ajuste do BP-e TA (112130, ainda
  "pendente de especificação" na NT 2025.002 v2.00).
- `vINSSRet` do BP-e múltiplo, `gCompraGov`, `pgtoVinc` (NT 2026.001),
  agência (`agencia`), `autXML` e `ISUFEmit`.
- Diferimento, redução e monofasia do IBS e da CBS além do `gRed` que o
  `l10n_br_bpe` já monta.
- Conferir no WSDL do `BPeRecepcaoTA` (servido só com certificado de cliente)
  o nome do elemento da mensagem: a NT 2025.002 v2.00 (item 2.4) escreve
  `BPeDadosMsg`, enquanto o MOC BP-e 1.00b e o cliente usam `bpeDadosMsg`.
- A `nfelib` 3.3.0 não traz schema de BP-e TA processado: o XML autorizado é
  guardado no `bpeProc` do BP-e (a NT 2025.002 v2.00, item 4.1, diz que o BP-e
  TA usa o leiaute do BP-e processado), sem validação contra XSD.
- Conferir se a regra F13 (UF de início igual à UF do emitente) vale: a
  tabela da NT 2025.002 v2.00 ainda a traz, mas o histórico da versão 1.06a
  diz que ela foi retirada. O módulo não a confere.
- Conferir o endereço do QR Code do BP-e TA nas UFs que têm autorizador
  próprio do BP-e (MG, MS, MT, PR e SP): o módulo usa o da SVRS.
