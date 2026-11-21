- Os grupos são preenchidos pelo assistente de faturamento da
  separação. Faturas criadas de outras formas podem chamar
  `account.move.line._fill_nfe40_veicprod()` ou ter o grupo digitado.
- Uma linha de fatura com vários veículos (vários números de série) não
  recebe grupo: ela não é dividida em uma linha por veículo.
- O total da NF-e de faturamento direto (`tpOp` 2, regra W16-10) e as
  exceções das regras N12-70, N16-04 e N16-20 para veículos não são
  tratados por este módulo.
- O hook do faturamento da separação não é coberto pelos testes, que
  montam o grupo diretamente a partir do número de série.
