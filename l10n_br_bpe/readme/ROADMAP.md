- Levar o cliente de webservice do BP-e (`bpe_client`) para a `nfelib`, em
  `nfelib/bpe/client/v1_0`, ao lado dos clientes de CT-e e MDF-e, com as
  classes SOAP geradas do WSDL (o WSDL só é servido com certificado de
  cliente, por isso as classes foram declaradas à mão).
- Conferir no Portal BP-e três endereços de homologação que parecem trocados
  na página de serviços (MG: Consulta aponta para produção e StatusServico
  para BPeConsulta; MS: Consulta aponta para MG). Foram mantidos como
  publicados.
- Contingência off-line (`tpEmis` 2): QR Code com o parâmetro `sign` (MOC
  item 10.2), `dhCont` e `xJust`.
- BP-e de substituição (`tpBPe` 3, `infBPeSub`) e os eventos de alteração de
  poltrona e de excesso de bagagem.
- Grupo `ICMSUFFim` (partilha do ICMS com a UF de término para consumidor
  final), grupo `agencia`, `autXML`, CST de ICMS 60 e diferimento, redução e
  monofasia do IBS e da CBS além do `gRed`.
- Vinculação de pagamento (`pgtoVinc`, NT 2026.001) e as regras da NT 2026.005
  para o Simples Nacional.
- DABPE (documento auxiliar em PDF) e importação de XML de BP-e.
