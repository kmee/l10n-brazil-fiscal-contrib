Este módulo informa o grupo de produtos agropecuários e florestais da
NF-e (grupo ZF, `agropecuario`), criado pela NT 2024.003: ou os
receituários de agrotóxicos (`defensivo`, até 20, com o número do
receituário e o CPF do responsável técnico) ou a guia de trânsito
(`guiaTransito`: tipo, UF, série e número da GTA, TTA, DTA, ATV, PTV,
GTV ou permissão florestal).

O grupo é digitado no documento fiscal, aba *Agricultural Products*,
porque o receituário e a guia pertencem a cada operação.

O leiaute é conferido na digitação (número do receituário com 1 a 30
caracteres, número da guia com 1 a 9 dígitos, série com até 9
caracteres) e o CPF do técnico precisa ser válido (regra ZF03a-10,
rejeição 308). Antes da emissão da NF-e (modelo 55), o módulo recusa o
que as regras de validação da NT 2024.003 v1.10 rejeitam:

- ZF02-10 (rejeição 835): item com NCM de agrotóxico vendido ao
  consumidor final em NF-e normal sem o receituário, exceto para CFOP de
  devolução, transferências (X.151, X.152, X.155, X.156), entrega futura
  (5.922, 6.922) e os NCM biológicos e saneantes da exceção 4.
- ZF02-20 (rejeição 309): receituário quando nenhum item tem NCM de
  agrotóxico.
- ZF05-10 (rejeição 836): bovinos (NCM 0102) em NF-e normal de empresa
  da BA, GO, MA ou MT (tabela 4.1 da NT) sem guia de trânsito animal,
  exceto para os CFOP listados pela regra.
- ZF05-14 (rejeição 310) e ZF05-24 (rejeição 312): guia de trânsito
  animal ou vegetal quando nenhum item é animal vivo (NCM 01 e 0301) ou
  produto vegetal (NCM 06, 07, 08 e 12).
- O grupo com receituários e guia ao mesmo tempo, ou com nenhum dos
  dois, que o leiaute não aceita.
