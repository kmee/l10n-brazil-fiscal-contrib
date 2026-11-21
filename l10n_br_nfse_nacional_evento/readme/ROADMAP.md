- As regras E0398 (o CEP do local pertence ao município do local da
  prestação) e E0402 (endereço no exterior quando o local da prestação é
  no exterior) não são conferidas: o módulo escolhe entre CEP e `endExt`
  pelo país do endereço do local.
- A regra E0393 se refere a um código de município do evento (`cMun`,
  apenas para os subitens 12.13 e 17.10) que não está no schema da DPS
  1.01, então não é informado.
- Os campos estão apenas no formulário do documento fiscal; o formulário
  da fatura do `l10n_br_account` não os mostra.
