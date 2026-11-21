- Propor ao xsdata-odoo a comparação de nomes de classe depois da
  normalização, para que a geração do BP-e saia correta sem ajuste local
  (`infBPe/comp` e `infValorBPe/Comp`).
- Gerar os modelos dos eventos do BP-e (`eventoBPeTiposBasico_v1.00.xsd`) se
  algum módulo precisar deles; hoje os eventos são montados direto com os
  bindings da `nfelib`.
