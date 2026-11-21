- O valor total da locação (`vTotOper`) parte do valor do serviço da
  linha, que é a parte do locador quando o imóvel tem vários
  proprietários: altere-o para o total da locação nesse caso, como o
  leiaute pede.
- As regras E0929 (código IBGE do município) e E0933 (dígito verificador
  do CIB, cujo algoritmo não consta do leiaute) ficam a cargo do ADN.
- O subitem 99.05 de condomínio (regra sem código que torna o grupo
  obrigatório) e a NFS-e de ajuste de débito e crédito (`tpNFSeDebito`,
  `tpNFSeCredito`) não são tratados: não constam do schema da DPS 1.01.
- O tipo de operação com bens imóveis (`tpOper`) e o grupo de bens
  móveis (`bensMoveis`) do grupo IBSCBS não são informados.
- Os campos estão apenas no formulário do documento fiscal; o formulário
  da fatura do `l10n_br_account` não os mostra.
