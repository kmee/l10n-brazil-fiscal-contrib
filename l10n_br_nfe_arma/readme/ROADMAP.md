- Os grupos são preenchidos pelo assistente de faturamento da
  separação. Faturas criadas de outras formas podem chamar
  `account.move.line._fill_nfe40_arma()` ou ter os grupos digitados.
- O número de grupos não é comparado com a quantidade do item: o MOC não
  tem essa regra.
- O hook do faturamento da separação não é coberto pelos testes, que
  montam os grupos diretamente a partir dos números de série.
