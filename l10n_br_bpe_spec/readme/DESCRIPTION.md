Este módulo traz os modelos abstratos do Bilhete de Passagem Eletrônico
(`BP-e`, `modelo 63`), gerados a partir dos esquemas XSD oficiais da versão
1.00 publicados no Portal BP-e (SVRS), na cópia que a biblioteca `nfelib`
mantém em `nfelib/bpe/schemas/v1_0`.

Assim como o `l10n_br_mdfe_spec` e o `l10n_br_cte_spec`, ele não emite o BP-e
sozinho: é a base para o módulo `l10n_br_bpe`, que empilha esses modelos no
documento fiscal (`l10n_br_fiscal.document`).

Os modelos cobrem os três leiautes do modelo 63, todos definidos em
`bpeTiposBasico_v1.00.xsd`:

- BP-e (`bpe.10.tbpe_*`): bilhete do transporte rodoviário, aquaviário e
  ferroviário de passageiros.
- BP-e TM (`bpe.10.tbpetm_*`): transporte metropolitano e semiurbano com
  cobrança por catraca ou contador.
- BP-e TA (`bpe.10.tbpeta_*`): transporte aéreo (NT 2025.002).

O grupo `IBSCBS` da reforma tributária (NT 2025.001 RTC) vem de
`DFeTiposBasicos_v1.00.xsd` (`bpe.10.ttribbpe`, `bpe.10.tcibs` e os subgrupos).
Os grupos de ICMS por CST (`ICMS00`, `ICMS20`, `ICMS45`, `ICMS90` e `ICMSSN`)
ficam de fora da geração, como no CT-e, porque o `l10n_br_bpe` os monta a
partir das linhas do documento fiscal.

## Geração

Os modelos foram gerados com o
[xsdata-odoo](https://github.com/akretion/xsdata-odoo) sobre os esquemas da
`nfelib` 3.3.0, a partir do `bpe_v1.00.xsd` (que inclui o
`bpeTiposBasico_v1.00.xsd`, o `tiposGeralBPe_v1.00.xsd` e o
`DFeTiposBasicos_v1.00.xsd`):

```bash
export XSDATA_SCHEMA=bpe
export XSDATA_VERSION=10
export XSDATA_SKIP="^ICMS\d+|^ICMSSN+"
export XSDATA_LANG="portuguese"
export XSDATA_CURRENCY_FIELD="brl_currency_id"

xsdata generate nfelib/bpe/schemas/v1_0/bpe_v1.00.xsd \
  --package nfelib.bpe.odoo.v1_0 \
  --output=odoo
```

Gerar a partir do diretório inteiro de esquemas não funciona: o
`DFeTiposBasicos_v1.00.xsd` não tem `targetNamespace` e, processado sozinho,
os tipos dele (`TTribBPe`, `TIBSCBSTot`...) deixam de ser encontrados pelos
outros arquivos e os campos viram `Char`.

O BP-e tem duas tags que só diferem pela caixa: `infBPe/comp` (comprador) e
`infBPe/infValorBPe/Comp` (componente do valor). O xsdata-odoo 1.2.2 compara os
nomes antes de normalizá-los e gera os dois grupos com o mesmo modelo
`bpe.10.tbpe_comp`. A geração deste módulo usou o xsdata-odoo com essa
comparação feita depois da normalização, o que dá `bpe.10.tbpe_comp`
(comprador) e `bpe.10.tbpe_infvalorbpe_comp` (componente); o mesmo vale para o
BP-e TA.

## Prefixo dos campos e versão

Cada campo tem o prefixo `bpe10_` (nome do esquema e dois dígitos da versão
1.00), como o `nfe40_` da NF-e e o `cte40_` do CT-e: uma versão menor do
esquema reaproveita os campos, e uma versão maior ganha campos e tabelas
novos.
