Este módulo informa o grupo de medicamento dos itens da NF-e (grupo K,
`med`) e exige o grupo de rastreabilidade que a SEFAZ requer para
medicamentos.

O código da ANVISA (`cProdANVISA`), o motivo da isenção
(`xMotivoIsencao`) e o preço máximo ao consumidor (`vPMC`) são definidos
uma vez no produto e copiados para as linhas do documento fiscal desse
produto. Os valores podem ser alterados em cada linha, e as linhas de
uma NF-e recebida mantêm os valores do XML do fornecedor.

O código da ANVISA é conferido contra o leiaute: 11 ou 13 dígitos, ou
`ISENTO` para medicamentos isentos de registro.

A regra K01-20 (rejeição 873) exige o grupo de rastreabilidade
(`rastro`) em todo item com o grupo de medicamento. O módulo recusa
confirmar uma NF-e assim sem lotes, exceto nos casos listados pela
regra: NF-e complementar, de ajuste e de devolução, vendas não
presenciais (`indPres` 2 ou 3), NF-e recebida, DANFE tipo 6 e os CFOP de
entrega futura e de venda por conta e ordem de terceiros (5922, 6922,
5118 a 5120, 6118 a 6120). Os lotes vêm do módulo `l10n_br_nfe_rastro`.
