Este módulo informa o registro de aquisição de cana-de-açúcar da NF-e
(grupo ZC, `cana`): safra, mês de referência, fornecimentos diários
(`forDia`), totais do mês, anterior e geral, deduções (`deduc`), e os
valores de fornecimentos, total de deduções e fornecimentos líquidos.

O grupo é digitado no documento fiscal, aba *Sugarcane*. O total do mês
é a soma dos fornecimentos diários, o total geral é o total do mês mais
o total anterior, o total de deduções é a soma das deduções e o valor
dos fornecimentos líquidos é o valor dos fornecimentos menos as
deduções; todos podem ser alterados à mão.

O leiaute é conferido na digitação: safra com 4 a 9 caracteres, mês de
referência como MM/AAAA, dias de 1 a 31 com um único fornecimento por
dia. Antes da emissão da NF-e, o módulo também recusa NFC-e com o grupo
(regra ZC01-10 do MOC), grupo sem fornecimentos diários ou com mais de
31, e mais de 10 deduções.
