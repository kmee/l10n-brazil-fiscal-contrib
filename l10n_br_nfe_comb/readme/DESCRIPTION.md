Este módulo informa o grupo de combustível dos itens da NF-e (grupo LA,
`comb`) e o confere contra as regras de validação da SEFAZ.

O código (`cProdANP`) e a descrição (`descANP`) do produto ANP, os
percentuais de GLP e o valor de partida (`pGLP`, `pGNn`, `pGNi`,
`vPart`), o CODIF, o percentual de biodiesel (`pBio`) e a origem do
combustível (`origComb`) são definidos uma vez no produto, e as linhas
do documento fiscal desse produto apontam para eles. O grupo pode ser
substituído em cada linha, por exemplo para acrescentar a CIDE, o
encerrante (`encerrante`) ou a quantidade na temperatura ambiente
(`qTemp`).

A UF de consumo (`UFCons`) é a UF do grupo de combustível quando
informada; caso contrário, é a UF do endereço de entrega do documento
(`EX` para cliente estrangeiro).

Os percentuais de GLP são gravados com duas casas decimais, para que a
soma seja exatamente 100. O código ANP é conferido contra o leiaute (9
dígitos) e cada percentual de origem deve ser maior que 0.

Antes da confirmação da NF-e, o módulo recusa os dados que a SEFAZ
rejeitaria:

- regra LA03c-10 (rejeição 461, NT 2016.002): percentuais de GLP para
  um código ANP diferente de 210203001;
- regra LA03c-20 (rejeição 855, NT 2016.002): percentuais de GLP que não
  somam 100;
- regra LA11-20 (rejeição 379, NT 2015.002): encerrante em NF-e (modelo
  55) com CFOP diferente de 5656 e 5667;
- regra LA16-10 (rejeição 380, NT 2015.002): encerrante final não maior
  que o inicial;
- regra LA18-20 (rejeição 909, NT 2023.001): GLP com gás natural e sem
  origem do combustível, exceto para consumidor final, NF-e
  complementar e de devolução e os CFOP 5922 e 6922;
- regras LA21-10 e LA21-20 (rejeição 958, NT 2023.001): percentuais de
  origem que não somam 100 (separadamente para origem nacional e
  importada nos códigos de GLP 210203001, 210203003, 210203004 e
  210203005), com tolerância de 0,1.
