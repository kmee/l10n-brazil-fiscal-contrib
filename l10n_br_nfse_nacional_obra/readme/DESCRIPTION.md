Este módulo informa o grupo de obra (`serv/obra`, TCInfoObra) da DPS da
NFS-e Nacional, que o `l10n_br_nfse_nacional` não preenche.

O canteiro de obras é um endereço (`res.partner`) que carrega a matrícula
da obra (CNO, ou a antiga CEI), o código do Cadastro Imobiliário
Brasileiro (CIB) e a inscrição imobiliária municipal. O documento fiscal
toma o canteiro do seu endereço de entrega e copia esses códigos; todos
podem ser alterados em cada documento.

O grupo identifica a obra pelo CNO (`cObra`), ou pelo CIB (`cCIB`)
quando não há CNO, ou pelo endereço do canteiro (`end`) quando não há
nenhum dos dois. A inscrição municipal (`inscImobFisc`) acompanha quando
informada.

A regra E0370 (Anexo VI da NFS-e Nacional, leiaute 1.04.01 publicado com
a NT 009) torna o grupo obrigatório para os códigos de tributação
nacional 07.02.01, 07.02.02, 07.04.01, 07.05.01, 07.05.02, 07.06.01,
07.06.02, 07.07.01, 07.08.01, 07.17.01, 07.19.01, 14.14.03 e 14.14.04: o
módulo recusa montar a DPS desses serviços sem a identificação da obra.
Para os demais serviços o grupo é informado apenas quando o documento
tem um CNO ou um CIB.
