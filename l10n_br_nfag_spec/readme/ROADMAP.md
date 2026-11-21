- Levar os esquemas e os bindings da NFAg para a `nfelib`
  (`nfelib/nfag/schemas/v1_0` e `nfelib/nfag/bindings/v1_0`, com a entrada em
  `generate_bindings.py`, as extensões no `.xsdata.xml` e o registro em
  `CHANGELOG_SCHEMAS.md`). Com eles publicados, este módulo passa a apontar
  `_nfag10_binding_module` para a `nfelib` e deixa de trazer `bindings/` e
  `schemas/`.
- Gerar os modelos dos eventos (`eventoNFAgTiposBasico_v1.00.xsd`) se algum
  módulo precisar deles; hoje os eventos são montados direto com os bindings.
