- Levar os bindings e os esquemas da NFGas para a `nfelib`
  (`nfelib/nfgas/bindings/v1_0` e `nfelib/nfgas/schemas/v1_0`, com a entrada no
  `CHANGELOG_SCHEMAS.md` e no `generate_bindings.py`) e passar este módulo a
  importar de lá, como o `l10n_br_nf3e_spec`. Depois disso o pacote `bindings`
  e a pasta `schemas` saem daqui.
- Regerar quando o Portal NFGas publicar um pacote de esquemas novo (NT 2026.001
  RTC de vinculação de pagamento já está dentro do pacote da NT 2026.004).
- Mapear o tipo `xs:gYearMonth` no xsdata-odoo para gerar as tags
  `competApur`.
