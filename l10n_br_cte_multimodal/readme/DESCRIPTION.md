Este módulo adiciona o modal de transporte multimodal (modal `06`) ao
CT-e 4.00. O módulo `l10n_br_cte` já permite escolher *Multimodal* como
modal de transporte, mas só serializa os modais rodoviário, aéreo,
aquaviário, ferroviário e dutoviário: com o modal `06` o grupo
`infModal` ficava vazio.

O módulo preenche o grupo `multimodal` do `infModal` (schema
`cteMultiModal_v4.00.xsd`, leiaute 3.6 do Anexo I do Manual de
Orientação do Contribuinte do CT-e, MOC 4.00):

- `COTM`: número do Certificado do Operador de Transporte Multimodal;
- `indNegociavel`: indicador de negociável (0 não negociável, 1
  negociável);
- `seg`: grupo opcional de seguro, com o nome e o CNPJ da seguradora
  (`infSeg/xSeg`, `infSeg/CNPJ`), o número da apólice (`nApol`) e o
  número da averbação (`nAver`).

A SEFAZ valida o XML do modal contra o schema próprio e rejeita o CT-e
com o código 580 quando a validação falha (MOC 4.00 Anexo I, regra
G026). Como o schema do CT-e não confere o modal (`xs:any` com
`processContents="skip"`), o módulo recusa exportar um CT-e multimodal
sem os elementos obrigatórios: `COTM` e `indNegociavel`, e o nome da
seguradora, a apólice e a averbação quando qualquer campo do seguro é
preenchido. O CNPJ da seguradora pode ficar vazio, como o leiaute
permite (`TCnpjOpc`).
