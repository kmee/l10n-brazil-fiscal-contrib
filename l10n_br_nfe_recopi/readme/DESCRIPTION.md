Este módulo informa o número do RECOPI dos itens de papel imune da NF-e
(grupo LB, `nRECOPI`, criado pela NT 2013/005).

O RECOPI é o sistema que controla a venda de papel usado na impressão de
livros, jornais e periódicos, que é imune a impostos. Cada operação
registrada nele recebe um número que os itens de papel imune da NF-e
devem carregar.

O número é digitado uma vez no documento fiscal (*RECOPI Number*) e
copiado para as linhas cujo produto está marcado como papel imune. Pode
ser alterado em cada linha (aba *Extra Info*).

Antes da confirmação da NF-e, o módulo recusa os dados que a SEFAZ
rejeitaria:

- regra LB01-30 (rejeição 350): o número deve seguir o formato
  `aaaammddHHMMSSffffDD` do MOC 7.0 (Visão Geral, seção 8.5): uma data e
  hora válidas de 2013 até hoje, seguidas de dois dígitos verificadores
  módulo 11;
- regra LB01-10 (rejeição 348): a NFC-e não aceita o número.
