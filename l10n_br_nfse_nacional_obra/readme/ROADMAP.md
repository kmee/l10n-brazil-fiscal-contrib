- A regra E0373 (o CIB tem 7 caracteres e um dígito verificador) é
  conferida apenas pelo ADN: o módulo confere o tamanho do schema, não o
  dígito verificador, cujo algoritmo não consta do leiaute.
- A regra E0380 (o CEP do canteiro pertence ao município do local da
  prestação) não é conferida: o módulo não tem tabela de CEP para
  município.
- A regra E0384 pede o grupo de endereço no exterior (`endExt`) quando o
  local da prestação é no exterior (`cPaisPrestacao`). O módulo escolhe
  entre CEP e `endExt` pelo país do endereço do canteiro.
- Os campos estão apenas no formulário do documento fiscal; o formulário
  da fatura do `l10n_br_account` não os mostra.
