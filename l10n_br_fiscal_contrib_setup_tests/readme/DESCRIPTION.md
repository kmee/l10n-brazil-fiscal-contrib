Módulo técnico para o CI deste repositório. Não se destina a bancos de
produção.

O CI instala apenas os módulos deste repositório e suas dependências.
Sem um módulo de plano de contas brasileiro, o post-init hook do
`l10n_br_account` aponta a empresa de demonstração
`empresa_lucro_presumido` para o plano `br_oca_generic`, que nunca é
carregado, e qualquer módulo que traga o `sale` falha na criação do
banco de testes. Depender do `l10n_br_coa_generic` carrega esse plano
nas empresas de demonstração, como no CI do OCA/l10n-brazil.
