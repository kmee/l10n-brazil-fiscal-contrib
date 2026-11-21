Na empresa (aba Fiscal, NFAg):

- escolha o ambiente da NFAg (homologação ou produção);
- confira o endereço do QR Code. O padrão é o da página de serviços do Portal
  NFAg (`https://dfe-portal.svrs.rs.gov.br/nfag/qrCode`), e a SEFAZ recusa o
  QR Code com endereço diferente do previsto (MOC NFAg 1.00l, Anexo I, regra
  G182).

A empresa precisa de CNPJ, estado, município, certificado digital e o
processador de documentos eletrônicos "Odoo Community". Crie também uma série
para o tipo de documento 75.

A NFAg não tem grupo de ICMS: a operação fiscal usada nas notas de água e
saneamento não deve calcular ICMS para os itens. O IBS e a CBS vêm da
classificação tributária (`cClassTrib`) da linha da operação fiscal.
