- Contingência off-line (`tpEmis` 2, `dhCont` e `xJust`).
- Grupos `gCompraGov` (compras governamentais), `pgtoVinc` (vinculação de
  pagamento, NT 2026.001), `autXML` e `IEST`/`ISUFEmit` do emitente.
- Diferimento, devolução e estorno de crédito do IBS e da CBS: o
  `IBSCBSTot` sai com `vDif` e `vDevTrib` zerados.
- Bloquear o cancelamento depois de 168 horas da autorização (regra J07a,
  rejeição 704): não foi feito porque o Fisco pode liberar o prazo pelo
  evento "Liberação do Prazo de Cancelamento", que o módulo não consulta.
- O Portal BP-e publica o `BPeRecepcaoTM` só em MG e na SVRS: incluir os
  endereços de MS, MT, PR e SP quando forem publicados.
