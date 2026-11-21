Este módulo informa o grupo de bens imóveis (`IBSCBS/imovel`,
TCRTCInfoImovel) que a reforma tributária acrescentou à DPS da NFS-e
Nacional e que o `l10n_br_nfse_nacional` não preenche:

- `cMun`: município do imóvel, tomado do endereço da primeira unidade
  ou, na falta dele, do município do ISSQN da linha de serviço;
- `gLocacao` (TCRTCLocacaoImovel): os dados da locação do subitem 99.03,
  com a participação na copropriedade, o valor total da locação e os
  descontos (tomados da linha de serviço e editáveis) e o vencimento
  original;
- `gUnidImob` (TCRTCUnidadesImobiliarias): as unidades imobiliárias,
  cada uma identificada pelo CIB ou pelo endereço, com a inscrição
  imobiliária municipal e os valores incluídos no aluguel que não fazem
  parte da base do IBS/CBS (`gAjusteBCLocImoveis`,
  TCRTCValoresBCImoveis).

O grupo faz parte do grupo IBSCBS, então só é informado quando a NFS-e
leva os dados da reforma tributária do `l10n_br_nfse_nacional`.

O módulo segue as regras do grupo no Anexo VI da NFS-e Nacional
(leiaute 1.04.01 publicado com a NT 009): o grupo é informado para os
indicadores de operação com bens imóveis (020101, 020201, 020202,
020301 e 020401) fora dos serviços de construção, como exigem as regras
E0928, E0931 e E0932; os dados da locação acompanham apenas o subitem
99.03 (E0936 e E0937). Recusa montar a DPS sem unidades para os
indicadores 020101, 020201 e 020301 (E0938), com ajustes de unidade fora
do subitem 99.03 (E0939), com o redutor social fora da NBS 1.1002.10.00
de locação residencial (E0944) ou com ajuste acima do valor total da
locação (E0966). A participação na copropriedade vai de 0 a 100% (E0940)
e apenas o tipo de ajuste 99 aceita descrição (E0949 e E0954).
