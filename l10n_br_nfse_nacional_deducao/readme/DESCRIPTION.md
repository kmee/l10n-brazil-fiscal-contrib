Este módulo informa o grupo de ajuste da base de cálculo
(`valores/vAjusteBC`, TCInfoAjusteBC) da DPS da NFS-e Nacional, que o
`l10n_br_nfse_nacional` não preenche: a dedução da base do ISSQN e os
documentos que sustentam as deduções e os reembolsos
(`documentos/docAjusteBC`).

A dedução do ISSQN vem do *ISSQN Deduction Value* da linha fiscal
(`vAjusteBCISSQN`), o mesmo campo que a NF-e informa como `vDeducao`.

Os documentos são listados na NFS-e, cada um com o tipo de ajuste
(`tpAjusteBC`), o valor do documento e a parte dele aplicada a esta
NFS-e. Um documento pode ser um documento eletrônico do repositório
nacional (NFS-e, NF-e, CT-e ou outro, pela chave de acesso), um
documento fiscal fora do repositório ou um documento não fiscal.
Escolher um documento fiscal registrado no Odoo preenche a chave, o
valor, as datas e o fornecedor, que podem ser alterados.

O módulo confere as regras do grupo que não dependem dos parâmetros
municipais nem dos cadastros nacionais (Anexo VI da NFS-e Nacional,
leiaute 1.04.01 publicado com a NT 009):

- em cada documento: E0464 e E0465 (apenas descrição e sempre para os
  tipos 99 e 199), E0469 (valor aplicado até o valor do documento),
  E0472 e E0474 (competência não posterior à data de emissão), E0470
  (descrição de documento eletrônico do tipo Outro), E0460 (chave de
  acesso de 50 dígitos para NFS-e e 44 para NF-e ou CT-e), E0476
  (documento fiscal fora do repositório apenas com competência anterior
  a 2026) e E0479 (os tipos 101, 103, 104 e 199 exigem um documento
  fiscal);
- na montagem da DPS: E0435 (serviço não tributado pelo ISSQN só aceita
  os reembolsos, tipos 101 a 199), E0462 (a dedução do ISSQN exclui os
  documentos dos tipos 2 a 99), E0463 (serviços 06.01 e 06.02 só aceitam
  os tipos 9 e 199) e E0467 (valor aplicado até o valor do serviço).
