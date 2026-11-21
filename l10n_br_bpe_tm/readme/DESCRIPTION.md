Emissão do BP-e TM, o Bilhete de Passagem Eletrônico do transporte
metropolitano e semiurbano de passageiros cobrado por catraca ou contador
(modelo 63, `tpBPe` 4, leiaute `bpeTM_v1.00.xsd` da NT BP-e 2020.002 v1.01),
a partir do documento fiscal (`l10n_br_fiscal.document`) com o leiaute "BP-e
TM" do `l10n_br_bpe`.

O BP-e TM é emitido no fim do ciclo de viagens de cada veículo e passou a ser
exigido nessas prestações pelo Ajuste SINIEF 36/25 (efeitos desde
01/07/2026); o grupo de IBS e CBS é obrigatório a partir de 01/03/2027 (Ato
Conjunto RFB/CGIBS 7/2026).

Cada linha do documento fiscal é uma viagem (`det`): a quantidade é o número
de passagens (`qPass`), o valor bruto é a soma dos bilhetes (`vBP`) e os
tributos (ICMS, IBS e CBS) vêm do motor fiscal. As viagens do mesmo
equipamento contador formam um `detBPeTM`.

O XML do BP-e TM usa os mesmos nomes de tag do BP-e com outro conteúdo (o
`ide` não traz a viagem, as viagens vêm agrupadas por equipamento e o
`total` substitui o `infValorBPe` e o `imp`). Por isso, como no `l10n_br_gtve`,
ele não é empilhado no documento fiscal ao lado do BP-e: o módulo monta os
bindings da `nfelib` a partir do documento, das linhas e dos valores que o
`l10n_br_bpe` já calcula (`ide`, `emit`, ICMS e `IBSCBS`).

O módulo:

- monta o XML do BP-e TM: `ide` (com `dCompet` e o CFOP único das viagens),
  `emit` (com o `TAR` da empresa), `detBPeTM` por equipamento, `det` por
  viagem com o ICMS, o grupo `IBSCBS` (NT 2025.001 RTC) e os componentes
  (`Comp`), `total` (com `ICMSTot`, `IBSCBSTot` e `vTotDFe` pela regra da NT
  2026.004 v1.01), `infAdic` e `infRespTec`;
- gera a chave de acesso, a série e o número como o BP-e, assina o XML com o
  certificado da empresa e valida contra o XSD do BP-e TM da `nfelib`. O
  leiaute do BP-e TM não tem QR Code (`infBPeSupl`);
- transmite pelo serviço síncrono `BPeRecepcaoTM` do cliente do `l10n_br_bpe`
  (mensagem compactada em GZip e Base64, resposta `retBPe`) e guarda o
  `bpeTMProc` (`procBPeTM_v1.00.xsd`) no evento de autorização;
- envia o evento de cancelamento (110111) pelo `BPeRecepcaoEvento`.

Regras da NT BP-e 2020.002 v1.01 conferidas antes da SEFAZ:

- H12 e H13 (rejeições 693 e 694): as viagens de um equipamento começam (e
  terminam) na mesma UF, que vai para `UFIniViagem` e `UFFimViagem`;
- H16 (rejeição 695): contador final maior que o inicial;
- H18 (rejeição 229): inscrição estadual do emitente;
- H26 (rejeição 414): `TAR` obrigatório no modal rodoviário;
- H31 (rejeição 696): a soma das quantidades dos componentes é o número de
  passagens da viagem, com a tolerância de 1 da NT;
- I20a (rejeição 703): o BP-e TM não tem evento de não embarque;
- o serviço `BPeRecepcaoTM` só existe nos autorizadores que o publicam no
  Portal BP-e (MG e SVRS).
