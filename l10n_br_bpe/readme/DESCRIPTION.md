Emissão do Bilhete de Passagem Eletrônico (`BP-e`, `modelo 63`, leiaute 1.00)
a partir do documento fiscal (`l10n_br_fiscal.document`) com o tipo de
documento 63 do `l10n_br_fiscal`, no padrão do `l10n_br_mdfe`: os grupos do
leiaute vêm do `l10n_br_bpe_spec` e são empilhados no documento fiscal.

O BP-e é obrigatório desde 01/07/2019 no transporte intermunicipal,
interestadual e internacional de passageiros rodoviário, aquaviário e
ferroviário (Ajuste SINIEF 01/17, cláusula 18ª-A, na redação do Ajuste SINIEF
22/18).

O módulo:

- monta o XML do BP-e: `ide`, `emit` (da empresa), `comp` (do parceiro do
  documento, quando informado), `infPassagem` e `infPassageiro`, `infViagem`,
  `infValorBPe` (um `Comp` por linha do documento fiscal), `imp` (ICMS das
  linhas, grupo `IBSCBS` e `vTotDFe`), `pag`, `infAdic`, `infRespTec` e o QR
  Code do `infBPeSupl`;
- calcula IBS e CBS pelo motor fiscal da OCA (classificação tributária e
  impostos das linhas) e leva o grupo `IBSCBS` da NT 2025.001 RTC;
- aplica a regra do `vTotDFe` da NT 2026.004 v1.01: igual ao `vBP` em 2026 e
  `vBP` mais IBS e CBS a partir de 2027, pela data de emissão local;
- gera a chave de acesso, assina o XML com o certificado da empresa e valida
  contra o XSD do BP-e da `nfelib`;
- transmite o BP-e (serviço síncrono `BPeRecepcao`, mensagem compactada em GZip
  e Base64) e registra o protocolo de autorização;
- envia os eventos de cancelamento (110111) e de não embarque (110115).

A transmissão usa um cliente próprio (`bpe_client`), sobre o
`brazil_fiscal_client`, no mesmo padrão dos clientes de CT-e e MDF-e da
`nfelib`, que ainda não tem cliente para o BP-e. Ele segue o MOC BP-e 1.00b
(itens 3.3 e 3.4): SOAP 1.2, requisição em `bpeDadosMsg`, resposta em
`bpeResultMsg`, sem cabeçalho SOAP. Os endereços dos autorizadores (MG, MS, MT,
PR, SP e SVRS para as demais UFs) e do QR Code são os do Portal BP-e
(https://dfe-portal.svrs.rs.gov.br/BPe/Servicos).

O modelo 63 tem mais dois leiautes, emitidos por módulos próprios que
dependem deste: o BP-e TM (transporte metropolitano e semiurbano com catraca
ou contador, NT 2020.002), no `l10n_br_bpe_tm`, e o BP-e TA (transporte
aéreo, NT 2025.002), no `l10n_br_bpe_ta`. O campo "BP-e Layout" do documento
escolhe o leiaute, e o cliente de webservice já traz os serviços
`BPeRecepcaoTM` (MG e SVRS) e `BPeRecepcaoTA` (SVRS) publicados no Portal
BP-e.
